from typing import List
from datetime import datetime
from entities import Blockchain


BLOCKCHAINS = [
    {
        'name': 'Bitcoin',
        'id': 'bitcoin-mainnet',
        'is_mainnet': True,
        'network': 'bitcoin',
        'confirmations_until_final': 4
    }
]


def get_blockchains() -> List[Blockchain]:
    col = []
    for chain in BLOCKCHAINS:
        data = {  # to be rendered dynamically
            'fee_estimates': [],
            'fee_estimates_timestamp': datetime.now(),
            'block_height': 1,
            'verified_block_height': 1,
            'verified_block_hash': '0xd3db33f',
        }
        data.update(chain)
        col.append(Blockchain(**data))
    return col
