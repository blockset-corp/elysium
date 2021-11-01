import os
from datetime import datetime
from aiohttp import ClientSession
from entities import Blockchain, Transaction
from providers.abstract import AbstractProvider, HeightPaginatedResponse
from blockchains import BLOCKCHAIN_MAP

BASE_URL = 'https://api.blockcypher.com/v1'
TOKEN = os.getenv('BLOCKCYPHER_TOKEN', '')
if not TOKEN:
    raise ValueError('BLOCKCYPHER_TOKEN not found in environment')
CHAIN_MAP = {
    'bitcoin-mainnet': 'btc/main',
    'bitcoin-testnet': 'btc/test3',
    'litecoin-mainnet': 'ltc/main',
    'dogecoin-mainnet': 'doge/main'
}


class BlockCypherProvider(AbstractProvider):
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        if chain_id not in CHAIN_MAP:
            raise ValueError('Unsupported Chain')
        blockcypher_id = CHAIN_MAP[chain_id]
        async with session.get(f'{BASE_URL}/{blockcypher_id}?token={TOKEN}') as resp:
            val = await resp.json()
            return Blockchain(
                fee_estimates=[],  # TODO: read fees here
                fee_estimates_timestamp=datetime.now(),
                block_height=val['height'],
                verified_block_height=val['height'],
                verified_block_hash=val['hash'],
                **BLOCKCHAIN_MAP[chain_id]
            )

    async def get_address_transactions(self, session: ClientSession, address: str, start_height: int,
                                       end_height: int) -> HeightPaginatedResponse[Transaction]:
        pass

