from typing import TypeVar, Generic, List, Dict
from datetime import datetime
from pydantic import BaseModel
from pydantic.generics import GenericModel

Contents = TypeVar('Contents')


class Link(BaseModel):
    href: str


class Collection(GenericModel, Generic[Contents]):
    embedded: Dict[str, List[Contents]]
    links: Dict[str, Link]

    class Config:
        fields = {'embedded': '_embedded', 'links': '_links'}


class FeeEstimate(BaseModel):
    pass


class Blockchain(BaseModel):
    name: str
    id: str
    is_mainnet: bool
    fee_estimates: List[FeeEstimate]
    fee_estimates_timestamp: datetime
    network: str
    block_height: int
    verified_block_height: int
    verified_block_hash: str
    confirmations_until_final: int


