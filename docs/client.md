#


## Client
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L44)
```python 
Client(
   auth_credentials: AccountCredentials, options: ClientOptions
)
```


---
UltradeSdk client. Provides methods for creating and canceling orders on Ultrade exchange. Also can be used for subscribing to Ultrade data streams


**Args**

* **credentials** (dict) : credentials as a mnemonic or a private key
* **options** (dict) : options allows to change default URLs for API



**Methods:**


### .new_order
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L85)
```python
.new_order(
   symbol, side, type, quantity, price
)
```

---
Create new order on the Ultrade exchange by sending group transaction to algorand API


**Args**

* **symbol** (str) : symbol represent existing pair, example: 'algo_usdt'
* **side** (str) : represent either 'S' or 'B' order (SELL or BUY)
* **type** (str) : can be one of these four order types: '0', 'P', 'I' or 'M',
    which are represent LIMIT, POST, IOK and MARKET orders respectively
* **quantity** (decimal) : quantity of the base coin
* **price** (decimal) : quantity of the price coin



**Returns**

* **str**  : First transaction id


### .cancel_order
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L150)
```python
.cancel_order(
   symbol: str, order_id: int
)
```

---
Cancel the order matching the id and symbol arguments


**Args**

* **symbol** (str) : symbol represent existing pair, example: 'algo_usdt'
* **order_id** (int) : id of the order to cancel, can be provided by Ultrade API


**Returns**

* **str**  : First transaction id


### .cancel_all_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L176)
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


### .get_balance_and_state
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L205)
```python
.get_balance_and_state(
   address
)
```


### .subscribe
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L220)
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
* **callback** (function) : a function, will be called on any occurred websocket event, should accept 'event' and 'args' parameters


**Returns**

* **str**  : Id of the established connection


### .unsubscribe
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/sdk_client.py/#L241)
```python
.unsubscribe(
   connection_id
)
```

---
Unsubscribe from ws connection


**Args**

* **connection_id** (str) : Id of the connection

