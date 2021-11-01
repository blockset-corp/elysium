from abc import ABC, abstractmethod
from aiohttp import ClientSession
from entities import Blockchain, Transaction, HeightPaginatedResponse


class AbstractProvider(ABC):
    @abstractmethod
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        pass

    @abstractmethod
    async def get_address_transactions(self, session: ClientSession, address: str,
                                       start_height: int, end_height: int) -> HeightPaginatedResponse[Transaction]:
        pass
