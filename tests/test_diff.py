import os
from tests.blockset import Blockset, TestClient
from elysium import app
from hdwallet import BIP44HDWallet, BIP32HDWallet
from hdwallet.derivations import BIP44Derivation, Derivation
from hdwallet.cryptocurrencies import DogecoinMainnet, BitcoinMainnet, LitecoinMainnet, BitcoinCashMainnet, EthereumMainnet
from ecashaddress.convert import Address as BCHAddress

MNEMONICS = []
if from_env := os.getenv('MNEMONIC', None):
    MNEMONICS.append(from_env)

WALLET_CURRENCIES = {
    'dogecoin-mainnet': {
        'type': 'bip44',
        'formats': ['p2pkh'],
        'crypto': DogecoinMainnet,
        'change': True
    },
    'bitcoin-mainnet': {
        'type': 'bip32',
        'formats': ['p2pkh', 'p2wpkh'],
        'crypto': BitcoinMainnet,
        'change': True
    },
    'bitcoincash-mainnet': {
        'type': 'bip32',
        'formats': ['p2pkh'],
        'crypto': BitcoinMainnet,
        'change': True,
        'cashaddr': 'bitcoincash'
    },
    'litecoin-mainnet': {
        'type': 'bip44',
        'formats': ['p2pkh', 'p2wpkh'],
        'crypto': LitecoinMainnet,
        'change': True
    },
    'ethereum-mainnet': {
        'type': 'bip44',
        'formats': ['p2pkh'],
        'crypto': EthereumMainnet,
        'change': False,
        'lower': True
    }
}

ADDRESSES = [
    ('ethereum-mainnet', ['0x04d542459de6765682d21771d1ba23dc30fb675f'])
]

elysium = TestClient(app)
blockset = Blockset()


def get_wallet_balance(mnemonic, blockchain_id, client):
    opts = WALLET_CURRENCIES[blockchain_id]
    if opts['type'] == 'bip44':
        wallet = BIP44HDWallet(cryptocurrency=opts['crypto'])
    elif opts['type'] == 'bip32':
        wallet = BIP32HDWallet(cryptocurrency=opts['crypto'])
    else:
        raise ValueError(f'Unrecognized wallet type: {opts["type"]}')
    wallet.from_mnemonic(mnemonic, language='english', passphrase=None)
    index = 0
    all_accounts = {}
    num_addresses = 0
    while True:
        wallet.clean_derivation()
        addresses = derive_addresses(blockchain_id, index, wallet)
        # print(f'{blockchain_id} checking addresses {addresses}')
        accounts = client.get_balances(blockchain_id=blockchain_id, addresses=addresses)
        num_addresses += len(addresses)
        has_encountered_entries = False
        for k, v in accounts.items():
            if k in all_accounts:
                all_accounts[k].entries.extend(v.entries)
            else:
                all_accounts[k] = v
            if v.entries:
                has_encountered_entries = True
        if not has_encountered_entries:
            break
        index += 1
    num_tx = sum(len(v.entries) for v in all_accounts.values())
    print(f'{blockchain_id} checked {num_addresses} addresses and found {num_tx} transactions')
    return all_accounts


def derive_addresses(blockchain_id, index, wallet):
    opts = WALLET_CURRENCIES[blockchain_id]
    if opts['type'] == 'bip44':
        derivation = BIP44Derivation(cryptocurrency=opts['crypto'], account=0, address=index)
        change_derivation = BIP44Derivation(cryptocurrency=opts['crypto'], account=0, address=index, change=True)
    elif opts['type'] == 'bip32':
        derivation = Derivation.from_path("m/0'/0").from_index(index)
        # print(f'{blockchain_id} derivation {derivation}')
        change_derivation = Derivation.from_path("m/0'/1").from_index(index)
    else:
        raise ValueError(f'Unrecognized wallet type: {opts["type"]}')
    all_addresses = []
    for fmt in opts['formats']:
        wallet.clean_derivation()
        wallet.from_path(derivation)
        all_addresses.append(getattr(wallet, f'{fmt}_address')())
        if opts['change']:
            wallet.clean_derivation()
            wallet.from_path(change_derivation)
            all_addresses.append(getattr(wallet, f'{fmt}_address')())
    if opts.get('lower', False):
        all_addresses = [a.lower() for a in all_addresses]
    if opts.get('cashaddr', False):
        all_addresses = [BCHAddress.from_string(a).to_cash_address(opts['cashaddr']) for a in all_addresses]
    return all_addresses


def test_mnemonics():
    print('testing mnemonics')
    for mnemonic in MNEMONICS:
        for blockchain_id in WALLET_CURRENCIES.keys():
            blockset_balances = get_wallet_balance(mnemonic, blockchain_id, client=blockset)
            elysium_balances = get_wallet_balance(mnemonic, blockchain_id, client=elysium)
            for k, v in blockset_balances.items():
                assert k in elysium_balances
                print(f'{k} blockset_balance={v.balance} elysium_balance={elysium_balances[k].balance}')
                assert v.balance == elysium_balances[k].balance
