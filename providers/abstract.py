from abc import ABC, abstractmethod
from aiohttp import ClientSession
from entities import Blockchain


class AbstractProvider(ABC):
    @abstractmethod
    async def get_blockchain_data(self, session: ClientSession, chain_id: str) -> Blockchain:
        pass
