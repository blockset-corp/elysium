import os
from tests.blockset import Blockset, TestClient
from elysium import app
from hdwallet import BIP44HDWallet, BIP32HDWallet
from hdwallet.derivations import BIP44Derivation, BIP32Derivation
from hdwallet.cryptocurrencies import DogecoinMainnet

MNEMONICS = []
if from_env := os.getenv('MNEMONIC', None):
    MNEMONICS.append(from_env)

WALLET_CURRENCIES = {
    'dogecoin-mainnet': {
        'type': 'bip44',
        'formats': ['p2pkh'],
        'crypto': DogecoinMainnet
    }
}

ADDRESSES = [
    ('ethereum-mainnet', ['0x04d542459de6765682d21771d1ba23dc30fb675f'])
]

elysium = TestClient(app)
blockset = Blockset()



# def test_diff():
#     blockset = Blockset()
#     for blockchain_id, addresses in ADDRESSES:
#         blockset_result = blockset.get_balances(blockchain_id, addresses)
#         elysium_result = elysium.get_balances(blockchain_id, addresses)
#         assert list(blockset_result.keys()) == list(elysium_result.keys())


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
    while True:
        wallet.clean_derivation()
        addresses = derive_addresses(blockchain_id, index, wallet)
        accounts = client.get_balances(blockchain_id=blockchain_id, addresses=addresses)
        has_encountered_balance = False
        for k, v in accounts.items():
            if k in all_accounts:
                all_accounts[k].balance += v.balance
            else:
                all_accounts[k] = v
            if v.balance:
                has_encountered_balance = True
        if not has_encountered_balance:
            break
        index += 1

    return all_accounts


def derive_addresses(blockchain_id, index, wallet):
    opts = WALLET_CURRENCIES[blockchain_id]
    if opts['type'] == 'bip44':
        derivation_class = BIP44Derivation
    elif opts['type'] == 'bip32':
        derivation_class = BIP32Derivation
    else:
        raise ValueError(f'Unrecognized wallet type: {opts["type"]}')
    all_addresses = []
    for format in opts['formats']:
        wallet.clean_derivation()
        derivation = derivation_class(cryptocurrency=opts['crypto'], account=0, address=index)
        wallet.from_path(derivation)
        address = getattr(wallet, f'{format}_address')()
        change_derivation = derivation_class(cryptocurrency=opts['crypto'], account=0, address=index, change=True)
        wallet.clean_derivation()
        wallet.from_path(change_derivation)
        change_address = getattr(wallet, f'{format}_address')()
        all_addresses.extend([address, change_address])
    return all_addresses


def test_mnemonics():
    for mnemonic in MNEMONICS:
        for blockchain_id in WALLET_CURRENCIES.keys():
            blockset_balances = get_wallet_balance(mnemonic, blockchain_id, client=blockset)
            elysium_balances = get_wallet_balance(mnemonic, blockchain_id, client=elysium)
            for k, v in blockset_balances.items():
                assert k in elysium_balances
                assert v.balance == elysium_balances[k].balance
