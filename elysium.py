from typing import Optional
from fastapi import FastAPI
from entities import Collection, Blockchain
import blockchains

app = FastAPI()


@app.get('/blockchains', response_model=Collection[Blockchain])
def get_blockchains(
        testnet: Optional[bool] = False,
        include_experimental: Optional[bool] = False
):
    return Collection(
        _embedded={
            'blockchains': blockchains.get_blockchains(),
        },
        _links={}
    )
