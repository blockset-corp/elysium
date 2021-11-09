from tests.blockset import Blockset, TestClient
from elysium import app


ADDRESSES = [
    ('ethereum-mainnet', ['0x04d542459de6765682d21771d1ba23dc30fb675f'])
]

elysium = TestClient(app)


def test_diff():
    blockset = Blockset()
    for blockchain_id, addresses in ADDRESSES:
        blockset_result = blockset.get_balances(blockchain_id, addresses)
        elysium_result = elysium.get_balances(blockchain_id, addresses)
        assert list(blockset_result.keys()) == list(elysium_result.keys())
