# Ultrade

## Table of Contents
1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Usage](#usage)
   - [Creating a Client](#creating-a-client)
   - [Creating a Signer](#creating-a-signer)
   - [Logging In](#logging-in)
   - [Creating an API Instance](#creating-an-api-instance)
   - [Getting Balances](#getting-balances)
   - [Getting Orders](#getting-orders)
   - [Getting Transactions](#getting-transactions)
   - [Getting the Pair List](#getting-the-pair-list)
   - [Creating an Order](#creating-an-order)
   - [Cancelling an Order](#cancelling-an-order)
   - [Withdrawing Tokens](#withdrawing-tokens)
   - [Subscribe to Websocket Streams](#subscribe-to-websocket-streams)
   - [Unsubscribe from Websocket Streams](#unsubscribe-from-websocket-streams)
   - [Get Exchange Information](#get-exchange-information)
   - [Ping](#ping)
   - [Get Price](#get-price)
   - [Get Depth](#get-depth)
   - [Get Symbols](#get-symbols)
   - [Get Trading History](#get-trading-history)
   - [Get Last Trades](#get-last-trades)
   - [Get Order by ID](#get-order-by-id)
   - [Get Company by Domain](#get-company-by-domain)

## Introduction

The `ultrade` package is a Python SDK for interacting with the Ultrade DeFi. It provides a simple interface for creating and signing transactions, as well as for interacting with the Ultrade API and streams

## Installation

To install the `ultrade` package, you can use pip:
  
  ```bash
  pip install ultrade
  ```
## Usage

### Creating a client

To create a client, you need to provide the network. The network can be either `mainnet` or `testnet`. You can also provide aditional options discribet in the table below.

| Option | Description | Default value |
| --- | --- | --- |
| api_url | The URL of the Ultrade API. | https://api.ultrade.io |
| websocket_url | The URL of the Ultrade WebSocket API. | wss://ws.ultrade.io |
| algo_sdk_client | The Algorand SDK client. | Public client |


```python
from ultrade.sdk_client import Client

client = Client(network="testnet")
```

### Creating a signer

To create a signer, you need to provide the mnemonic key. The mnemonic key is a 25-word phrase for Algorand or EVM private key.  
Signer can be used to login, deposit, withdraw and signing transactions.
  
  ```python
  from ultrade import Signer
  #algorand
  mnemonic_key = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod ..."
  #EVM
  mnemonic_key = "e421abcdb55899d7bc2be1652a64a63fffc3cf654e989ebcce45k121d6a34a"
  signer = Signer.create_signer(mnemonic_key)
  ```

### Logging in

To log in, you need to call the `set_login_user` method on the client instance. The `set_login_user` method takes a signer as an argument.

```python
await client.set_login_user(signer)

isLogged = client.is_logged_in()
```

### Creating an API Instance

The `create_api` method is designed to create an instance of the public API. This instance provides access to various functionalities of the Ultrade platform that do not require user authentication.

```python
api = client.create_api()
```

### Getting balances

The `get_balances` method retrieves the current balance information for the logged-in user on the Ultrade platform. It returns a list of balance details for each token associated with the user's account.  

```python
balances = await client.get_balances()
```
The method returns a list of dictionaries with the following key-value pairs:

| Key            | Type         | Description                               |
|----------------|--------------|-------------------------------------------|
| `loginAddress` | `str`        | The blockchain address of the logged user.|
| `loginChainId` | `int`        | The chain ID associated with the user's login address. |
| `tokenId`      | `int` or `str` | The identifier of the token.          |
| `tokenChainId` | `int`        | The chain ID of the token.                |
| `amount`       | `int`        | The total amount of the token.            |
| `lockedAmount` | `int`        | The amount of the token that is locked.   |


### Getting orders

The `get_orders_with_trades` method retrieves a list of orders along with their trade details for the logged-in user on the Ultrade platform. It allows filtering orders based on a specific trading pair symbol and order status.  
| Parameter | Type          | Optional | Description                                  |
|-----------|---------------|----------|----------------------------------------------|
| `symbol`  | `str`         | Yes      | The symbol of the trading pair.              |
| `status`  | `OrderStatus` | Yes      | The status of the orders. Defaults to `OrderStatus.OPEN_ORDER`. |

```python
from ultrade.types import OrderStatus

orders = await client.get_orders_with_trades(symbol="algo_usdc", status=OrderStatus.OPEN_ORDER)
```

### Getting Transactions

The `get_transactions` method fetches the transaction history for the logged-in user on the Ultrade platform. It optionally allows filtering the transactions by a specific trading pair symbol.

| Parameter | Type    | Optional | Description                               |
|-----------|---------|----------|-------------------------------------------|
| `symbol`  | `str`   | Yes      | The symbol of the trading pair to filter transactions. If not provided, transactions for all pairs are returned. |

The method returns a list of `WalletTransaction` dictionaries, each representing a transaction.

```python
transactions = await client.get_transactions(symbol="algo_usdc")
for transaction in transactions:
    print(f"Transaction ID: {transaction['id']}, Amount: {transaction['amount']}")
```

### Getting the pair list

To get the pair list, you need to call the `get_pair_list` method on the API instance. The `get_pair_list` method takes an optional `company_id` argument. If the `company_id` argument is not provided, all pairs are returned. If the `company_id` argument is provided, only pairs with the provided company ID are returned.

```python
pairs = await api.get_pair_list()
```

### Creating an Order

The `create_order` method is used to create a new order on the Ultrade platform. This method allows you to specify various parameters for the order, including the type, side, amount, and price.


| Parameter             | Type   | Description                                      |
|-----------------------|--------|--------------------------------------------------|
| `pair_id`             | `int`  | The ID of the trading pair.                      |
| `company_id`          | `int`  | The ID of the company associated with the order. |
| `order_side`          | `str`  | The side of the order, 'B' (buy) or 'S' (sell).  |
| `order_type`          | `str`  | The type of the order, 'L' (limit) or 'M' (market). |
| `amount`              | `int`  | The amount of tokens to buy or sell.             |
| `price`               | `int`  | The price per token for the order.               |
| `base_token_address`  | `str`  | The blockchain address of the base token.        |
| `base_token_chain_id` | `int`  | The chain ID of the base token.                  |
| `price_token_address` | `str`  | The blockchain address of the price token.       |
| `price_token_chain_id`| `int`  | The chain ID of the price token.                 |


To create an order, you need to provide details about the order such as the pair ID, company ID, order side and type, amount, price, and the addresses and chain IDs of the tokens involved. The method is asynchronous and must be awaited.

```python
res = await client.create_order(
    pair_id=pair["id"],
    company_id=1,
    order_side="B",
    order_type="L",
    amount=350000000,
    price=1000,
    base_token_address=pair["base_id"],
    base_token_chain_id=pair["base_chain_id"],
    price_token_address=pair["price_id"],
    price_token_chain_id=pair["price_chain_id"],
)

if res == "Order created successfully":
    print("Order created successfully")
```

### Cancelling an Order

The `cancel_order` method is used to cancel an existing order on the Ultrade platform. This method requires the user to be logged in and have a valid order to cancel.


| Parameter  | Type   | Description                       |
|------------|--------|-----------------------------------|
| `order_id` | `int`  | The ID of the order to be cancelled. |


To cancel an order, provide the ID of the order you wish to cancel. The method checks if the user is logged in before proceeding. It is asynchronous and must be awaited.

```python
try:
    response = await client.cancel_order(order_id)
    if response == "Order cancelled successfully":
        print("Order cancelled successfully")
except Exception as error:
    print(f"Error: {error}")
```

### Withdrawing Tokens

The `withdraw` method enables the withdrawal of a specified amount of tokens to a designated recipient. This operation requires the user to be logged in and have sufficient token balance.


| Parameter          | Type  | Description                               |
|--------------------|-------|-------------------------------------------|
| `amount`           | `int` | The amount of tokens to withdraw.         |
| `token_address`    | `str` | The blockchain address of the token.      |
| `token_chain_id`   | `int` | The chain ID of the token.                |
| `recipient`        | `str` | The blockchain address of the recipient.  |
| `recipient_chain_id` | `int` | The chain ID of the recipient's address. |


To perform a withdrawal, specify the amount, token address, token chain ID, recipient address, and recipient chain ID. The method is asynchronous and must be awaited.

```python
from ultrade.types import WormholeChains

try:
    response = await client.withdraw(
        amount=1000,
        token_address="0xTokenAddress",
        token_chain_id=WormholeChains.POLYGON.value,
        recipient="0xRecipientAddress",
        recipient_chain_id=WormholeChains.POLYGON.value
    )
    print(response)  # Response from the server
except Exception as error:
    print(f"Error: {error}")
 ```
 
 ### Subscribe to Websocket Streams
 
 The subscribe method subscribes the client to various websocket streams based on the provided options. This method is useful for real-time data monitoring on the Ultrade platform.
 | Parameter          | Type  | Description                               |
|--------------------|-------|-------------------------------------------|
| `options`           | `dict` | A dictionary containing the websocket subscription options. |
| `callback`    | `function` | A function to be called on receiving a websocket event.      |

```python
from ultrade import socket_options

options = {
    'symbol': "yldy_stbl",
    'streams': [socket_options.ORDERS, socket_options.TRADES],
    'options': {"address": "your wallet address here"}
}

async def event_handler(event, data):
    pass

connection_id = await client.subscribe(options, event_handler)
```

### Unsubscribe from Websocket Streams

The `unsubscribe` method is used to disconnect the client from a previously established websocket connection. This is particularly useful for stopping real-time data feeds that are no longer needed, helping to manage resource usage effectively.


| Parameter       | Type   | Description                                       |
|-----------------|--------|---------------------------------------------------|
| `connection_id` | `str`  | The ID of the websocket connection to be unsubscribed from. |


To unsubscribe from a websocket stream, you need to provide the connection ID obtained when you initially subscribed to the stream. The method is asynchronous and must be awaited.

```python
await client.unsubscribe("your_connection_id")
```

### Get Exchange Information

The `get_exchange_info` method retrieves detailed information about a specific trading pair on the Ultrade platform. It provides key data such as current price and trading volume.


| Parameter | Type  | Description                                            |
|-----------|-------|--------------------------------------------------------|
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |

Returns:
- `dict`: A dictionary containing detailed information about the trading pair. This includes data such as current price, trading volume, etc.


```python
info = await client.get_exchange_info("algo_usdt")
print(info)
```

### Ping

The `ping` method measures the latency between the client and the server by calculating the round-trip time of a request. It returns the latency in milliseconds. This method is useful for checking the responsiveness of the server or the network connection.

```python
latency = await client.ping()
print(f"Latency: {latency} ms")
```

### Get Price

The `get_price` method fetches the current market price for a specific trading pair. It provides details such as the current ask, bid, and last trade price.

| Parameter | Type  | Description                                            |
|-----------|-------|--------------------------------------------------------|
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |


The method returns a dictionary containing the price information.

```python
price_info = await client.get_price("algo_usdt")
print(price_info)
```
### Get Depth

The `get_depth` method retrieves the order book depth for a specified trading pair, showing the demand and supply at different price levels.

| Parameter | Type  | Description                                              |
|-----------|-------|----------------------------------------------------------|
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |
| `depth`   | `int` | The depth of the order book to retrieve. Optional, defaults to 100. |

The method returns a dictionary representing the order book, including lists of bids and asks.

```python
order_book = await client.get_depth("algo_usdt", 100)
print(order_book)
```

### Get Symbols

The `get_symbols` method retrieves a list of trading pairs that match a given pattern or partial symbol.

| Parameter | Type  | Description                                              |
|-----------|-------|----------------------------------------------------------|
| `mask`    | `str` | A pattern or partial symbol to filter the trading pairs, e.g., 'algo'. |

The method returns a list of dictionaries, each containing a 'pairKey' that matches the provided mask.

```python
symbols = await client.get_symbols("algo")
print(symbols)
```

### Get Trading History

The `get_history` method fetches the trading history for a specific trading pair and interval.

| Parameter   | Type  | Description                                              |
|-------------|-------|----------------------------------------------------------|
| `symbol`    | `str` | Trading pair symbol, e.g., 'algo_usdc'.                  |
| `interval`  | `str` | Interval for the trading data, e.g., '1m', '1h'.         |
| `start_time`| `int` | Optional. Start timestamp for the history data.          |
| `end_time`  | `int` | Optional. End timestamp for the history data.            |
| `limit`     | `int` | Optional. Number of records to retrieve. Defaults to 500.|
| `page`      | `int` | Optional. Page number for pagination. Defaults to 1.     |

The method returns a dictionary containing the trading history for the specified trading pair and interval.

```python
history = await client.get_history("btc_usd", "1h", start_time=1609459200, end_time=1609545600)
print(history)
```
### Get Last Trades

The `get_last_trades` method retrieves the most recent trades for a specified trading pair.

| Parameter | Type  | Description                                            |
|-----------|-------|--------------------------------------------------------|
| `symbol`  | `str` | The symbol representing the trading pair, e.g., 'algo_usdt'. |

The method returns a list of the most recent trades for the specified trading pair.

```python
last_trades = await client.get_last_trades("algo_usdt")
print(last_trades)
```

### Get Order by ID

The `get_order_by_id` method retrieves detailed information about an order using its unique identifier.

| Parameter | Type  | Description                               |
|-----------|-------|-------------------------------------------|
| `order_id`| `int` | The unique identifier of the order.       |

The method returns a dictionary containing detailed information about the specified order.

```python
order_details = await client.get_order_by_id(123456)
print(order_details)
```
### Get Company by Domain

The `get_company_by_domain` method retrieves the company ID based on the domain name.

| Parameter | Type  | Description                               |
|-----------|-------|-------------------------------------------|
| `domain`  | `str` | The domain of the company, e.g., "app.ultrade.org" or "https://app.ultrade.org/". |

The method returns an integer representing the company ID.

If the specified company is not enabled, or if an error occurs during the API request, a `CompanyNotEnabledException` is raised.

Example:
```python
company_id = await client.get_company_by_domain("app.ultrade.org")
print(company_id)
```
