from typing import List
from aiohttp import ClientSession
from entities import Blockchain
import blockcypher

BLOCKCHAINS = [
    {
        'name': 'Bitcoin',
        'id': 'bitcoin-mainnet',
        'is_mainnet': True,
        'network': 'bitcoin',
        'confirmations_until_final': 4,
    },
    {
        'name': 'Bitcoin',
        'id': 'bitcoin-testnet',
        'is_mainnet': False,
        'network': 'bitcoin',
        'confirmations_until_final': 10
    }
]


async def get_blockchains(testnet) -> List[Blockchain]:
    col = []
    async with ClientSession() as session:
        for chain in BLOCKCHAINS:
            if (testnet and chain['is_mainnet']) or (not testnet and not chain['is_mainnet']):
                continue
            data = await blockcypher.get_blockchain_data(session, chain['id'])
            data.update(chain)
            col.append(Blockchain(**data))
    return col
