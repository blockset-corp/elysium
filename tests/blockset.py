import os
from dataclasses import dataclass
from typing import List, Mapping
from urllib.parse import urljoin, urlparse, parse_qs
from requests import Session
from requests.auth import AuthBase
from fastapi.testclient import TestClient as BaseTestClient


@dataclass
class Account:
    currency_id: str
    balance: int


class BlocksetApiMixin:
    def get_balances(self, blockchain_id: str, addresses: List[str]) -> Mapping[str, Account]:
        totals = {}  # currency_id: balance_as_int
        transactions = self.paginate_fully('transactions', {
            'blockchain_id': blockchain_id,
            'address': addresses
        })
        for transaction in transactions:
            transfers = transaction.get('_embedded', {}).get('transfers', [])
            for transfer in transfers:
                cur_amount = totals.setdefault(transfer['amount']['currency_id'], 0)
                transfer_amount = int(transfer['amount']['amount'])
                if transfer['from_address'] in addresses:
                    new_amount = cur_amount - transfer_amount
                elif transfer['to_address'] in addresses:
                    new_amount = cur_amount + transfer_amount
                else:
                    new_amount = cur_amount
                totals[transfer['amount']['currency_id']] = new_amount

        return {k: Account(currency_id=k, balance=v) for k, v in totals.items()}

    def paginate_fully(self, resource, params):
        results = []
        response = self.get(resource, params=params)
        response.raise_for_status()
        if len(response.content):
            result = response.json()
        else:
            result = {}
        if '_embedded' in result and resource in result['_embedded']:
            results.extend(result['_embedded'][resource])
        if '_links' in result and 'next' in result['_links']:
            parsed_url = urlparse(result['_links']['next']['href'])
            parsed_qs = parse_qs(parsed_url.query)
            if len(parsed_qs.get('start_height', [])):
                new_params = dict(params)
                new_params['start_height'] = parsed_qs['start_height'][0]
                results.extend(self.paginate_fully(resource, new_params))
        return results


class BlocksetAuth(AuthBase):
    def __init__(self):
        self.token = os.getenv('BLOCKSET_TOKEN', None)
        if not self.token:
            raise ValueError('Missing BLOCKSET_TOKEN in environment')

    def __call__(self, req):
        req.headers['Authorization'] = f'Bearer {self.token}'
        return req


class Blockset(BlocksetApiMixin, Session):
    def __init__(self, base_url='https://api.blockset.com'):
        super().__init__()
        self.base_url = base_url
        self.auth = BlocksetAuth()

    def request(self, method, url, *args, **kwargs):
        return super().request(method, urljoin(self.base_url, url), *args, **kwargs)


class TestClient(BlocksetApiMixin, BaseTestClient):
    pass
