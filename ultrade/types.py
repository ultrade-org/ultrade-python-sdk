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
    WORMCHAIN = 3104
    SEPOLIA = 10002


class Providers(Enum):
    METAMASK = "METAMASK"
    MYALGO = "myalgo"
    PHANTOM = "phantom"


class CreateOrder:
    def __init__(
        self,
        pair_id: int,
        company_id: int,
        login_address: str,
        login_chain_id: int,
        order_side: str,
        order_type: str,
        price: int,
        amount: int,
        base_token_address: str,
        base_token_chain_id: int,
        price_token_address: str,
        price_token_chain_id: int,
        wlp_id: int = 0,
    ):
        self.pair_id = pair_id
        self.company_id = company_id
        self.address = login_address
        self.chain_id = login_chain_id
        self.order_side = order_side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.expired_time = int(time.time()) + 30 * 24 * 60 * 60  # cur time + 30 days
        self.base_token_address = base_token_address
        self.base_token_chain_id = base_token_chain_id
        self.price_token_address = price_token_address
        self.price_token_chain_id = price_token_chain_id
        self.wlp_id = wlp_id

        self._data = self.__setup_data()

    def __setup_data(self):
        return {
            "pairId": self.pair_id,
            "companyId": self.company_id,
            "address": self.address,
            "chainId": self.chain_id,
            "orderSide": self.order_side,
            "orderType": self.order_type,
            "price": self.price,
            "amount": self.amount,
            "expiredTime": self.expired_time,
            "baseTokenAddress": self.base_token_address,
            "baseTokenChainId": self.base_token_chain_id,
            "priceTokenAddress": self.price_token_address,
            "priceTokenChainId": self.price_token_chain_id,
            "wlpId": self.wlp_id,
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
    is_verified: int
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


class WalletTransaction(TypedDict, total=False):
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
