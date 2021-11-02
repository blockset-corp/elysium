from datetime import timedelta
from typing import List, Dict
from asyncio import gather
from aiohttp import ClientSession
from memoize.wrapper import memoize
from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.key import EncodedMethodNameAndArgsKeyExtractor
from entities import Blockchain, Transaction, HeightPaginatedResponse
from blockchains import BLOCKCHAINS
from providers.abstract import AbstractProvider
from providers.blockcypher import BlockCypherProvider
from providers.bitgo import BitgoFeeProvider
from providers.blockbook import BlockbookProvider
from providers.etherscan import EtherscanProvider


def blockchain_cache_config():
    return MutableCacheConfiguration.initialized_with(DefaultInMemoryCacheConfiguration(
        capacity=1000,
        method_timeout=timedelta(seconds=10),
        update_after=timedelta(seconds=10),
        expire_after=timedelta(seconds=10),
    )).set_key_extractor(EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=True))


class Client(ClientSession):
    provider_map: Dict[str, AbstractProvider]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        bitgo = BitgoFeeProvider()
        blockbook = BlockbookProvider(bitgo)
        blockcypher = BlockCypherProvider(bitgo)
        etherscan = EtherscanProvider()
        self.provider_map = {
            'bitcoin-mainnet': blockcypher,
            'bitcoincash-mainnet': blockbook,
            'litecoin-mainnet': blockcypher,
            'dogecoin-mainnet': blockcypher,
            'ethereum-mainnet': etherscan
        }

    def _get_provider(self, blockchain_id: str) -> AbstractProvider:
        if blockchain_id not in self.provider_map:
            raise ValueError(f'Unsupported chain: {blockchain_id}')
        return self.provider_map[blockchain_id]

    @memoize(configuration=blockchain_cache_config())
    async def get_blockchain(self, chain_id: str) -> Blockchain:
        print('rendering blockchain')
        provider = self._get_provider(chain_id)
        return await provider.get_blockchain_data(self, chain_id)

    @memoize(configuration=blockchain_cache_config())
    async def get_blockchains(self, testnet: bool) -> List[Blockchain]:
        print('rendering blockchains')
        tasks = []
        for chain in BLOCKCHAINS:
            if (testnet and chain['is_mainnet']) or (not testnet and not chain['is_mainnet']):
                continue
            provider = self._get_provider(chain['id'])
            tasks.append(provider.get_blockchain_data(self, chain['id']))
        results = await gather(*tasks)
        return list(results)

    async def get_transactions(self, addresses: List[str], blockchain_id: str, start_height: int, end_height: int,
                               max_page_size: int, include_raw: bool) -> HeightPaginatedResponse[Transaction]:
        provider = self._get_provider(blockchain_id)

        tasks = [provider.get_address_transactions(session=self, chain_id=blockchain_id,
                                                   address=addr, start_height=start_height,
                                                   end_height=end_height) for addr in addresses]
        results = await gather(*tasks)

        all_txns = []
        lowest_next_start_height = None
        highest_next_end_height = None

        for resp in results:
            if resp.has_more:
                if lowest_next_start_height is None or resp.next_start_height < lowest_next_start_height:
                    lowest_next_start_height = resp.next_start_height
                if highest_next_end_height is None or resp.next_end_height > highest_next_end_height:
                    highest_next_end_height = resp.next_end_height
            all_txns.extend(resp.contents)

        resp = HeightPaginatedResponse(contents=all_txns, has_more=False)

        if lowest_next_start_height is not None or highest_next_end_height is not None:
            resp.has_more = True
            resp.next_start_height = lowest_next_start_height
            resp.next_end_height = highest_next_end_height

        return resp
