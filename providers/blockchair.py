import os
import warnings
from asyncio import gather, Semaphore
from base64 import b64encode
from binascii import unhexlify
from datetime import datetime, timezone, timedelta
import backoff
from aiohttp import ClientSession, ClientError
from memoize.wrapper import memoize
from memoize.configuration import MutableCacheConfiguration, DefaultInMemoryCacheConfiguration
from memoize.key import EncodedMethodNameAndArgsKeyExtractor
from blockchains import BLOCKCHAIN_MAP
from entities import HeightPaginatedResponse, Transaction, Blockchain, Amount, Transfer
from providers.abstract import AbstractProvider, AbstractFeeProvider

BASE_URL = 'https://api.blockchair.com'
TOKEN = os.getenv('BLOCKCHAIR_TOKEN', None)
if TOKEN is None:
    warnings.warn('No BlockChair token found in environment')
CHAIN_MAP = {
    'bitcoin-mainnet': 'bitcoin',
    'bitcoin-testnet': 'bitcoin/testnet',
    'bitcoincash-mainnet': 'bitcoin-cash',
    'litecoin-mainnet': 'litecoin',
    'dogecoin-mainnet': 'dogecoin'
}
SEM = Semaphore(value=12)
LAST_BLOCK_HEIGHT = 0


def transaction_cache_config():
    return MutableCacheConfiguration.initialized_with(DefaultInMemoryCacheConfiguration(
        capacity=100_000,
        method_timeout=timedelta(minutes=5),
        update_after=timedelta(days=365),
        expire_after=timedelta(days=365),
    )).set_key_extractor(EncodedMethodNameAndArgsKeyExtractor(skip_first_arg_as_self=True))


class BlockChairProvider(AbstractProvider):
    def __init__(self, fee_provider: AbstractFeeProvider):
        self.fee_provider = fee_provider

    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        val = await self._get(session, chain_id, 'stats')
        global LAST_BLOCK_HEIGHT
        LAST_BLOCK_HEIGHT = val['best_block_height']
        fees = await self.fee_provider.get_fees(session, chain_id)
        return Blockchain(
            fee_estimates=fees,
            fee_estimates_timestamp=datetime.now().replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
            block_height=val['best_block_height'],
            verified_height=val['best_block_height'],
            verified_block_hash=val['best_block_hash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str, start_height: int,
                                       end_height: int) -> HeightPaginatedResponse[Transaction]:
        result = await self._get(session, chain_id, f'dashboards/address/{address}', params={
            'limit': '10000',
            'transaction_details': 'true'
        })
        tasks = [self._get_transaction(session, chain_id, txdetails, i, address)
                 for i, txdetails in enumerate(result.get(address, {}).get('transactions', []))]
        txns = await gather(*tasks)
        return HeightPaginatedResponse(contents=list(txns), has_more=False)

    @memoize(configuration=transaction_cache_config())
    async def _get_transaction(self, session, chain_id, txdetails, idx, address):
        result = await self._get(session, chain_id, f'raw/transaction/{txdetails["hash"]}')
        txn = result[txdetails['hash']]['decoded_raw_transaction']
        raw = unhexlify(result[txdetails['hash']]['raw_transaction'])
        txid = f'{chain_id}:{txn["txid"]}'
        curid = f'{chain_id}:__native__'
        timestamp = datetime.strptime(txdetails['time'], '%Y-%m-%d %H:%M:%S').replace(tzinfo=timezone.utc)
        transfer = Transfer(
            transfer_id=f'{txid}:0',
            blockchain_id=chain_id,
            from_address='unknown' if txdetails['balance_change'] > 0 else address,
            to_address='unknown' if txdetails['balance_change'] < 0 else address,
            index=0,
            transaction_id=txid,
            amount=Amount(amount=str(abs(txdetails['balance_change'])), currency_id=curid),
            meta={}
        )
        return Transaction(
            transaction_id=txid,
            identifier=txn['txid'],
            hash=txn['hash'],
            blockchain_id=chain_id,
            timestamp=timestamp.isoformat(timespec='milliseconds'),
            _embedded={'transfers': [transfer]},
            fee=Amount(currency_id=curid, amount='0'),
            confirmations=LAST_BLOCK_HEIGHT - txdetails['block_id'],
            size=txn['size'],
            index=idx,
            block_hash='',
            block_height=txdetails['block_id'],
            status='confirmed',
            meta={},
            raw=b64encode(raw).decode('ascii')
        )

    @backoff.on_exception(backoff.expo, ClientError, max_tries=3)
    async def _get(self, session, chain_id, endpoint, **kwargs):
        blockchair_chain = CHAIN_MAP.get(chain_id, None)
        if blockchair_chain is None:
            raise ValueError(f'Chain not supported by BlockChair provider: {chain_id}')
        params = kwargs.pop('params', {})
        params['key'] = TOKEN
        url = f'{BASE_URL}/{blockchair_chain}/{endpoint}'
        async with SEM, session.get(url, params=params, **kwargs) as resp:
            if resp.status != 200:
                print(f'BlockChairProvider bad status code: {resp.status} url: {url}')
                resp.raise_for_status()
            return (await resp.json()).get('data', {})
