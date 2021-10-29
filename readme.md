# Elysium 

All Blocksets go to heaven

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

# run it
uvicorn elysium:app --reload
```