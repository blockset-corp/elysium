from typing import List
from asyncio import gather
from aiohttp import ClientSession
from entities import Blockchain
from blockchains import BLOCKCHAINS
from providers.abstract import AbstractProvider
from providers.blockcypher import BlockCypherProvider


class Client(ClientSession):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        blockcypher = BlockCypherProvider()
        self.provider_map = {
            'bitcoin-mainnet': blockcypher,
            'bitcoin-testnet': blockcypher,
            'litecoin-mainnet': blockcypher,
            'dogecoin-mainnet': blockcypher,
        }

    def _get_provider(self, blockchain_id: str) -> AbstractProvider:
        if blockchain_id not in self.provider_map:
            raise ValueError(f'Unsupported chain: {blockchain_id}')
        return self.provider_map[blockchain_id]

    async def get_blockchains(self, testnet) -> List[Blockchain]:
        tasks = []
        for chain in BLOCKCHAINS:
            if (testnet and chain['is_mainnet']) or (not testnet and not chain['is_mainnet']):
                continue
            provider = self._get_provider(chain['id'])
            tasks.append(provider.get_blockchain_data(self, chain['id']))
        results = await gather(*tasks)
        return results