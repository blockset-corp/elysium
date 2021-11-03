from asyncio import Semaphore
from datetime import datetime
from aiohttp import ClientSession
from dateutil.parser import isoparse
from blockchains import BLOCKCHAIN_MAP
from entities import HeightPaginatedResponse, Transaction, Blockchain, FeeEstimate, Amount, Transfer
from providers.abstract import AbstractProvider

BASE_URL = 'https://data.ripple.com/v2'
SEM = Semaphore(10)
LAST_BLOCK_HEIGHT = 0


class RippleProvider(AbstractProvider):
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        val = await self._get(session, 'ledgers')
        global LAST_BLOCK_HEIGHT
        LAST_BLOCK_HEIGHT = val['ledger']['ledger_index']
        return Blockchain(
            fee_estimates=[FeeEstimate(
                fee=Amount(currency_id='ripple-mainnet:__native__', amount='10'),
                tier='0m',
                estimated_confirmation_in=4000
            )],
            fee_estimates_timestamp=datetime.now().isoformat(),
            block_height=val['ledger']['ledger_index'],
            verified_height=val['ledger']['ledger_index'],
            verified_block_hash=val['ledger']['ledger_hash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str, start_height: int,
                                       end_height: int) -> HeightPaginatedResponse[Transaction]:
        val = await self._get(session, f'accounts/{address}/transactions', params={
            'type': 'Payment',
            'descending': 'false',
            'limit': '10000'
        })
        txns = []
        for i, tx in enumerate(val['transactions']):
            txid = f'{chain_id}:{tx["hash"]}'
            fee = Amount(currency_id='ripple-mainnet:__native__', amount=tx['tx']['Fee'])
            xfers = [
                Transfer(
                    transfer_id=f'{txid}:0',
                    blockchain_id=chain_id,
                    from_address=tx['tx']['Account'],
                    to_address='__fee__',
                    index=0,
                    transaction_id=txid,
                    amount=fee,
                    meta={}
                ),
                Transfer(
                    transfer_id=f'{txid}:1',
                    blockchain_id=chain_id,
                    from_address=tx['tx']['Account'],
                    to_address=tx['tx']['Destination'],
                    index=1,
                    transaction_id=txid,
                    amount=Amount(currency_id='ripple-mainnet:__native__', amount=tx['tx']['Amount']),
                    meta={}
                )
            ]
            txns.append(Transaction(
                transaction_id=txid,
                identifier=tx['hash'],
                hash=tx['hash'],
                blockchain_id=chain_id,
                timestamp=isoparse(tx['date']).isoformat(),
                _embedded={'transfers': xfers},
                fee=fee,
                confirmations=LAST_BLOCK_HEIGHT - tx['ledger_index'],
                index=i,
                size=1,
                block_hash='',
                block_height=tx['ledger_index'],
                status='confirmed',
                meta={'DestinationTag': tx['tx'].get('DestinationTag', 0)},
            ))
        return HeightPaginatedResponse(contents=txns, has_more=False)

    async def _get(self, session, endpoint, **kwargs):
        url = f'{BASE_URL}/{endpoint}'
        async with SEM, session.get(url, **kwargs) as resp:
            if resp.status != 200:
                print(f'RippleProvider invalid status code: {resp.status} for url: {url}')
                resp.raise_for_status()
            return await resp.json()
