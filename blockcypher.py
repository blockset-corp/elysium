import os
from datetime import datetime
import aiohttp

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


async def get_blockchain_data(session: aiohttp.ClientSession, chain: str) -> dict:
    if chain not in CHAIN_MAP:
        raise ValueError('Unsupported Chain')
    blockcypher_id = CHAIN_MAP[chain]
    async with session.get(f'{BASE_URL}/{blockcypher_id}?token={TOKEN}') as resp:
        d = await resp.json()
        return {
            'fee_estimates': [],  # TODO: read fees here
            'fee_estimates_timestamp': datetime.now(),
            'block_height': d['height'],
            'verified_block_height': d['height'],
            'verified_block_hash': d['hash'],
        }
