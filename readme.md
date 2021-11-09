# Elysium 

All Blocksets go to heaven

### Chain Support Status

- 😁 Bitcoin Mainnet - Working with BlockChair backend
- 😁 Bitcoin Testnet - Working with BlockChair backend
- 😁 Bitcoin Cash Mainnet - Working with BlockChair backend
- 😁 Litecoin Mainnet - Working with BlockChair backend
- 😁 Dogecoin Mainnet - Working with BlockChair backend
- 😁 Ethereum Mainnet - Mostly working via Etherscan. Correct token balances, correct number of transactions, 
  incorrect ETH balance because of fee calculation issue.
- 😁 Ripple Mainnet - Working with public APIs
- 😁 Tezos Mainnet - Workign with public APIs
- 🙅 Hedera Mainnet - Might not be possible

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
  * 🚫 Doesn't return raw transaction data (though it says they do, nothing is returned) 
    A support ticket has been submitted.
  * 👍 Returns correct data for BTC, BCH, LTC
  * 👎 No DOGE support

**[Blockchair](https://blockchair.com)** - for Bitcoin-alikes
  * 👎 Individual address queries
  * 👎 Further, have to request each transaction individually as address endpoints only return txids
  * 👎 Expensive

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