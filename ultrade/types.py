from enum import Enum
from typing import TypedDict, Optional, List
from algosdk.v2client.algod import AlgodClient
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
    MAINNET = 'mainnet'
    TESTNET = 'testnet'

class KeyType(BaseEnum):
    ALGORAND = 'algorand'
    ETH = 'ethereum'
    SOLANA = 'solana'

class Order(TypedDict):
    id: str
    symbol: str
    side: str
    type: str
    time_force: str
    quantity: int
    price: int
    status: int


class NewOrderOptions(TypedDict):
    symbol: str
    side: str
    type: str
    quantity: int
    price: int

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
    def __init__(self, pair_id: int, company_id: int, address: str, chain_id: int, order_side: str, order_type: str, price: int, amount: int, base_token_address: str, base_token_chain_id: int, price_token_address: str, price_token_chain_id: int, wlp_id: int = 0):
        self.pair_id = pair_id
        self.company_id = company_id
        self.address = address
        self.chain_id = chain_id
        self.order_side = order_side
        self.order_type = order_type
        self.price = price
        self.amount = amount
        self.expired_time = int(time.time()) + 30 * 24 * 60 * 60 #cur time + 30 days
        self.base_token_address = base_token_address
        self.base_token_chain_id = base_token_chain_id
        self.price_token_address = price_token_address
        self.price_token_chain_id = price_token_chain_id
        self.wlp_id = wlp_id

        self._data = self.__setup_data()

    def __setup_data(self):
        return {
            'pairId': self.pair_id,
            'companyId': self.company_id,
            'address': self.address,
            'chainId': self.chain_id,
            'orderSide': self.order_side,
            'orderType': self.order_type,
            'price': self.price,
            'amount': self.amount,
            'expiredTime': self.expired_time,
            'baseTokenAddress': self.base_token_address,
            'baseTokenChainId': self.base_token_chain_id,
            'priceTokenAddress': self.price_token_address,
            'priceTokenChainId': self.price_token_chain_id,
            'wlpId': self.wlp_id
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