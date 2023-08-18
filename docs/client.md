#


## Client
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L48)
```python 
Client(
   auth_credentials: AccountCredentials, options: ClientOptions
)
```


---
UltradeSdk client. Provides methods for creating and canceling orders on Ultrade exchange. Also can be used for subscribing to Ultrade data streams


**Args**

* **auth_credentials** (dict) : credentials as a mnemonic or a private key
* **options** (dict) : options allows to change default URLs for the API calls, also options should have algod client



**Methods:**


### .new_order
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L96)
```python
.new_order(
   symbol, side, type, quantity, price, partner_app_id = 0, direct_settle = 'N'
)
```

---
Create new order on the Ultrade exchange by sending group transaction to algorand API


**Args**

* **symbol** (str) : The symbol representing an existing pair, for example: 'algo_usdt'
* **side** (str) : Represents either a 'S' or 'B' order (SELL or BUY).
* **type** (str) : Can be one of the following four order types: 'L', 'P', 'I', or 'M', which represent LIMIT, POST, IOC, and MARKET orders respectively.
* **quantity** (decimal) : The quantity of the base coin.
* **price** (decimal) : The quantity of the price coin.
* **partner_app_id** (int, default=0) : The ID of the partner to use in transactions.
* **direct_settle** (str) : Can be either "N" or "Y".


**Returns**

* The ID of the created order.
* The slot data of the created order.
A dictionary with the following keys:

### .cancel_order
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L214)
```python
.cancel_order(
   symbol: str, order_id: int, slot: int, fee = None
)
```

---
Cancel the order matching the ID and symbol arguments.


**Args**

* **symbol** (str) : The symbol representing an existing pair, for example: 'algo_usdt'.
* **order_id** (int) : The ID of the order to cancel, which can be provided by the Ultrade API.
* **slot** (int) : The order position in the smart contract.
* **fee** (int, default=None) : The fee needed for canceling an order with direct settlement option enabled.


**Returns**

The first transaction ID.

### .cancel_all_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L258)
```python
.cancel_all_orders(
   symbol, fee = None
)
```

---
Perform cancellation of all existing orders for the wallet specified in the Algod client.


**Args**

* **symbol** (str) : The symbol representing an existing pair, for example: 'algo_usdt'.
* **fee** (int, default=None) : The fee needed for canceling orders with direct settlement option enabled.


**Returns**

The first transaction ID.

### .subscribe
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L313)
```python
.subscribe(
   options, callback
)
```

---
Subscribe the client to websocket streams for the specified options.


**Args**

* **options** (dict) : A dictionary containing the websocket subscribe options, for example:
    {
        'symbol': "yldy_stbl",
        'streams': [OPTIONS.ORDERS, OPTIONS.TRADES],
        'options': {"address": "your wallet address here"}
    }
* **callback** (function) : A synchronous function that will be called on any occurred websocket event and should accept 'event' and 'args' parameters.


**Returns**

* **str**  : The ID of the established connection.


### .unsubscribe
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L333)
```python
.unsubscribe(
   connection_id
)
```

---
Unsubscribe from a websocket connection.


**Args**

* **connection_id** (str) : The ID of the connection to unsubscribe from.


### .get_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L342)
```python
.get_orders(
   symbol = None, status = 1, start_time = None, end_time = None, limit = 500
)
```

---
Get a list of orders for the specified address.

With the default status, it will return only open orders.
If no symbol is specified, it will return orders for all pairs.


**Args**

* **symbol** (str) : The symbol representing an existing pair, for example: 'algo_usdt'.
* **status** (int) : The status of the returned orders.


**Returns**

* **list**  : A list of orders.


### .get_wallet_transactions
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L366)
```python
.get_wallet_transactions(
   symbol = None
)
```

---
Get the last transactions from the current wallet with a maximum amount of 100.


**Args**

* **symbol** (str) : The symbol representing an existing pair, for example: 'algo_usdt'.


**Returns**

* **list**  : A list of transactions.


### .get_order_by_id
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L386)
```python
.get_order_by_id(
   symbol, order_id
)
```

---
Get an order by the specified ID and symbol.


**Returns**

* **dict**  : A dictionary containing the order information.


### .get_balances
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L407)
```python
.get_balances(
   symbol
)
```

---
Returns a dictionary containing information about the assets stored in the wallet and exchange pair for a specified symbol. Return value contains the following keys:
- 'priceCoin_available': The amount of price asset stored in the current pair and available for usage
- 'baseCoin_locked': The amount of base asset locked in the current pair
- 'baseCoin_available': The amount of base asset stored in the current pair and available for usage
- 'baseCoin': The amount of base asset stored in the wallet
- 'priceCoin': The amount of price asset stored in the wallet


**Args**

* **symbol** (str) : The symbol representing an existing pair, for example: 'algo_usdt'


**Returns**

dict

### .get_account_balances
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L451)
```python
.get_account_balances(
   exchange_pair_list = None
)
```

---
Returns a list of dictionaries containing information about the assets stored in the wallet and exchange pairs. Each dictionary includes the following keys:
- 'free': the amount of the asset stored in the wallet.
- 'total': the total amount of the asset, including any amounts stored in exchange pairs as available or locked balance.
- 'asset': the name of the asset.
---
The list contains one dictionary for each asset.


**Args**

* **exchange_pair_list** (dict[], default=None) : list of pairs to get balances for,
    if not provided, would return balance for all currently available pairs.
    To get pairs that you want, use function "api.get_pair_list()".


**Returns**

List of dictionaries
