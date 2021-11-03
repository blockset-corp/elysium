# Elysium 

All Blocksets go to heaven

### Chain Support Status

- 🤷 Bitcoin Mainnet - Untested, hit roadblock with BlockCypher rate limits
- 🤷 Bitcoin Testnet - Untested, hit roadblock with BlockCypher rate limits
- 🤷 Bitcoin Cash Mainnet - Untested, not supported by BlockCypher
- 🤷 Litecoin Mainnet - Untested, hit roadblock with BlockCypher rate limits
- 🤷 Dogecoin Mainnet  - Untested, hit roadblock with BlockCypher rate limits
- 😁 Ethereum Mainnet is mostly working via Etherscan. Correct token balances, correct number of transactions, 
  incorrect ETH balance because of fee calculation issue.
- 🙅 Ripple Mainnet not started
- 🙅 Tezos Mainnet not started
- 🙅 Hedera Mainnet not started

### Usage & Setup

You need to have `pyenv` installed. Once that is installed and correctly set up in your environment, follow the
script below. 

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

### Evaluation of Backend Providers

**[BlockCypher](https://www.blockcypher.com)** - for Bitcoin-alikes
  * 👍 Returns correct data for BTC, DOGE, LTC
  * 👎 No BCH support
  * 👎 Only query a single address at a time
  * 👎 Extremely low rate limits (max of 15k req/hr on their highest plan = $2600/mo)

**[Etherscan](https://etherscan.io)** - for Ethereum
  * 👍 Returns correct data for ETH, and ERC-20
  * 👍 Industry standard data source 
  * 👎 Slow
  * 👎 Frequent downtime

**[Amberdata](https://amberdata.io)** - for Bitcoin-alikes
  * 👍 Returns correct data for BTC, BCH, LTC
  * 👎 No DOGE support

**[Blockdemon](https://blockdaemon.com/)** - for Bitcoin-alikes
  * 🚫 Can't return raw transaction data

**[CryptoAPIs](https://cryptoapis.io/products/blockchain-data)** - for Bitcoin-alikes
  * 🚫 Can't return raw transaction data (though they claim "raw" data acceess is possible - 
      not sure if this means the same thing as when we say raw transaction bytes)

**[Bloq](https://www.bloq.com/)** - for Bitcoin-alikes
  * 🚫 Can't return raw transaction data

**[blockbook](https://github.com/trezor/blockbook)** - for Bitcoin-alikes
  * 👍 Returns correct data for BTC, BCH, LTC, DOGE
  * 👎 Have to host your own, as the public API limits to .5req/s