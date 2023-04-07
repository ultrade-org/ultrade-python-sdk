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
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L99)
```python
.new_order(
   symbol, side, type, quantity, price, partner_app_id = 0, direct_settle = 'N'
)
```

---
Create new order on the Ultrade exchange by sending group transaction to algorand API


**Args**

* **symbol** (str) : symbol represent existing pair, example: 'algo_usdt'
* **side** (str) : represent either 'S' or 'B' order (SELL or BUY)
* **type** (str) : can be one of these four order types: 'L', 'P', 'I' or 'M',
    which represent LIMIT, POST, IOC and MARKET orders respectively
* **quantity** (decimal) : quantity of the base coin
* **price** (decimal) : quantity of the price coin
* **partner_app_id** (int, default=0) : id of the partner to use in transactions
* **direct_settle** (str) : can be either "N" or "Y"


---
If order successfully fulfilled returns dictionary with order_id and slot data in it

### .cancel_order
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L221)
```python
.cancel_order(
   symbol: str, order_id: int, slot: int
)
```

---
Cancel the order matching the id and symbol arguments


**Args**

* **symbol** (str) : symbol represent existing pair, example: 'algo_usdt'
* **order_id** (int) : id of the order to cancel, can be provided by Ultrade API
* **slot** (int) : order position in the smart contract


**Returns**

* **str**  : First transaction id


### .cancel_all_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L256)
```python
.cancel_all_orders(
   symbol
)
```

---
Perform cancellation of all existing orders for wallet specified in algod client


**Args**

* **symbol** (str) : symbol represent existing pair, example: 'algo_usdt'


**Returns**

* **str**  : First transaction id


### .subscribe
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L300)
```python
.subscribe(
   options, callback
)
```

---
Subscribe client to websocket streams listed in arg "options"
Can be used multiple times for different pairs


**Args**

* **options** (dict) : websocket subscribe options, example:
    {
        'symbol': "yldy_stbl",
        'streams': [OPTIONS.ORDERS, OPTIONS.TRADES],
        'options': {"address": "your wallet address here"}
    }
* **callback** (function) : a synchronous function, will be called on any occurred websocket event, should accept 'event' and 'args' parameters


**Returns**

* **str**  : Id of the established connection


### .unsubscribe
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L321)
```python
.unsubscribe(
   connection_id
)
```

---
Unsubscribe from ws connection


**Args**

* **connection_id** (str) : Id of the connection


### .get_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L330)
```python
.get_orders(
   symbol = None, status = 1, start_time = None, end_time = None, limit = 500
)
```

---
Get orders list for specified address
With default status it return only open orders
If symbol not specified, return orders for all pairs


**Args**

* **symbol** (str) : symbol represents existing pair, example: 'algo_usdt'
* **status** (int) : status of the returned orders


**Returns**

list

### .get_wallet_transactions
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L353)
```python
.get_wallet_transactions(
   symbol = None
)
```

---
Get last transactions from current wallet, max_amount=100


**Args**

* **symbol** (str) : symbol represents existing pair, example: 'algo_usdt'


**Returns**

list

### .get_order_by_id
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L373)
```python
.get_order_by_id(
   symbol, order_id
)
```

---
Get order with specific id and symbol


**Returns**

dict

### .get_balances
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L394)
```python
.get_balances(
   symbol
)
```

