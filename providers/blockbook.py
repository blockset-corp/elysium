from asyncio import Semaphore
from datetime import datetime
import backoff
from aiohttp import ClientSession
from entities import Blockchain, Transaction, Amount, Transfer
from providers.abstract import AbstractProvider, AbstractFeeProvider, HeightPaginatedResponse
from blockchains import BLOCKCHAIN_MAP

SEM = Semaphore(value=1)
CHAIN_MAP = {
    'bitcoin-mainnet': 'https://btc1.trezor.io',
    'bitcoincash-mainnet': 'https://bch1.trezor.io',
    'litecoin-mainnet': 'https://ltc1.trezor.io',
    'dogecoin-mainnet': 'https://doge1.trezor.io'
}


class BlockbookProvider(AbstractProvider):
    def __init__(self, fee_provider: AbstractFeeProvider):
        self.fee_provider = fee_provider

    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        val = await self._get(chain_id, session, 'api/v2', params={})
        fees = await self.fee_provider.get_fees(session, chain_id)
        return Blockchain(
            fee_estimates=fees,
            fee_estimates_timestamp=datetime.now().isoformat(),
            block_height=val['blockbook']['bestHeight'],
            verified_height=val['blockbook']['bestHeight'],
            verified_block_hash=val['backend']['bestBlockHash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str,
                                       start_height: int, end_height: int) -> HeightPaginatedResponse[Transaction]:
        val = await self._get(chain_id, session, f'api/v2/address/{address}', params={
            'details': 'txs',
            'pageSize': '50',
            'to': str(end_height),
            'from': str(start_height)
        })
        contents = []
        last_block_height = None
        for i, tx in enumerate(val.get('transactions', [])):
            txid = f'{chain_id}:{tx["txid"]}'
            transfers = []
            counter = 0
            for txin in tx.get('vin', []):
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{tx["txid"]}:{counter}',
                    blockchain_id=chain_id,
                    from_address=txin['addresses'][0] if len(txin.get('addresses', [])) else '',
                    to_address='unknown',
                    index=counter,
                    transaction_id=txid,
                    amount=_to_amount(chain_id, txin.get('value', 0)),
                    meta={}
                ))
                counter += 1
            for txout in tx.get('outputs', []):
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{tx["txid"]}:{counter}',
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
                identifier=tx['txid'],
                hash=tx['txid'],
                blockchain_id=chain_id,
                timestamp=datetime.utcfromtimestamp(tx['blockTime']).isoformat(),
                _embedded={'transfers': transfers},
                fee=_to_amount(chain_id, tx['fees']),
                confirmations=tx['confirmations'],
                size=len(tx['hex'])//2,
                index=i,
                block_hash=tx['blockHash'],
                block_height=tx['blockHeight'],
                status='confirmed',
                meta={},
                raw=tx['hex']
            ))
            last_block_height = tx['blockHeight']

        resp = HeightPaginatedResponse(contents=contents, has_more=False)

        if val['txs'] > val['itemsOnPage']:
            resp.has_more = True
            resp.next_start_height = start_height
            resp.next_end_height = last_block_height

        return resp

    @backoff.on_exception(backoff.expo, ValueError, max_tries=3)
    async def _get(self, chain_id, session, url, **kwargs):
        if chain_id not in CHAIN_MAP:
            raise ValueError(f'Chain not supported by blockbook backend: {chain_id}')
        full_url = f'{CHAIN_MAP[chain_id]}/{url}'
        async with SEM, session.get(full_url, **kwargs) as resp:
            if resp.status != 200:
                print(f'Got status code = {resp.status} from blockbook for {full_url}')
                raise ValueError(f'Invalid status code {resp.status} for GET {full_url}')
            return await resp.json()


def _to_amount(chain_id, num) -> Amount:
    return Amount(
        currency_id=f'{chain_id}:__native__',
        amount=str(num)
    )
