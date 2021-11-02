import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, Request, Query
from entities import Collection, Link, Blockchain, Transaction, UserToken
from client import Client

app = FastAPI()


@app.get('/blockchains', response_model=Collection[Blockchain])
async def get_blockchains(
        testnet: Optional[bool] = False,
        include_experimental: Optional[bool] = False):
    async with Client() as client:
        chains = await client.get_blockchains(testnet=testnet)
    return Collection(
        _embedded={
            'blockchains': chains,
        },
        _links={}
    )


@app.get('/blockchains/{blockchain_id}', response_model=Blockchain)
async def get_blockchain(blockchain_id: str):
    async with Client() as client:
        chain = await client.get_blockchain(blockchain_id)
    return chain


@app.get('/currencies')
async def get_currencies():
    path = Path(__file__).resolve().parent / 'resources' / 'currencies.json'
    with path.open('r') as f:
        return json.load(f)


@app.get('/transactions', response_model=Collection[Transaction])
async def get_transactions(
        request: Request,
        blockchain_id: str,
        address: List[str] = Query(None),
        start_height: int = 0,
        end_height: Optional[int] = None,
        max_page_size: Optional[int] = 50,
        include_raw: Optional[bool] = False):
    async with Client() as client:
        if end_height is None or end_height < 1:
            blockchain = await client.get_blockchain(blockchain_id)
            end_height = blockchain.verified_height
        transactions = await client.get_transactions(
            addresses=address,
            blockchain_id=blockchain_id,
            start_height=start_height,
            end_height=end_height,
            max_page_size=max_page_size,
            include_raw=include_raw
        )
    links = {}
    if transactions.next_start_height is not None:
        links['next'] = Link(href=str(request.url.include_query_params(
            start_height=transactions.next_start_height,
            end_height=transactions.next_end_height
        )))
    return Collection(
        _embedded={
            'transactions': transactions.contents
        },
        _links=links
    )


@app.post('/users/token', response_model=UserToken)
def post_user_token():
    now = datetime.utcnow().isoformat()
    return UserToken(
        user_id='1',
        device_id='a-device-id',
        name=None,
        token='static-user-token',
        client_token='static-client-token',
        pub_key='',
        created=now,
        last_access=now
    )
