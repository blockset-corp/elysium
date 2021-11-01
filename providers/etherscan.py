import os
import warnings
from asyncio import gather
from datetime import datetime, timedelta
from typing import List
from aiohttp import ClientSession
from entities import HeightPaginatedResponse, Transaction, Blockchain, FeeEstimate, Amount
from providers.abstract import AbstractProvider, AbstractFeeProvider
from blockchains import BLOCKCHAIN_MAP

BASE_URL = 'https://api.etherscan.io/api'
TOKEN = os.getenv('ETHERSCAN_TOKEN', '')
if not TOKEN:
    warnings.warn('ETHERSCAN_TOKEN not found in environment')
FEE_CACHE = {}  # {chain_id: {'ts': datetime, 'value': fees}
FEE_CACHE_EXPIRY = timedelta(minutes=1)


class EtherscanProvider(AbstractProvider, AbstractFeeProvider):
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        async with session.get(f'{BASE_URL}?module=proxy&action=eth_blockNumber&apikey={TOKEN}') as resp:
            block_num_resp = await resp.json()
        block_num_hex = block_num_resp['result']
        args = f'tag={block_num_hex}&boolean=true&apikey={TOKEN}'
        async with session.get(f'{BASE_URL}?module=proxy&action=eth_getBlockByNumber&{args}') as resp:
            block_resp = await resp.json()
        fees = await self.get_fees(session, chain_id)
        return Blockchain(
            fee_estimates=fees,
            fee_estimates_timestamp=datetime.now(),
            block_height=int(block_resp['result']['number'], 16),
            verified_block_height=int(block_resp['result']['number'], 16),
            verified_block_hash=block_resp['result']['hash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str, start_height: int,
                                       end_height: int) -> HeightPaginatedResponse[Transaction]:
        pass

    async def get_fees(self, session: ClientSession, chain_id: str) -> List[FeeEstimate]:
        if cached_fees := FEE_CACHE.get(chain_id):
            if datetime.now() - cached_fees['ts'] < FEE_CACHE_EXPIRY:
                return cached_fees['value']

        async with session.get(f'{BASE_URL}?module=gastracker&action=gasoracle&apikey={TOKEN}') as resp:
            oracle = await resp.json()

        fees = []
        tasks = []

        for price in ['SafeGasPrice', 'ProposeGasPrice', 'FastGasPrice']:
            wei = int(oracle['result'][price]) * 1_000_000_000
            fees.append(FeeEstimate(
                fee=Amount(currency_id=f'{chain_id}:__native__', amount=str(wei)),
                tier='',
                estimated_confirmation_in=0,
            ))
            tasks.append(self._get_etherscan_duration(session, wei))

        durations = await gather(*tasks)

        for fee, duration in zip(fees, durations):
            fee.tier = f'{int(duration/1000/60)}m'
            fee.estimated_confirmation_in = duration

        FEE_CACHE[chain_id] = {'ts': datetime.now(), 'value': fees}

        return fees

    async def _get_etherscan_duration(self, session, wei):
        args = f'gasprice={wei}&apikey={TOKEN}'
        async with session.get(f'{BASE_URL}?module=gastracker&action=gasestimate&{args}') as resp:
            result = await resp.json()
        return int(result['result']) * 1000
