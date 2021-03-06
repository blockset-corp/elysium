import os
import warnings
from asyncio import gather, Semaphore
from datetime import datetime, timezone, timedelta
from typing import List
import backoff
from aiohttp import ClientSession
from entities import HeightPaginatedResponse, Transaction, Blockchain, FeeEstimate, Amount, Transfer
from providers.abstract import AbstractProvider, AbstractFeeProvider
from blockchains import BLOCKCHAIN_MAP

BASE_URL = 'https://api.etherscan.io/api'
TOKEN = os.getenv('ETHERSCAN_TOKEN', '')
if not TOKEN:
    warnings.warn('ETHERSCAN_TOKEN not found in environment')
ETHERSCAN_RATE_LIMIT = int(os.getenv('ETHERSCAN_RATE_LIMIT', '3'))
SEM = Semaphore(ETHERSCAN_RATE_LIMIT)
FEE_CACHE = {}  # {chain_id: {'ts': datetime, 'value': fees}
FEE_CACHE_EXPIRY = timedelta(minutes=1)


class EtherscanProvider(AbstractProvider, AbstractFeeProvider):
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        block_num_hex = await self._get(session, params={'module': 'proxy', 'action': 'eth_blockNumber'})
        block = await self._get(session, params={
            'module': 'proxy',
            'action': 'eth_getBlockByNumber',
            'tag': block_num_hex,
            'boolean': 'true'
        })
        fees = await self.get_fees(session, chain_id)
        return Blockchain(
            fee_estimates=fees,
            fee_estimates_timestamp=datetime.now().replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
            block_height=int(block['number'], 16),
            verified_height=int(block['number'], 16),
            verified_block_hash=block['hash'],
            **BLOCKCHAIN_MAP[chain_id]
        )

    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str, start_height: int,
                                       end_height: int) -> HeightPaginatedResponse[Transaction]:
        params = {'address': address, 'startblock': start_height, 'endblock': end_height}
        transactions, token_transactions, internal_transactions = await gather(
            self._get(session, params={'module': 'account', 'action': 'txlist', **params}),
            self._get(session, params={'module': 'account', 'action': 'tokentx', **params}),
            self._get(session, params={'module': 'account', 'action': 'txlistinternal', **params})
        )

        tx_map = {}
        default = lambda: {'tx': None, 'tok': [], 'int': []}
        native_cur_id = f'{chain_id}:__native__'
        contents = []

        for tx in transactions:
            tx_map.setdefault(tx['hash'], default())['tx'] = tx

        for tx in token_transactions:
            tx_map.setdefault(tx['hash'], default())['tok'].append(tx)

        for tx in internal_transactions:
            tx_map.setdefault(tx['hash'], default())['int'].append(tx)

        block_indexes = {}

        def block_accumulating_index(block):
            block_indexes.setdefault(block, 0)
            block_indexes[block] += 1
            return block_indexes[block]

        for txid, txn in tx_map.items():
            transaction_id = f'{chain_id}:{txid}'
            xfer_counter = 0
            transfers = []
            timestamp = None
            block_hash = None
            block_height = None
            confirmations = None
            meta = {}
            fee = None
            status = 'confirmed'
            if txn['tx']:
                if txn['tx'].get('isError') == '1':
                    status = 'failed'
                timestamp = datetime.utcfromtimestamp(int(txn['tx']['timeStamp']))
                total_fee = str(int(txn['tx']['gasUsed']) * int(txn['tx']['gasPrice']))
                block_hash = txn['tx']['blockHash']
                block_height = int(txn['tx']['blockNumber'])
                confirmations = int(txn['tx']['confirmations'])
                fee = Amount(currency_id=native_cur_id, amount=total_fee)
                meta = {
                    'gasLimit': f'0x{int(txn["tx"]["gas"]):x}',
                    'gasUsed': f'0x{int(txn["tx"]["gasUsed"]):x}',
                    'gasPrice': f'0x{int(txn["tx"]["gasPrice"]):x}',
                    'nonce': f'0x{int(txn["tx"]["nonce"]):x}'
                }
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{txid}:{xfer_counter}',
                    blockchain_id=chain_id,
                    from_address=txn['tx']['from'],
                    to_address='__fee__',
                    index=xfer_counter,
                    transaction_id=transaction_id,
                    amount=fee,
                    meta={}
                ))
                xfer_counter += 1
                if txn['tx'].get('value', '0') != '0':
                    transfers.append(Transfer(
                        transfer_id=f'{chain_id}:{txid}:{xfer_counter}',
                        blockchain_id=chain_id,
                        from_address=txn['tx']['from'],
                        to_address=txn['tx']['to'],
                        index=xfer_counter,
                        transaction_id=transaction_id,
                        amount=Amount(currency_id=native_cur_id, amount=txn['tx']['value']),
                        meta={}
                    ))
                    xfer_counter += 1
            for tok_tx in txn['tok']:
                if timestamp is None:
                    timestamp = datetime.utcfromtimestamp(int(tok_tx['timeStamp']))
                if fee is None:
                    total_fee = str(int(tok_tx['gasUsed']) * int(tok_tx['gasPrice']))
                    fee = Amount(currency_id=native_cur_id, amount=total_fee)
                    transfers.append(Transfer(
                        transfer_id=f'{chain_id}:{txid}:{xfer_counter}',
                        blockchain_id=chain_id,
                        from_address=tok_tx['from'],
                        to_address='__fee__',
                        index=xfer_counter,
                        transaction_id=transaction_id,
                        amount=fee,
                        meta={}
                    ))
                    xfer_counter += 1
                if block_hash is None:
                    block_hash = tok_tx['blockHash']
                if block_height is None:
                    block_height = int(tok_tx['blockNumber'])
                if confirmations is None:
                    confirmations = int(tok_tx['confirmations'])
                if not meta:
                    meta = {
                        'gasLimit': f'0x{int(tok_tx["gas"]):x}',
                        'gasUsed': f'0x{int(tok_tx["gasUsed"]):x}',
                        'gasPrice': f'0x{int(tok_tx["gasPrice"]):x}',
                        'nonce': f'0x{int(tok_tx["nonce"]):x}'
                    }
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{txid}:{xfer_counter}',
                    blockchain_id=chain_id,
                    from_address=tok_tx['from'],
                    to_address=tok_tx['to'],
                    index=xfer_counter,
                    transaction_id=transaction_id,
                    amount=Amount(currency_id=f'{chain_id}:{tok_tx["contractAddress"]}', amount=tok_tx['value']),
                    meta={}
                ))
                xfer_counter += 1

            for int_tx in txn['int']:
                if timestamp is None:
                    timestamp = datetime.utcfromtimestamp(int(int_tx['timeStamp']))
                if block_height is None:
                    block_height = int(int_tx['blockNumber'])
                if fee is None:
                    fee = Amount(currency_id=native_cur_id, amount='0')
                if confirmations is None:
                    confirmations = 0
                if block_hash is None:
                    block_hash = ''
                transfers.append(Transfer(
                    transfer_id=f'{chain_id}:{txid}:{xfer_counter}',
                    blockchain_id=chain_id,
                    from_address=int_tx['from'],
                    to_address=int_tx['to'],
                    index=xfer_counter,
                    transaction_id=transaction_id,
                    amount=Amount(currency_id=native_cur_id, amount=int_tx['value']),
                    meta={}
                ))
                xfer_counter += 1
            contents.append(Transaction(
                transaction_id=transaction_id,
                identifier=txid,
                hash=txid,
                blockchain_id=chain_id,
                timestamp=timestamp.replace(tzinfo=timezone.utc).isoformat(timespec='milliseconds'),
                _embedded={'transfers': transfers},
                fee=fee,
                confirmations=confirmations,
                index=block_accumulating_index(block_hash),
                size=int(meta.get('gasUsed', '0x0'), base=16),
                block_hash=block_hash,
                block_height=block_height,
                status=status,
                meta={'input': '0x', **meta},
            ))

        return HeightPaginatedResponse(contents=contents, has_more=False)

    async def get_fees(self, session: ClientSession, chain_id: str) -> List[FeeEstimate]:
        if cached_fees := FEE_CACHE.get(chain_id):
            if datetime.now() - cached_fees['ts'] < FEE_CACHE_EXPIRY:
                return cached_fees['value']

        oracle = await self._get(session, params={'module': 'gastracker', 'action': 'gasoracle'})

        fees = []
        tasks = []

        for price in ['SafeGasPrice', 'ProposeGasPrice', 'FastGasPrice']:
            wei = int(oracle[price]) * 1_000_000_000
            fees.append(FeeEstimate(
                fee=Amount(currency_id=f'{chain_id}:__native__', amount=str(wei)),
                tier='',
                estimated_confirmation_in=0,
            ))
            tasks.append(self._get_fee_duration(session, wei))

        durations = await gather(*tasks)

        for fee, duration in zip(fees, durations):
            fee.tier = f'{int(duration/1000/60)}m'
            fee.estimated_confirmation_in = duration

        FEE_CACHE[chain_id] = {'ts': datetime.now(), 'value': fees}

        return fees

    async def _get_fee_duration(self, session, wei):
        result = await self._get(session, params={
            'gasprice': wei,
            'module': 'gastracker',
            'action': 'gasestimate'
        })
        return int(result) * 1000

    @backoff.on_exception(backoff.expo, ValueError, max_tries=3, factor=2)
    async def _get(self, session, **kwargs):
        params = kwargs.pop('params', {})
        params['apikey'] = TOKEN
        async with SEM, session.get(BASE_URL, params=params, **kwargs) as resp:
            if resp.status != 200:
                if resp.status != 200:
                    print(f'Got status code = {resp.status} from Etherscan')
                    raise ValueError(f'Invalid status code {resp.status} for GET')
            data = await resp.json()
            print(f'etherscan request: module={params.get("module", None)} action={params.get("action", None)} '
                  f'status={data.get("status", "1")} message={data.get("message", "")}')
        return data['result']
