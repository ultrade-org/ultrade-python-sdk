from enum import Enum
from typing import TypedDict, Optional, List
from algosdk.v2client.algod import AlgodClient
from datetime import datetime
import time


class BaseEnum(Enum):
    @classmethod
    def is_valid_value(cls, value):
        try:
            cls(value)
            return True
        except ValueError:
            return False


class Network(BaseEnum):
    MAINNET = "mainnet"
    TESTNET = "testnet"


class KeyType(BaseEnum):
    ALGORAND = "algorand"
    ETH = "ethereum"
    SOLANA = "solana"


class ClientOptions(TypedDict, total=False):
    algo_sdk_client: AlgodClient
    api_url: str
    websocket_url: str


class WormholeChains(BaseEnum):
    UNSET = 0
    SOLANA = 1
    ETH = 2
    TERRA = 3
    BSC = 4
    POLYGON = 5
    AVAX = 6
    OASIS = 7
    ALGORAND = 8
    AURORA = 9
    FANTOM = 10
    KARURA = 11
    ACALA = 12
    KLAYTN = 13
    CELO = 14
    NEAR = 15
    MOONBEAM = 16
    NEON = 17
    TERRA2 = 18
    INJECTIVE = 19
    OSMOSIS = 20
    SUI = 21
    APTOS = 22
    ARBITRUM = 23
    OPTIMISM = 24
    GNOSIS = 25
    PYTHNET = 26
    XPLA = 28
    BTC = 29
    BASE = 30
    SEI = 32
    ROOTSTOCK = 33
    SCROLL = 34
    MANTLE = 35
    BLAST = 36
    XLAYER = 37
    LINEA = 38
    BERACHAIN = 39
    SEIEVM = 40
    COSMOSHUB = 4000
    EVMOS = 4001
    KUJIRA = 4002
    NEUTRON = 4003
    CELESTIA = 4004
    STARGAZE = 4005
    SEDA = 4006
    DYME = 4007
    PROVENANCE = 4008
    SEPOLIA = 10002
    ARBITRUM_SEPOLIA = 10003
    BASE_SEPOLIA = 10004
    OPTIMISM_SEPOLIA = 10005
    HOLESKY = 10006
    POLYGON_SEPOLIA = 10007


class Technology(Enum):
    ALGORAND = "ALGORAND"
    SOLANA = "SOLANA"
    EVM = "EVM"


class CreateOrder:
    def __init__(
        self,
        version: int,
        pair_id: int,
        company_id: int,
        login_address: str,
        login_chain_id: int,
        order_side: str,
        order_type: str,
        price: int,
        amount: int,
        decimal_price: float,
        base_token_address: str,
        base_token_chain_id: int,
        price_token_address: str,
        price_token_chain_id: int,
        expiration_date_in_seconds: int,
    ):
        self.version = version
        self.pair_id = pair_id
        self.company_id = company_id
        self.address = login_address
        self.chain_id = login_chain_id
        self.order_side = order_side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.decimal_price = decimal_price
        self.expired_time = expiration_date_in_seconds
        self.base_token_address = base_token_address
        self.base_token_chain_id = base_token_chain_id
        self.price_token_address = price_token_address
        self.price_token_chain_id = price_token_chain_id

        self._data = self.__setup_data()

    def __setup_data(self):
        return {
            "version": self.version,
            "pairId": self.pair_id,
            "companyId": self.company_id,
            "address": self.address,
            "chainId": self.chain_id,
            "orderSide": self.order_side,
            "orderType": self.order_type,
            "price": self.price,
            "amount": self.amount,
            "decimalPrice": self.decimal_price,
            "expiredTime": self.expired_time,
            "baseTokenAddress": self.base_token_address,
            "baseTokenChainId": self.base_token_chain_id,
            "priceTokenAddress": self.price_token_address,
            "priceTokenChainId": self.price_token_chain_id,
        }

    @property
    def data(self):
        return self._data


class PairSettings(TypedDict, total=False):
    mft_audioLink: Optional[str]
    view_baseCoinIconLink: Optional[str]
    mft_title: Optional[str]


