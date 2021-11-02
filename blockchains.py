BLOCKCHAINS = [
    {
        'name': 'Bitcoin',
        'id': 'bitcoin-mainnet',
        'is_mainnet': True,
        'network': 'bitcoin',
        'confirmations_until_final': 4,
        'native_currency_id': 'bitcoin-mainnet:__native__'
    },
    {
        'name': 'Bitcoin',
        'id': 'bitcoin-testnet',
        'is_mainnet': False,
        'network': 'testnet',
        'confirmations_until_final': 10,
        'native_currency_id': 'bitcoin-testnet:__native__'
    },
    {
        'name': 'Dogecoin',
        'id': 'dogecoin-mainnet',
        'is_mainnet': True,
        'network': 'mainnet',
        'confirmations_until_final': 40,
        'native_currency_id': 'dogecoin-mainnet:__native__'
    },
    {
        'name': 'Litecoin',
        'id': 'litecoin-mainnet',
        'is_mainnet': True,
        'network': 'mainnet',
        'confirmations_until_final': 12,
        'native_currency_id': 'litecoin-mainnet:__native__'
    },
    {
        'name': 'Ethereum',
        'id': 'ethereum-mainnet',
        'is_mainnet': True,
        'network': 'mainnet',
        'confirmations_until_final': 20,
        'native_currency_id': 'ethereum-mainnet:__native__'
    }
]

BLOCKCHAIN_MAP = {c['id']: c for c in BLOCKCHAINS}
