# Ultrade

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick start](#quick-start)
   - [Structure](#structure)
   - [Creating a Client](#creating-a-client)
   - [Creating a Signer](#creating-a-signer)
   - [Trading key example](#trading-key-example)
   - [Logging In](#logging-in)
4. [Public methods](#public-methods)
5. [Required login methods](#required-login-methods)

## Introduction

This is an early preview version of this SDK. It is work in progress. More detailed documentation will be added, and there may still be bugs lurking around. The SDK is available via this github but is NOT yet available via PIP.

The `ultrade` package is a Python SDK for interacting with ULTRADE's V2 platform, the Native Exchange (NEX) with Bridgeless Crosschain Orderbook technology . It provides a simple interface for creating and managing orders, as well as for interacting with the Ultrade API and streams. Deposits are always credited to the logged in account. Creating orders are done via this SDK. The login account is used to create orders by cryptographically signing order messages and sending them to the API. This process does not involve on-chain transactions and does not incur any gas costs. Trading keys can be associated with a specific login account and its balances and will be used for managing orders, but will not be able to withdraw. This is useful for working with MM clients on their own accounts.

When using this SDK, please note that token amounts and prices that are stated to be in Atomic Units mean the smallest indivisible units of the token based on its number of decimals, in a unsigned integern format. For example 1 ETH from Ethereum will be represented as 1 with 18 zeros, while 1 USDC from Algorand will be 1 with 6 zeros (6 decimals asset). The price is denominated based on the Price (Quote) token, while amounts of a base token are denominated according to that base tokens' decimals.

### Funds Management on Ultrade Exchange

Ultrade Exchange provides a straightforward approach to funds management:

Users deposit funds into their Ultrade accounts.
When creating orders, a portion of the user's funds may be temporarily locked to cover the order.
These locked funds are used for order execution.
Unused funds remain accessible for other purposes, including withdrawals.
Ultrade ensures that users cannot spend more than their available balance. This straightforward approach eliminates the need for complex liquidation procedures, allowing users to trade securely and efficiently.

## Installation

To install the `ultrade` package, you can use pip:

```bash
pip install ultrade
```

## Quick start

### Structure

| Import                   | Description                                                                                                                                       |
| ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------- |
| `ultrade.Client`         | The core class encompassing essential methods for working with Ultrade DeFi, including functionalities secured by user login.                     |
| `ultrade.Signer`         | A class designed for generating signers based on the provided private key. It can be used for user login as well as signing deposit transactions. |
| `ultrade.types`          | A module containing data type definitions used throughout the SDK.                                                                                |
| `ultrade.socket_options` | Options related to WebSocket connections.                                                                                                         |
| `ultrade.utils`          | Contains helper functions that can be useful.                                                                                                     |

### Creating a client

To create a client, you must specify the `network`, which can be either `mainnet` or `testnet`. Depending on the selected network, optional parameters are set by default. These parameters are primarily intended for testing purposes and can be manually configured if necessary. A detailed description of these optional parameters is provided in the table below.

| Option          | Description                           | Default value                                                                  |
| --------------- | ------------------------------------- | ------------------------------------------------------------------------------ |
| company_id      | Id of your company.                   | Ultrade (company_id = 1)                                                       |
| api_url         | The URL of the Ultrade API.           | **Testnet**: _api.testnet.ultrade.org_<br>**Mainnet**: _api.ultrade.org_       |
| websocket_url   | The URL of the Ultrade WebSocket API. | **Testnet**: _ws.testnet.ultrade.org_<br>**Mainnet**: _ws.mainnet.ultrade.org_ |
| algo_sdk_client | The Algorand SDK client.              | Public client                                                                  |

```python
from ultrade import Client

company_id = await Client.get_company_by_domain("app.ultrade.org")
api_url = "api.ultrade.org"

client = Client(network="testnet", company_id=company_id, api_url=api_url)
```

### Creating a signer

To create a signer, you must provide a mnemonic key. This key is a 25-word phrase used for Algorand or an EVM private key. The signer is utilized for various functions such as logging in, depositing, withdrawing, and signing transactions.

```python
from ultrade import Signer

#algorand
mnemonic_key = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod ..."
signer = Signer.create_signer(mnemonic_key)

#EVM
private_key = "e421abcdb55899d7bc2be1652a64a63fffc3cf654e989ebcce45k121d6a34a"
signer = Signer.create_signer(private_key)
```

### Logging in

To initiate a login, invoke the `set_login_user` method on the client instance, passing a `signer` instance as its argument. This login process generates a special token that grants access to the SDK's protected methods, which require authentication. These methods, offering enhanced security and functionality, are detailed in the "Private Methods" table. This token ensures secure interaction with the SDK's privileged features.

```python
from ultrade import Signer, Client

private_key = #your EVM private key or Algorand mnemonic
client = Client(private_key)
signer = Signer.create_signer(mnemonic_key)
await client.set_login_user(signer)

isLogged = client.is_logged_in() #returns True or False
```

---

### Trading Key Example

Sets the trading key for the SDK client. This method is used to authenticate the client with the Ultrade exchange. The key allows you to carry out trading operations, but does not have the ability to perform deposit/withdraw. Alternatively, you can use the `set_login_user` method to authenticate the client.

| Option               | Description                                                                                                          |
| -------------------- | -------------------------------------------------------------------------------------------------------------------- |
| trading_key          | The trading key.                                                                                                     |
| address              | Login address of the account for which the trading key was issued                                                    |
| trading_key_mnemonic | The mnemonic of the trading key. The mnemonic is a string of words that is generated when you register a trading key |

```python
client.set_trading_key(
        trading_key=TRADING_KEY,
        address=LOGIN_ADDRESS,
        trading_key_mnemonic=TRADING_KEY_MNEMONIC,
    )
```

---

## Public methods

Below are methods that do not require the [login function](#logging-in) to be executed
| Method | Description |
| ------ | ----------- |
| [get_pair_list](#get_pair_list) | Retrieves a list of trading pairs available on the exchange. |
| [get_pair_info](#get_pair_info) | Retrieves detailed information about a specific trading pair. |
| [ping](#ping) | Checks the latency between the client and the server. |
| [get_price](#get_price) | Retrieves the current market price for a specified trading pair. |
| [get_depth](#get_depth) | Retrieves the order book depth for a specified trading pair. |
| [get_symbols](#get_symbols) | Retrieves a list of trading pairs that match a given pattern. |
| [get_last_trades](#get_last_trades) | Retrieves the most recent trades for a specified trading pair. |
| [get_order_by_id](#get_order_by_id) | Retrieves detailed information about an order by its ID. |
| [get_company_by_domain](#get_company_by_domain) | Retrieves the company ID based on the domain name. |
| [get_avaible_chains](#get_avaible_chains) | Retrieves the list of chains supported by Ultrade. |
| [get_cctp_assets](#get_cctp_assets) | Retrieves the list of CCTP assets from the market endpoint. |
| [get_cctp_unified_assets](#get_cctp_unified_assets) | Retrieves the list of unified CCTP assets from the market endpoint. |
| [get_assets](#get_assets) | Retrieves the list of market assets |

---

### get_pair_list

To get the listed pair list, you need to call the `get_pair_list` method on the API instance.

```python
pairs = await client.get_pair_list()
```

**Returns:**
`List[TradingPair]` from `ultrade.types`

<details>
<summary><strong>TradingPair</strong></summary>

| Field                 | Type           | Description                                         |
| --------------------- | -------------- | --------------------------------------------------- |
| `base_chain_id`       | `int`          | Blockchain ID of the base currency.                 |
| `base_currency`       | `str`          | Base currency code.                                 |
| `base_decimal`        | `int`          | Decimal precision of the base currency.             |
| `base_id`             | `str`          | Unique identifier of the base currency.             |
| `created_at`          | `str`          | Timestamp of creation.                              |
| `id`                  | `int`          | Unique identifier of the trading pair.              |
| `is_active`           | `bool`         | Indicates if the trading pair is active.            |
| `is_verified`         | `int` (0 or 1) | Indicates if the trading pair is verified.          |
| `min_order_size`      | `str`          | Minimum order size.                                 |
| `min_price_increment` | `str`          | Minimum price increment in atomic units.            |
| `min_size_increment`  | `str`          | Minimum size increment for orders in atomic units.  |
| `pair_key`            | `str`          | Unique key of the trading pair.                     |
| `pair_name`           | `str`          | Display name of the trading pair.                   |
| `pairId`              | `int`          | Alternate identifier for the trading pair.          |
| `price_chain_id`      | `int`          | Blockchain ID of the price currency.                |
| `price_currency`      | `str`          | Price currency code.                                |
| `price_decimal`       | `int`          | Decimal precision of the price currency.            |
| `price_id`            | `str`          | Unique identifier of the price currency.            |
| `trade_fee_buy`       | `int`          | Trading fee for buying in atomic units.             |
| `trade_fee_sell`      | `int`          | Trading fee for selling in atomic units.            |
| `updated_at`          | `str`          | Timestamp of the last update.                       |
| `inuseWithPartners`   | `List[int]`    | List of partner IDs using this pair.                |
| `restrictedCountries` | `List[str]`    | List of countries where the pair is restricted.     |
| `pairSettings`        | `PairSettings` | Additional settings for the pair.                   |
| `partner_id`          | `int`          | Identifier of the partner associated with the pair. |

</details>

<details>
<summary><strong>PairSettings</strong></summary>

| Field                   | Type            | Description                            |
| ----------------------- | --------------- | -------------------------------------- |
| `mft_audioLink`         | `Optional[str]` | MFT audio link.                        |
| `view_baseCoinIconLink` | `Optional[str]` | Link to the icon of the base currency. |
| `mft_title`             | `Optional[str]` | MFT title                              |

</details>

---

### get_pair_info

The `get_pair_info` method retrieves detailed information about a specific trading pair on the Ultrade platform. It provides key data such as current price and trading volume.

| Parameter | Type  | Description                                                  |
| --------- | ----- | ------------------------------------------------------------ |
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |

```python
info = await client.get_pair_info("algo_usdt")
```

**Returns**:
`PairInfo` dict from `ultrade.types`

<details>
<summary><strong>PairInfo</strong></summary>

| Field                 | Type        | Description                                        |
| --------------------- | ----------- | -------------------------------------------------- |
| `id`                  | `int`       | Unique identifier of the trading pair.             |
| `pairId`              | `int`       | Alternate identifier for the trading pair.         |
| `pair_key`            | `str`       | Unique key of the trading pair.                    |
| `is_active`           | `bool`      | Indicates if the trading pair is active.           |
| `is_verified`         | `int` (0/1) | Indicates if the trading pair is verified.         |
| `base_chain_id`       | `int`       | Blockchain ID of the base currency.                |
| `base_currency`       | `str`       | Base currency code.                                |
| `base_decimal`        | `int`       | Decimal precision of the base currency.            |
| `base_id`             | `str`       | Unique identifier of the base currency.            |
| `price_chain_id`      | `int`       | Blockchain ID of the price currency.               |
| `price_currency`      | `str`       | Price currency code.                               |
| `price_decimal`       | `int`       | Decimal precision of the price currency.           |
| `price_id`            | `str`       | Unique identifier of the price currency.           |
| `pair_name`           | `str`       | Display name of the trading pair.                  |
| `min_price_increment` | `str`       | Minimum price increment in atomic units.           |
| `min_order_size`      | `str`       | Minimum order size in atomic units.                |
| `min_size_increment`  | `str`       | Minimum size increment for orders in atomic units. |
| `created_at`          | `str`       | Timestamp of creation.                             |
| `updated_at`          | `str`       | Timestamp of the last update.                      |

</details>

---

### ping

The `ping` method measures the latency between the client and the server by calculating the round-trip time of a request. It returns the latency in milliseconds. This method is useful for checking the responsiveness of the server or the network connection.

```python
latency = await client.ping()
print(f"Latency: {latency} ms")
```

---

### get_price

The `get_price` method fetches the current market price for a specific trading pair. It provides details such as the current ask, bid, and last trade price.

| Parameter | Type  | Description                                                  |
| --------- | ----- | ------------------------------------------------------------ |
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |

The method returns a dictionary containing the price information.

```python
price_info = await client.get_price("algo_usdt")
print(price_info)
```

**Returns:**
`Price` from `ultrade.types`

<details>
<summary><strong>Price</strong></summary>

| Field       | Type          | Description                                        |
| ----------- | ------------- | -------------------------------------------------- |
| `pairId`    | `int or None` | Market id.                                         |
| `pair`      | `str or None` | Market symbol.                                     |
| `askPrice`  | `str or None` | Ask price in atomic units.                         |
| `askQty`    | `str or None` | Ask depth in atomic units.                         |
| `bidPrice`  | `str or None` | Bid price in atomic units.                         |
| `bidQty`    | `str or None` | Bid depth in atomic units.                         |
| `lastPrice` | `str or None` | Last price in atomic units.                        |
| `ts`        | `int or None` | UTC timestamp in microseconds.                     |
| `u`         | `int or None` | The last sequence number of the order book update. |
| `U`         | `int or None` | The prev sequence number of the order book update. |

</details>

---

### get_depth

The `get_depth` method retrieves the order book depth for a specified trading pair, showing the demand and supply at different price levels.

| Parameter | Type            | Description                                                         |
| --------- | --------------- | ------------------------------------------------------------------- |
| `symbol`  | `str`           | The symbol representing the trading pair, e.g., 'algo_usdt'.        |
| `depth`   | `Optional[int]` | The depth of the order book to retrieve. Optional, defaults to 100. |

The method returns a dictionary representing the order book, including lists of bids and asks.

```python
order_book = await client.get_depth("algo_usdt", 100)
print(order_book)
```

**Returns:**
`Depth` from `ultrade.types`

<details>
<summary><strong>Depth</strong></summary>

| Field  | Type              | Description                                                                                                                                                                          |
| ------ | ----------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `sell` | `List[List[str]]` | List of sell orders. Each element contains price and quantity in atomic units.                                                                                                       |
| `buy`  | `List[List[str]]` | List of buy orders. Each element contains price and quantity atomic units.                                                                                                           |
| `ts`   | `int`             | Timestamp of data retrieval.                                                                                                                                                         |
| `pair` | `str`             | The trading pair for which the order book depth was retrieved.                                                                                                                       |
| `u`    | `int`             | A unique identifier for the last data update (lastUpdateId). This identifier can be used to compare with other update IDs to determine whether to apply the order book depth or not. |

</details>

---

### get_symbols

The `get_symbols` method retrieves a list of trading pairs that match a given pattern or partial symbol.

| Parameter | Type  | Description                                                            |
| --------- | ----- | ---------------------------------------------------------------------- |
| `mask`    | `str` | A pattern or partial symbol to filter the trading pairs, e.g., 'algo'. |

The method returns a list of dictionaries, each containing a 'pairKey' that matches the provided mask.

```python
symbols = await client.get_symbols("algo")
print(symbols)
```

**Returns:**
List of `Symbol` from `ultrade.types`
| Field | Type | Description |
| -------- | ----- | ----------------------------------------------- |
| `pairKey` | `str` | A string representing a trading pair, e.g., 'algo_usdt' for 'algo' or 'usdt'. |

---

### get_last_trades

The `get_last_trades` method retrieves the most recent trades for a specified trading pair.

| Parameter | Type  | Description                                                  |
| --------- | ----- | ------------------------------------------------------------ |
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |

```python
last_trades = await client.get_last_trades("algo_usdt")
print(last_trades)
```

**Returns:**
List of `LastTrade` from `ultrade.types`

<details>
<summary>LastTrade</summary>

| Field          | Type   | Description                                                                                                  |
| -------------- | ------ | ------------------------------------------------------------------------------------------------------------ |
| `price`        | `str`  | The price at which the trade was executed (in atomic units).                                                 |
| `amount`       | `str`  | The amount of the asset traded (in atomic units).                                                            |
| `createdAt`    | `str`  | The timestamp indicating when the trade was executed, in ISO 8601 format (e.g., '2023-12-19T16:43:40.256Z'). |
| `buy_user_id`  | `str`  | The user ID or address of the buyer in the trade.                                                            |
| `sell_user_id` | `str`  | The user ID or address of the seller in the trade.                                                           |
| `trade_side`   | `int`  | An integer indicating the trade side. A value of `0` represents a buy, and `1` represents a sell.            |
| `isBuyerMaker` | `bool` | Boolean indicating if the buyer is the maker of the trade.                                                   |

</details>

---

### get_order_by_id

The `get_order_by_id` method retrieves detailed information about an order using its unique identifier.

| Parameter  | Type  | Description                         |
| ---------- | ----- | ----------------------------------- |
| `order_id` | `int` | The unique identifier of the order. |

The method returns a dictionary containing detailed information about the specified order.

```python
order_details = await client.get_order_by_id(123456)
print(order_details)
```

**Returns:**
Dict: `Order`

<details>
<summary><strong>Order Details</strong></summary>

| Field                 | Type            | Description                                                                                                   |
| --------------------- | --------------- | ------------------------------------------------------------------------------------------------------------- |
| `id`                  | `int`           | Unique identifier of the order.                                                                               |
| `pair_id`             | `int`           | Identifier of the trading pair.                                                                               |
| `order_side`          | `int`           | Side of the order (0 for buy, 1 for sell).                                                                    |
| `order_type`          | `int`           | The type of the order (0 for limit order, 1 for ioc, 2 for post, 3 for market). `OrderType` enum from `types` |
| `order_price`         | `str`           | Price at which order was placed (in atomic units).                                                            |
| `excuted_price`       | `str`           | Price at which order was executed (in atomic units).                                                          |
| `amount`              | `str`           | Amount of tokens in the order (in atomic units).                                                              |
| `filled_amount`       | `str`           | Amount of the order that has been filled (in atomic units).                                                   |
| `total`               | `str`           | Total cost of the order (in atomic units).                                                                    |
| `filled_total`        | `str`           | Total cost of the filled amount (in atomic units).                                                            |
| `status`              | `int`           | Status of the order. Enum `OrderStatus` values: 1 (Open), 2 (Canceled), 3 (Matched), 4 (SelfMatched).         |
| `user_id`             | `str`           | User identifier.                                                                                              |
| `created_at`          | `str`           | Timestamp of when the order was created.                                                                      |
| `partner_id`          | `None` or `str` | Partner identifier (if applicable).                                                                           |
| `direct_settle`       | `int`           | Indicates if the settlement is direct.                                                                        |
| `pair_key`            | `str`           | Key of the trading pair.                                                                                      |
| `base_decimal`        | `int`           | Decimal precision of the base currency.                                                                       |
| `price_decimal`       | `int`           | Decimal precision of the price currency.                                                                      |
| `min_size_increment`  | `str`           | Minimum size increment for orders (in atomic units).                                                          |
| `min_price_increment` | `str`           | Minimum price increment for orders (in atomic units).                                                         |
| `base_id`             | `str`           | Identifier of the base currency.                                                                              |
| `price_id`            | `str`           | Identifier of the price currency.                                                                             |

</details>

---

### get_company_by_domain

The `get_company_by_domain` static method retrieves the company ID based on the domain name.

| Parameter | Type  | Description                                                                       |
| --------- | ----- | --------------------------------------------------------------------------------- |
| `domain`  | `str` | The domain of the company, e.g., "app.ultrade.org" or "https://app.ultrade.org/". |

The method returns an integer representing the company ID.

```python
from ultrade import Client

company_id = await Client.get_company_by_domain("app.ultrade.org")
print(company_id)
```

---

### get_avaible_chains

Retrieves the list of chains supported by Ultrade DeFi.

```python
avaible_chains = await client.get_avaible_chains()
print(avaible_chains)
```

### get_cctp_assets

This method retrieves the list of CCTP assets available on the Ultrade platform from the market endpoint.

```python
cctp_assets = await client.get_cctp_assets()
```

**Returns**:
dict: A dictionary containing the CCTP assets.

### get_cctp_unified_assets

This method retrieves the list of unified CCTP assets from the market endpoint, providing a standardized interface across different blockchain platforms.

```python
unified_cctp_assets = await client.get_cctp_unified_assets()
```

**Returns**:
dict: A dictionary containing the unified CCTP assets.

### get_assets

This method retrieves the list of assets from the market endpoint

```python
assets = await client.get_assets()
```

**Returns**:
Returns the list of market assets:

<details>
<summary><strong>Asset Details</strong></summary>

| Field      | Type   | Description                         |
| ---------- | ------ | ----------------------------------- |
| `id`       | `int`  | The ID of the asset                 |
| `address`  | `str`  | The address of the asset            |
| `chainId`  | `int`  | The chain ID of the asset           |
| `name`     | `str`  | The name of the asset               |
| `unitName` | `str`  | The unit name of the asset          |
| `decimals` | `int`  | The number of decimals of the asset |
| `isGas`    | `bool` | Whether the asset is gas            |

</details>

---

## Required login methods

Below are methods that require the [login function](#logging-in) to be executed
| Method | Description |
| ------ | ----------- |
| [get_balances](#get_balances) | Retrieves the current balance information for the logged-in user. |
| [get_orders_with_trades](#get_orders_with_trades) | Retrieves a list of orders along with their trade details for the logged-in user. |
| [get_orders](#get_orders) | Retrieves a list of logged user orders.
| [get_wallet_transactions](#get_wallet_transactions) | Returns a list of wallet transactions and it statuses (deposits/withdrawals) for the logged-in user. |
| [create_order](#create_order) | Creates an order on the Ultrade platform. |
| [create_bulk_orders](#create_bulk_orders) | Creates multiple orders in a single batch. |
| [cancel_order](#cancel_order) | Cancels an existing order on the Ultrade platform. |
| [cancel_bulk_orders](#cancel_bulk_orders) | Cancels multiple orders on the Ultrade platform. |
| [deposit](#deposit) | Deposit a specified amont of tokens to the Token Manager Contract. |
| [withdraw](#withdraw) | Withdraws a specified amount of tokens to a designated recipient. |
| [subscribe](#subscribe) | Subscribes the client to various websocket streams. |
| [unsubscribe](#unsubscribe) | Unsubscribes from a previously established websocket connection. |

---

### get_balances

The `get_balances` method retrieves the current balance information for the logged-in user on the Ultrade platform. It returns a list of balance details for each token associated with the user's account.

```python
balances = await client.get_balances()
```

The method returns a list of dictionaries with the following key-value pairs:

| Key            | Type           | Description                                            |
| -------------- | -------------- | ------------------------------------------------------ |
| `loginAddress` | `str`          | The blockchain address of the logged user.             |
| `loginChainId` | `int`          | The chain ID associated with the user's login address. |
| `tokenAddress` | `int` or `str` | The contract address of the token.                     |
| `tokenChainId` | `int`          | The chain ID of the token.                             |
| `amount`       | `int`          | The total amount of the token.                         |
| `lockedAmount` | `int`          | The amount of the token that is locked.                |
| `tokenId`      | `int`          | Database token id                                      |

---

### get_orders_with_trades

The `get_orders_with_trades` method retrieves a list of orders along with their trade details for the logged-in user on the Ultrade platform. It allows filtering orders based on a specific trading pair symbol and order status.  
| Parameter | Type | Description |
|-----------|---------------|----------|
| `symbol` | `Optional[str]` | The symbol of the trading pair. |
| `status` | `Optional[OrderStatus]` | The status of the orders. Defaults to `OrderStatus.OPEN_ORDER`. |

```python
from ultrade.types import OrderStatus

orders = await client.get_orders_with_trades(symbol="algo_usdc", status=OrderStatus.OPEN_ORDER)
```

**Returns:**
List of `OrderWithTrade` from `ultrade.types`

<details>
<summary>OrderWithTrade</summary>

| Field                  | Type                    | Description                                                                 |
| ---------------------- | ----------------------- | --------------------------------------------------------------------------- |
| `id`                   | `int`                   | Unique identifier of the order.                                             |
| `pair_id`              | `int`                   | Identifier of the trading pair.                                             |
| `order_side`           | `int`                   | Side of the order (0 for buy, 1 for sell).                                  |
| `order_type`           | `int`                   | Type of the order: M (market), L (limit), I (ioc), P (post only).           |
| `order_price`          | `str`                   | Price at which the order was placed. Values are in atomic units.            |
| `order_executed_price` | `str`                   | Price at which the order was executed. Values are in atomic units.          |
| `order_amount`         | `str`                   | Amount of the order. Values are in atomic units.                            |
| `order_filled_amount`  | `str`                   | Amount of the order that has been filled. Values are in atomic units.       |
| `order_total`          | `str`                   | Total value of the order. Values are in atomic units.                       |
| `order_filled_total`   | `str`                   | Total value of the filled portion of the order. Values are in atomic units. |
| `order_status`         | `int`                   | Status of the order (1: Open, 2: Canceled, 3: Matched, 4: SelfMatched).     |
| `user_id`              | `str`                   | Identifier of the user who placed the order.                                |
| `completed_at`         | `Optional[datetime]`    | Timestamp when the order was completed.                                     |
| `cancel_at`            | `Optional[datetime]`    | Timestamp when the order was cancelled, if applicable.                      |
| `created_at`           | `datetime`              | Timestamp when the order was created.                                       |
| `updated_at`           | `datetime`              | Timestamp of the last update to the order.                                  |
| `trades`               | `Optional[List[Trade]]` | List of trades associated with the order, if any.                           |

</details>

<details>
<summary>Trade</summary>

| Field              | Type                 | Description                                             |
| ------------------ | -------------------- | ------------------------------------------------------- |
| `trades_id`        | `int`                | Unique identifier of the trade.                         |
| `trade_price`      | `Optional[str]`      | Price at which the trade was executed. In atomic units. |
| `trade_amount`     | `Optional[str]`      | Amount of tokens traded. In atomic units.               |
| `trade_fee`        | `Optional[str]`      | Fee associated with the trade. In atomic units.         |
| `trade_rebate`     | `Optional[str]`      | Rebate received for the trade. In atomic units.         |
| `trade_created_at` | `Optional[datetime]` | Timestamp when the trade was created.                   |

</details>

---

### get_orders

The `get_orders` method retrieves a list of orders for the logged-in user on the Ultrade platform. It allows filtering orders based on time, pagination, and limits.

| Parameter   | Type             | Description                                                     |
| ----------- | ---------------- | --------------------------------------------------------------- |
| `startTime` | `Optional[date]` | The start time for filtering transactions (in ISO 8601 format). |
| `endTime`   | `Optional[date]` | The end time for filtering transactions (in ISO 8601 format).   |
| `page`      | `Optional[int]`  | The page number for pagination.                                 |
| `limit`     | `Optional[int]`  | The number of transactions per page.                            |

```python
orders = await client.get_orders(
    startTime='2023-12-01T00:00:00Z',
    endTime='2023-12-31T23:59:59Z',
    page=1,
    limit=50
)
```

**Returns:**
List of Orders:

<details>
<summary>Orders</summary>

| Field          | Type       | Description                                                                 |
| -------------- | ---------- | --------------------------------------------------------------------------- |
| `id`           | `int`      | Unique identifier of the order.                                             |
| `pairId`       | `int`      | Identifier of the trading pair.                                             |
| `pair`         | `str`      | Symbol of the trading pair.                                                 |
| `amount`       | `str`      | Amount of the order. Values are in atomic units.                            |
| `price`        | `str`      | Price at which the order was placed. Values are in atomic units.            |
| `total`        | `str`      | Total value of the order. Values are in atomic units.                       |
| `filledAmount` | `str`      | Amount of the order that has been filled. Values are in atomic units.       |
| `filledTotal`  | `str`      | Total value of the filled portion of the order. Values are in atomic units. |
| `status`       | `int`      | Status of the order (1: Open, 2: Canceled, 3: Matched, 4: SelfMatched).     |
| `side`         | `int`      | Side of the order (0 for buy, 1 for sell).                                  |
| `type`         | `int`      | Type of the order: M (market), L (limit), I (ioc), P (post only).           |
| `userId`       | `str`      | Identifier of the user who placed the order.                                |
| `createdAt`    | `datetime` | Timestamp when the order was created.                                       |

</details>

### get_wallet_transactions

The `get_wallet_transactions` method fetches the transaction history (deposit/withdraw) for the logged-in user on the Ultrade platform.

| Parameter   | Type             | Description                                           |
| ----------- | ---------------- | ----------------------------------------------------- |
| `startTime` | `Optional[date]` | The start time for filtering transactions. (ISO 8601) |
| `endTime`   | `Optional[date]` | The end time for filtering transactions. (ISO 8601)   |
| `page`      | `Optional[int]`  | The page number for pagination.                       |
| `limit`     | `Optional[int]`  | The number of transactions per page.                  |

```python
transactions = client.get_wallet_transactions(
    startTime='2023-12-01T00:00:00Z', # optional
    endTime='2023-12-31T23:59:59Z', # optional
    page=1, # optional
    limit=50 # optional
)
print(transactions)
```

**Returns:** a list of `WalletTransactions` dictionaries from `ultrade.types`

<details>
<summary><strong>WalletTransactions</strong></summary>

| Field            | Type   | Description                                                    |
| ---------------- | ------ | -------------------------------------------------------------- |
| `primaryId`      | `int`  | Primary identifier of the transaction.                         |
| `id`             | `str`  | Unique transaction identifier.                                 |
| `login_address`  | `str`  | Address of the user who initiated the transaction.             |
| `login_chain_id` | `int`  | Chain ID associated with the user's login address.             |
| `action_type`    | `str`  | Type of action "deposit" or "withdraw.                         |
| `status`         | `str`  | Current status of the transaction (pending, completed, failed) |
| `amount`         | `str`  | Amount involved in the transaction. In atomic units.           |
| `targetAddress`  | `str`  | Target address for the transaction.                            |
| `timestamp`      | `str`  | Timestamp when the transaction occurred.                       |
| `createdAt`      | `str`  | Timestamp when the transaction record was created.             |
| `updatedAt`      | `str`  | Timestamp of the last update to the transaction record.        |
| `token_id`       | `dict` | Details about the token involved in the transaction.           |
| `id`             | `int`  | Identifier of the token.                                       |
| `address`        | `str`  | Blockchain address of the token.                               |
| `chainId`        | `int`  | Chain ID of the token.                                         |
| `unitName`       | `str`  | Unit name of the token.                                        |
| `name`           | `str`  | Name of the token.                                             |
| `decimals`       | `int`  | Decimal precision of the token.                                |

</details>

---

### deposit

The `deposit` method allows for depositing a specified amount of tokens into the Token Manager Contract. This function requires the user to create a `Signer` instance using the mnemonic of the wallet that will act as the source for the deposit. The `Signer` wallet must be part of the same blockchain network as the asset to be deposited. For EVM-compatible networks (like Ethereum, Polygon, Binance Smart Chain, etc.), specifying the network's RPC URL via the 'rpc_url' parameter is necessary. For other blockchain networks, this parameter is optional.

| Parameter       | Type            | Description                                                                  |
| --------------- | --------------- | ---------------------------------------------------------------------------- |
| `signer`        | `Signer`        | The 'Signer' instance, created from the wallet's mnemonic.                   |
| `amount`        | `int`           | The amount of tokens to be deposited.                                        |
| `token_address` | `str` \| `int`  | The ID of the token to be deposited.                                         |
| `rpc_url`       | `str`, optional | The RPC URL of the EVM-compatible chain for the deposit. Defaults to `None`. |

Raises

```python
try:
    await client.deposit(
        signer=your_signer_instance,
        amount=5000,
        token_address="0xTokenIDorAddress",
        rpc_url="http://example.rpc.url"
    )
except Exception as e:
    print(f"Error depositing funds: {str(e)}")
```

---

### withdraw

The `withdraw` method enables the withdrawal of a specified amount of tokens to a designated recipient. To perform a withdrawal, you need to specify the recipient's wallet address where you wish to transfer the funds. This operation requires the user to be logged in and have a sufficient balance of the token they intend to withdraw.

| Parameter         | Type   | Description                                                  |
| ----------------- | ------ | ------------------------------------------------------------ |
| `amount`          | `int`  | The amount of tokens to withdraw in atomic units             |
| `token_address`   | `str`  | The blockchain address of the token.                         |
| `token_chain_id`  | `int`  | The chain ID of the token.                                   |
| `recipient`       | `str`  | The blockchain address of the recipient.                     |
| `is_native_token` | `bool` | Whether the token is native to the chain. Defaults to False. |

```python
from ultrade.types import WormholeChains

try:
    await client.withdraw(
        amount=10000,
        token_address="0xTokenAddress",
        token_chain_id=WormholeChains.POLYGON.value,
        recipient="0xRecipientAddress",
    )
except Exception as e:
    print(f"Error withdrawing funds: {str(e)}")
```

---

### create_order

The `create_order` method is used to create a new order on the Ultrade platform. This method allows you to specify various parameters for the order, including the type, side, amount, and price.

| Parameter                  | Type  | Description                                                              |
| -------------------------- | ----- | ------------------------------------------------------------------------ |
| `pair_id`                  | `int` | The ID of the trading pair.                                              |
| `order_side`               | `str` | The side of the order, 'B' (buy) or 'S' (sell).                          |
| `order_type`               | `str` | The type of the order: 'M' (market), 'L' (limit), 'I' (IOC), 'P' (post). |
| `amount`                   | `int` | The amount of tokens to buy or sell in atomic units.                     |
| `price`                    | `int` | The price is in factored units, equals decimalPrice \* 10 ^ 18.          |
| `seconds_until_expiration` | `int` | Seconds until the order expires, default=3600.                           |

```python
pair = await client.get_pair_info("algo_moon")
try:
    await client.create_order(
        pair_id=pair["id"],
        order_side="B",
        order_type="L",
        amount=3000000,  # in atomic units
        price=1500000000000000000  # in factored units
    )
except Exception as e:
    print(f"Error creating order: {str(e)}")
```

This function does not return a value.  
Raises:
`ValueError: If the order amount is below the minimum order size.`
`ValueError: If the price does not meet the minimum price increment.`
`ValueError: If there are insufficient funds in the price currency balance to execute the buy order.`
`ValueError: If there are insufficient funds in the base currency balance to execute the sell order.`

---

### create_bulk_orders

The `create_bulk_orders` method is used to create multiple orders in a single batch operation on the Ultrade platform. It takes a list of order objects and sends them one by one using the same logic as `create_order`.

Each order in the list must include the same required parameters as `create_order`.

| Parameter                     | Type         | Description                                                               |
| ----------------------------- | ------------ | ------------------------------------------------------------------------- |
| `orders`                      | `list[dict]` | A list of order dictionaries. Each dictionary must contain the following: |
| ├─ `pair_id`                  | `int`        | The ID of the trading pair.                                               |
| ├─ `order_side`               | `str`        | The side of the order: 'B' (buy) or 'S' (sell).                           |
| ├─ `order_type`               | `str`        | The type of the order: 'M', 'L', 'I', or 'P'.                             |
| ├─ `amount`                   | `int`        | The amount of tokens to buy or sell in atomic units.                      |
| ├─ `price`                    | `int`        | The price in factored units (decimalPrice \* 10^18).                      |
| └─ `seconds_until_expiration` | `int`        | _(Optional)_ Time in seconds until the order expires. Default is 3660.    |

#### Example

```python
pair = await client.get_pair_info("algo_moon")

orders = [
    {
        "pair_id": pair["id"],
        "order_side": "B",
        "order_type": "L",
        "amount": 1000000,
        "price": 1500000000000000000
    },
    {
        "pair_id": pair["id"],
        "order_side": "S",
        "order_type": "L",
        "amount": 2000000,
        "price": 1600000000000000000
    }
]

try:
    await client.create_bulk_orders(orders)
except Exception as e:
    print(f"Error creating bulk orders: {str(e)}")
```

This function does not return a value.

**Raises:**

- `ValueError`: If any order has invalid parameters.
- `Exception`: If there is an error in the response for any order.

---

#### cancel_order

The `cancel_order` method is used to cancel an existing order on the Ultrade platform. This method requires the user to be logged in and have a valid order to cancel.

| Parameter  | Type  | Description                          |
| ---------- | ----- | ------------------------------------ |
| `order_id` | `int` | The ID of the order to be cancelled. |

To cancel an order, provide the ID of the order you wish to cancel. The method checks if the user is logged in before proceeding. It is asynchronous and must be awaited.

Returns: void if order succsesfully canceled

Raises: Exception: If there is an error in the response from the server.
`Exception: {'statusCode': 404, 'message': 'Order not found', 'error': 'Not Found'}`

```python
orders = await client.get_orders_with_trades()
order = orders[0] # the first one order in array
order_id = order["id"]
try:
    await client.cancel_order(order_id)
    print(f"Order with ID {order_id} has been successfully canceled.")
except Exception as e:
    print(f"Error canceling order with ID {order_id}: {str(e)}")
```

---

#### cancel_bulk_orders

The `cancel_bulk_orders` method is used to cancel multiple orders at once on the Ultrade platform. This method requires the user to be logged in and each order must have a valid ID for cancellation.

| Parameter   | Type        | Description                          |
| ----------- | ----------- | ------------------------------------ |
| `order_ids` | `list[int]` | A list of order IDs to be cancelled. |
| `pair_id`   | `list[int]` | A trading pair ID.                   |

To cancel multiple orders, provide pair ID and a list of order IDs from this pair. The method checks if the user is logged in before proceeding. It is asynchronous and must be awaited.

Returns: void if orders are successfully canceled.

Raises:

- `Exception`: If there is an error in the response from the server.
- `Exception`: If any of the provided orders are not found.

```python
orders = await client.get_orders_with_trades()
order_ids = [order["id"] for order in orders[:5]]  # cancel the first 5 orders

try:
    await client.cancel_bulk_orders(order_ids)
    print(f"Successfully canceled orders with IDs: {', '.join(map(str, order_ids))}")
except Exception as e:
    print(f"Error canceling orders with IDs {', '.join(map(str, order_ids))}: {str(e)}")
```

---

### subscribe

The `subscribe` method subscribes the client to various WebSocket streams based on the provided options. This method is useful for real-time data monitoring on the Ultrade platform.

| Parameter  | Type       | Description                                                 |
| ---------- | ---------- | ----------------------------------------------------------- |
| `options`  | `dict`     | A dictionary containing the WebSocket subscription options. |
| `callback` | `function` | A function to be called on receiving a WebSocket event.     |

<strong>Websocket Subscription Options:</strong>

| Field     | Type                       | Description                                                                                                   |
| --------- | -------------------------- | ------------------------------------------------------------------------------------------------------------- |
| `symbol`  | `str`                      | The symbol representing the trading pair, e.g., "yldy_stbl".                                                  |
| `streams` | `List[int]`                | Identifiers for the types of data streams to subscribe to. Each number represents a different type of stream. |
| `options` | `Dict[str, Optional[str]]` | Additional options for the subscription.                                                                      |

<strong>Stream Identifiers in `socket_options`:</strong>

| Stream/ID                 | Events                   | Description                                                                              |
| ------------------------- | ------------------------ | ---------------------------------------------------------------------------------------- |
| `QUOTE` - 1               | `quote`                  | Real-time quotes for a trading pair. (ask/bid)                                           |
| `LAST_PRICE` - 2          | `lastPrice`              | The latest price of the trading pair.                                                    |
| `DEPTH` - 3               | `depth`                  | The depth of the order book.                                                             |
| `ORDERS` - 5              | `order`                  | Real-time updates of orders.                                                             |
| `TRADES` - 6              | `lastTrade`, `userTrade` | `lastTrade`: Info about last executed trade. <br>`userTrade`: info about last user trade |
| `MAINTENANCE` - 7         | `maintenance`            | Notifications of maintenance events                                                      |
| `WALLET_TRANSACTIONS` - 8 | `walletTransaction`      | Updates on wallet transactions (deposits, withdraws)                                     |
| `ALL_STAT` - 9            | `allStat`                | Statistics about all trading pairs.                                                      |
| `CODEX_BALANCES` - 10     | `codexBalances`          | Balance information of your login address.                                               |

<strong>`options` Parameter:</strong>

- `address`: Optional. The wallet address to use for subscriptions. If the user is logged in, this is optional and will default to the logged-in user's address.
- `companyId`: Optional. The identifier for a specific company. Used to receive data specific to that company.

```python
from ultrade import socket_options

options = {
    'symbol': "yldy_stbl",
    'streams': [socket_options.ORDERS, socket_options.TRADES],
    'options': {"address": "your wallet address here", "companyId": "optional company ID"}
}

async def event_handler(event, data):
    print(event)
    print(data)

connection_id = await client.subscribe(options, event_handler)
```

---

### unsubscribe

The `unsubscribe` method is used to disconnect the client from a previously established websocket connection. This is particularly useful for stopping real-time data feeds that are no longer needed, helping to manage resource usage effectively.

| Parameter       | Type  | Description                                                 |
| --------------- | ----- | ----------------------------------------------------------- |
| `connection_id` | `str` | The ID of the websocket connection to be unsubscribed from. |

To unsubscribe from a websocket stream, you need to provide the connection ID obtained when you initially subscribed to the stream. The method is asynchronous and must be awaited.

```python
await client.unsubscribe("your_connection_id")
```
