from datetime import datetime, timezone
from aiohttp import ClientSession
from dateutil.parser import isoparse
from blockchains import BLOCKCHAIN_MAP
from entities import Blockchain, HeightPaginatedResponse, Transaction, FeeEstimate, Amount, Transfer
from providers.abstract import AbstractProvider

API_URL = 'https://api.tzstats.com/explorer'
RPC_URL = 'https://mainnet-tezos.giganode.io'
MUTEZ = 1_000_000


class TezosProvider(AbstractProvider):
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        async with session.get(f'{RPC_URL}/chains/main/blocks/head/header') as resp:
            val = await resp.json()
        return Blockchain(
            fee_estimates=[FeeEstimate(
                fee=Amount(currency_id='tezos-mainnet:__native__', amount='1'),
                tier='1m',
                estimated_confirmation_in=60000
            )],
            fee_estimates_timestamp=datetime.now().replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
            block_height=val['level'],
            verified_height=val['level'],
            verified_block_hash=val['hash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str, start_height: int,
                                       end_height: int) -> HeightPaginatedResponse[Transaction]:
        params = {
            'order': 'asc',
            'limit': '10000',
            'types': 'transaction,delegation,reveal'
        }
        async with session.get(f'{API_URL}/account/{address}/op', params=params) as resp:
            val = await resp.json()

        txns = []
        for i, op in enumerate(val['ops']):
            txid = f'{chain_id}:{op["hash"]}'
            fee = Amount(currency_id='tezos-mainnet:__native__', amount=str(int(op['fee']*MUTEZ)))
            xfers = [
                Transfer(
                    transfer_id=f'{txid}:0',
                    blockchain_id=chain_id,
                    from_address=op['sender'],
                    to_address='__fee__',
                    index=0,
                    transaction_id=txid,
                    amount=fee,
                    meta={'status': op['status'], 'type': op['type'].upper()}
                ),
                Transfer(
                    transfer_id=f'{txid}:1',
                    blockchain_id=chain_id,
                    from_address=op['sender'],
                    to_address=op.get('receiver', 'unknown'),
                    index=1,
                    transaction_id=txid,
                    amount=Amount(currency_id='tezos-mainnet:__native__', amount=str(int(op['volume']*MUTEZ))),
                    meta={'status': op['status'], 'type': op['type'].upper()}
                )
            ]
            txns.append(Transaction(
                transaction_id=txid,
                identifier=op['hash'],
                hash=op['hash'],
                blockchain_id=chain_id,
                timestamp=isoparse(op['time']).replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
                _embedded={'transfers': xfers},
                fee=fee,
                confirmations=op['confirmations'],
                index=i,
                size=op['storage_size'],
                block_hash=op['block'],
                block_height=op['height'],
                status='confirmed',
                meta={},
            ))

        return HeightPaginatedResponse(contents=txns, has_more=False)
