import os
import warnings
from asyncio import Semaphore
from datetime import datetime
import backoff
from aiohttp import ClientSession
from dateutil.parser import isoparse
from entities import Blockchain, Transaction, Amount, Transfer
from providers.abstract import AbstractProvider, AbstractFeeProvider, HeightPaginatedResponse
from blockchains import BLOCKCHAIN_MAP

BASE_URL = 'https://api.blockcypher.com/v1'
TOKEN = os.getenv('BLOCKCYPHER_TOKEN', '')
BLOCKCYPHER_RATE_LIMIT = int(os.getenv('BLOCKCYPHER_RATE_LIMIT', '5'))
SEM = Semaphore(value=BLOCKCYPHER_RATE_LIMIT)
if not TOKEN:
    warnings.warn('BLOCKCYPHER_TOKEN not found in environment')
CHAIN_MAP = {
    'bitcoin-mainnet': 'btc/main',
    'bitcoin-testnet': 'btc/test3',
    'litecoin-mainnet': 'ltc/main',
    'dogecoin-mainnet': 'doge/main'
}


class BlockCypherProvider(AbstractProvider):
    def __init__(self, fee_provider: AbstractFeeProvider):
        self.fee_provider = fee_provider

    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        blockcypher_id = _blockcypher_id(chain_id)
        val = await self._get(session, f'{blockcypher_id}', params={})
        fees = await self.fee_provider.get_fees(session, chain_id)
        return Blockchain(
            fee_estimates=fees,
            fee_estimates_timestamp=datetime.now().isoformat(),
            block_height=val['height'],
            verified_height=val['height'],
            verified_block_hash=val['hash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str,
                                       start_height: int, end_height: int) -> HeightPaginatedResponse[Transaction]:
        blockcypher_id = _blockcypher_id(chain_id)
        val = await self._get(session, f'{blockcypher_id}/addrs/{address}/full', params={
            'includeHex': 'true',
            'limit': '50',
            'before': str(end_height),
            'after': str(start_height)
        })
        contents = []
        last_block_height = None
        for tx in val.get('txs', []):
            txid = f'{chain_id}:{tx["hash"]}'
            transfers = []
            counter = 0
            for txin in tx.get('inputs', []):
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{tx["hash"]}:{counter}',
                    blockchain_id=chain_id,
                    from_address=txin['addresses'][0] if len(txin.get('addresses', [])) else '',
                    to_address='unknown',
                    index=counter,
                    transaction_id=txid,
                    amount=_to_amount(chain_id, txin.get('output_value', 0)),
                    meta={}
                ))
                counter += 1
            for txout in tx.get('outputs', []):
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{tx["hash"]}:{counter}',
                    blockchain_id=chain_id,
                    from_address='unknown',
                    to_address=txout['addresses'][0] if len(txout.get('addresses', [])) else '',
                    index=counter,
                    transaction_id=txid,
                    amount=_to_amount(chain_id, txout.get('value', 0)),
                    meta={}
                ))
                counter += 1
            contents.append(Transaction(
                transaction_id=txid,
                identifier=tx['hash'],
                hash=tx['hash'],
                blockchain_id=chain_id,
                timestamp=isoparse(tx['received']).isoformat(),
                _embedded={'transfers': transfers},
                fee=_to_amount(chain_id, tx['fees']),
                confirmations=tx['confirmations'],
                block_hash=tx['block_hash'],
                block_height=tx['block_height'],
                status='confirmed',
                meta={},
                raw=tx['hex']
            ))
            last_block_height = tx['block_height']

        resp = HeightPaginatedResponse(contents=contents, has_more=False)

        if val.get('hasMore', False):
            resp.has_more = True
            resp.next_start_height = start_height
            resp.next_end_height = last_block_height

        return resp

    @backoff.on_exception(backoff.expo, ValueError, max_tries=3)
    async def _get(self, session, url, **kwargs):
        params = kwargs.pop('params', {})
        params['token'] = TOKEN
        async with SEM, session.get(f'{BASE_URL}/{url}', params=params, **kwargs) as resp:
            if resp.status != 200:
                print(f'Got status code = {resp.status} from BlockCypher for {url}')
                raise ValueError(f'Invalid status code {resp.status} for GET {url}')
            return await resp.json()


def _blockcypher_id(chain_id):
    if chain_id not in CHAIN_MAP:
        raise ValueError(f'Chain not supported by BlockCypher backend: {chain_id}')
    return CHAIN_MAP[chain_id]


def _to_amount(chain_id, num) -> Amount:
    return Amount(
        currency_id=f'{chain_id}:__native__',
        amount=str(num)
    )
