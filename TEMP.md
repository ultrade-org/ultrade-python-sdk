# ultrade

## Introduction

The `ultrade` package is a Python SDK for interacting with the Ultrade DeFi. It provides a simple interface for creating and signing transactions, as well as for interacting with the Ultrade API.

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
| algo_sdk_client | The Algorand SDK client. | None |


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
  mnemonic_key = "lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod tempor incididunt ut labore et dolore magna aliqua..."
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

### Getting balances

To get your logged user balances you need to call the `get_balances` method on the client instance. The `get_balances` method return a list of balacnce object with the following properties:

- `loginAddress`: The address of the logged user.
- `loginChainId`: The chain ID of the logged user.
- `tokenId`: The ID of the token.
- `tokenChainId`: The chain ID of the token.
- `amount`: The amount of tokens.
- `lockedAmount`: The amount of locked tokens.


```python

balances = await client.get_balances()

```

### Getting orders

To get orders, you need to call the `get_orders_with_trades` method on the client instance. The `get_orders_with_trades` method takes an optional `status` argument. If the `status` argument is not provided, all orders are returned. If the `status` argument is provided, only orders with the provided status are returned.

```python

orders = await client.get_orders_with_trades()

```

#  async def get_transactions(self, symbol=None) -> List[WalletTransaction]:
### Getting transactions

To get transactions, you need to call the `get_transactions` method on the client instance. The `get_transactions` method takes an optional `symbol` argument. If the `symbol` argument is not provided, all transactions are returned. If the `symbol` argument is provided, only transactions with the provided symbol are returned.

```python

transactions = await client.get_transactions()
  
```

### Getting the pair list

To get the pair list, you need to call the `get_pair_list` method on the API instance. The `get_pair_list` method takes an optional `company_id` argument. If the `company_id` argument is not provided, all pairs are returned. If the `company_id` argument is provided, only pairs with the provided company ID are returned.

```python

pairs = await api.get_pair_list()
  
  ```

### Creating an order

To create an order, you need to call the `create_order` method on the client instance. The `create_order` method takes the following arguments:

- `pair_id`: The ID of the pair.
- `company_id`: The ID of the company.
- `order_side`: The order side. Can be either `B` (buy) or `S` (sell).
- `order_type`: The order type. Can be either `L` (limit) or `M` (market).
- `amount`: The amount of tokens to buy or sell.
- `price`: The price of the order.
- `base_token_address`: The address of the base token.
- `base_token_chain_id`: The chain ID of the base token.
- `price_token_address`: The address of the price token.
- `price_token_chain_id`: The chain ID of the price token.

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

### Cancelling an order

To cancel an order, you need to call the `cancel_order` method on the client instance. The `cancel_order` method takes the ID of the order as an argument.
  
  ```python

  res = await client.cancel_order(order["id"])
  if res == "Order cancelled successfully":
      print("Order cancelled successfully")
  
    ```
