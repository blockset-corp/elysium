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
        'network': 'testnet',
        'confirmations_until_final': 10
    },
    {
        'name': 'Dogecoin',
        'id': 'dogecoin-mainnet',
        'is_mainnet': True,
        'network': 'mainnet',
        'confirmations_until_final': 40
    },
    {
        'name': 'Litecoin',
        'id': 'litecoin-mainnet',
        'is_mainnet': True,
        'network': 'mainnet',
        'confirmations_until_final': 12
    },
    {
        'name': 'Ethereum',
        'id': 'ethereum-mainnet',
        'is_mainnet': True,
        'network': 'mainnet',
        'confirmations_until_final': 20
    }
]

BLOCKCHAIN_MAP = {c['id']: c for c in BLOCKCHAINS}
