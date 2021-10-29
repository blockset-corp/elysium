from typing import Optional
from fastapi import FastAPI
from entities import Collection, Blockchain
import blockchains

app = FastAPI()


@app.get('/blockchains', response_model=Collection[Blockchain])
async def get_blockchains(
        testnet: Optional[bool] = False,
        include_experimental: Optional[bool] = False
):
    chains = await blockchains.get_blockchains(testnet=testnet)
    return Collection(
        _embedded={
            'blockchains': chains,
        },
        _links={}
    )
