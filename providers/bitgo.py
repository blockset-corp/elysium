from datetime import timedelta, datetime
from math import ceil
from typing import List
from aiohttp import ClientSession
from entities import FeeEstimate, Amount
from providers.abstract import AbstractFeeProvider


CONFIG_MAP = {
    'bitcoincash-mainnet': {
        'url': 'https://www.bitgo.com/api/v2/bch/tx/fee',
        'block_time': timedelta(minutes=10),
    },
    'bitcoin-mainnet': {
        'url': 'https://www.bitgo.com/api/v2/btc/tx/fee',
        'block_time': timedelta(minutes=10),
    },
    'bitcoin-testnet': {
        'static': True,
        'fees': [
            FeeEstimate(
                fee=Amount(currency_id='bitcoin-testnet:__native__', amount='1'),
                tier='1m',
                estimated_confirmation_in=60000
            )
        ]
    },
    'litecoin-mainnet': {
        'url': 'https://www.bitgo.com/api/v2/ltc/tx/fee',
        'block_time': timedelta(minutes=2.5),
    },
    'dogecoin-mainnet': {
        'static': True,
        'fees': [
            FeeEstimate(
                fee=Amount(currency_id='dogecoin-mainnet:__native__', amount='600000'),
                tier='1m',
                estimated_confirmation_in=60000
            )
        ]
    }
}

CACHE_TIMEOUT = timedelta(minutes=1)
CACHE = {}  # {chain_id: {'ts': datetime, 'value': list}}


class BitgoFeeProvider(AbstractFeeProvider):
    async def get_fees(self, session: ClientSession, chain_id: str) -> List[FeeEstimate]:
        config = CONFIG_MAP.get(chain_id)
        if not config:
            raise ValueError(f'Unsupported chain: {chain_id}')
        if config.get('static', False):
            return config['fees']

        # retrieve from cache
        if cached_value := CACHE.get(chain_id, None):
            if datetime.now() - cached_value['ts'] < CACHE_TIMEOUT:
                return cached_value['value']

        async with session.get(config['url']) as resp:
            body = await resp.json()

        if not body.get('feeByBlockTarget', None):
            conf_ms = body['numBlocks'] * int(round(config['block_time'].total_seconds() * 1000))
            results = [
                FeeEstimate(
                    tier=f'{int(conf_ms/1000/60)}m',
                    estimated_confirmation_in=conf_ms,
                    fee=Amount(
                        currency_id=f'{chain_id}:__native__',
                        amount=ceil(float(body['feePerKb']) / 1024.0)
                    )
                )
            ]
        else:
            results = []
            for nblocks, nsats in body['feeByBlockTarget'].items():
                conf_ms = int(nblocks) * int(round(config['block_time'].total_seconds() * 1000))
                results.append(FeeEstimate(
                    tier=f'{int(conf_ms/1000/60)}m',
                    estimated_confirmation_in=conf_ms,
                    fee=Amount(
                        currency_id=f'{chain_id}:__native__',
                        amount=ceil(float(nsats) / 1024.0)
                    )
                ))

        # memoize
        CACHE[chain_id] = {'ts': datetime.now(), 'value': results}

        return results
