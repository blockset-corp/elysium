from abc import ABC, abstractmethod
from typing import List
from aiohttp import ClientSession
from entities import Blockchain, FeeEstimate, Transaction, HeightPaginatedResponse


class AbstractProvider(ABC):
    @abstractmethod
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        pass

    @abstractmethod
    async def get_address_transactions(self, session: ClientSession, chain_id: str, address: str,
                                       start_height: int, end_height: int) -> HeightPaginatedResponse[Transaction]:
        pass


class AbstractFeeProvider(ABC):
    @abstractmethod
    async def get_fees(self, session: ClientSession, chain_id: str) -> List[FeeEstimate]:
        pass