class TradingPair(TypedDict):
    base_chain_id: int
    base_currency: str
    base_decimal: int
    base_id: str
    created_at: str
    id: int
    is_active: bool
    is_verified: int  # 0 or 1
    min_order_size: str
    min_price_increment: str
    min_size_increment: str
    pair_key: str
    pair_name: str
    pairId: int
    price_chain_id: int
    price_currency: str
    price_decimal: int
    price_id: str
    trade_fee_buy: int
    trade_fee_sell: int
    updated_at: str
    inuseWithPartners: List[int]
    restrictedCountries: List[str]
    pairSettings: PairSettings
    partner_id: int


{
    "id": 47,
    "pairId": 47,
    "pair_key": "algo_usdc",
    "is_active": True,
    "is_verified": 0,
    "base_chain_id": 8,
    "base_currency": "algo",
    "base_decimal": 6,
    "base_id": "0",
    "price_chain_id": 8,
    "price_currency": "usdc",
    "price_decimal": 6,
    "price_id": "157824770",
    "pair_name": "ALGO_USDC",
    "min_price_increment": "100",
    "min_order_size": "1000000",
    "min_size_increment": "1000000",
    "created_at": "2023-04-27T14:11:24.199Z",
    "updated_at": "2023-05-04T16:46:05.000Z",
}


class Balance(TypedDict):
    hash: str
    loginAddress: str
    loginChainId: int
    tokenId: str
    tokenChainId: int
    amount: int
    lockedAmount: int


# class export enum ORDER_STATUS {
class OrderStatus(Enum):
    OPEN_ORDER = 1
    CANCELLED = 2
    MATCHED = 3
    SELF_MATCHED = 4


class OrderType(Enum):
    LIMIT = 0
    IOC = 1
    POST = 2
    MARKET = 3


class OrderSide(Enum):
    BUY = 0
    SELL = 1


class Trade(TypedDict, total=False):
    trades_id: int
    trade_price: Optional[str]
    trade_amount: Optional[str]
    trade_fee: Optional[str]
    trade_rebate: Optional[str]
    trade_created_at: Optional[datetime]


class OrderWithTrade(TypedDict, total=False):
    id: int
    pair_id: int
    order_side: int
    order_type: int
    partner_id: Optional[int]
    direct_settle: int
    order_price: str
    order_executed_price: str
    order_amount: str
    order_filled_amount: str
    order_total: str
    order_filled_total: str
    order_status: int
    user_id: str
    completed_at: Optional[datetime]
    cancel_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    trades: Optional[List[Trade]]


class Token(TypedDict):
    id: int
    address: str
    chainId: int
    unitName: str
    name: str
    decimals: int


class WalletTransactions(TypedDict, total=False):
    primaryId: int
    id: Optional[str]
    login_address: str
    login_chain_id: int
    action_type: str
    status: str
    amount: str
    targetAddress: str
    timestamp: datetime
    createdAt: datetime
    updatedAt: datetime
    token_id: Token


class PairInfo(TypedDict):
    id: int
    pairId: int
    pair_key: str
    is_active: bool
    is_verified: int  # 0 or 1
    base_chain_id: int
    base_currency: str
    base_decimal: int
    base_id: str
    price_chain_id: int
    price_currency: str
    price_decimal: int
    price_id: str
    pair_name: str
    min_price_increment: str
    min_order_size: str
    min_size_increment: str
    created_at: str
    updated_at: str


class Price(TypedDict, total=False):
  pairId: int
  pair: Optional[str]
  askPrice: Optional[str]
  askQty: Optional[str]
  bidPrice: Optional[str]
  bidQty: Optional[str]
  lastPrice: Optional[str]
  ts: Optional[int]
  u: Optional[int]
  U: Optional[int]


class Depth(TypedDict, total=False):
    sell: List[List[str]]
    buy: List[List[str]]
    ts: int
    u: int  # lastUpdateId
    pair: str


class Symbol(TypedDict):
    pairKey: str


class LastTrade(TypedDict):
    price: str
    amount: str
    created_at: str
    buy_user_id: str
    sell_user_id: str
    trade_side: int


class AuthMethod(Enum):
    TRADING_KEY = 1
    LOGIN = 2
    NONE = 3
