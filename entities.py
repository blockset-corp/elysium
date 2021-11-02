from typing import TypeVar, Generic, List, Dict, Optional
from pydantic import BaseModel
from pydantic.generics import GenericModel

Contents = TypeVar('Contents')


class HeightPaginatedResponse(Generic[Contents]):
    contents: List[Contents]
    has_more: bool
    next_start_height: Optional[int]
    next_end_height: Optional[int]

    def __init__(self, contents: List[Contents], has_more: bool,
                 next_start_height: Optional[int] = None,
                 next_end_height: Optional[int] = None):
        self.contents = contents
        self.has_more = has_more
        self.next_start_height = next_start_height
        self.next_end_height = next_end_height


class Link(BaseModel):
    href: str


class Collection(GenericModel, Generic[Contents]):
    embedded: Dict[str, List[Contents]]
    links: Dict[str, Link]

    class Config:
        fields = {'embedded': '_embedded', 'links': '_links'}


class Amount(BaseModel):
    amount: str
    currency_id: str


class FeeEstimate(BaseModel):
    fee: Amount
    tier: str
    estimated_confirmation_in: int


class Blockchain(BaseModel):
    name: str
    id: str
    is_mainnet: bool
    fee_estimates: List[FeeEstimate]
    fee_estimates_timestamp: str
    network: str
    block_height: int
    verified_height: int
    verified_block_hash: str
    confirmations_until_final: int
    native_currency_id: str


class Transfer(BaseModel):
    transfer_id: str
    blockchain_id: str
    from_address: str
    to_address: str
    index: int
    transaction_id: str
    amount: Amount
    meta: Dict[str, str]


class Transaction(BaseModel):
    transaction_id: str
    identifier: str
    hash: str
    blockchain_id: str
    timestamp: str
    embedded: Dict[str, List[Transfer]]
    fee: Amount
    confirmations: int
    block_hash: str
    block_height: int
    status: str
    meta: Dict[str, str]
    raw: Optional[str]

    class Config:
        fields = {'embedded': '_embedded'}


class UserToken(BaseModel):
    user_id: str
    device_id: str
    name: Optional[str]
    token: str
    client_token: str
    pub_key: str
    created: str
    last_access: str
