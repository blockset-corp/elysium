# Elysium 

All Blocksets go to heaven

### Chain Support

- [x] Bitcoin Mainnet
  - BlockCypher
- [x] Bitcoin Testnet
  - BlockCypher
- [x] Bitcoin Cash Mainnet
  - BlockCypher
- [x] Litecoin Mainnet
  - BlockCypher
- [x] Dogecoin Mainnet
  - BlockCypher
- [x] Ethereum Mainnet
  - Etherscan
- [ ] Ripple Mainnet
- [ ] Tezos Mainnet
- [ ] Hedera Mainnet

### Usage

```shell
# set up environment
pyenv install 3.10.0
git clone git@github.com:blockset-corp/elysium.git
cd elysium
python -mvenv .venv
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt

# populate environment
export BLOCKCYPHER_TOKEN="<TOKEN HERE>"
export ETHERSCAN_TOKEN="<TOKEN HERE>"

# run it
uvicorn elysium:app --reload
```