#


### get_exchange_info
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L7)
```python
.get_exchange_info(
   identifier = None
)
```

---
Get pair info from the Ultrade exchange
If identifier is not specified returns a list of pairs info


**Args**

* **identifier** (str|int) : symbol or pair id


**Returns**

object with pair info

----


### ping
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L41)
```python
.ping()
```

---
Check connection with server 


**Returns**

latency of the sent request in ms

----


### get_order_by_id
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L58)
```python
.get_order_by_id(
   symbol, order_id
)
```

---
Find order with specified id and symbol


**Returns**

order object

----


### get_open_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L79)
```python
.get_open_orders(
   symbol
)
```

---
Get orderbook for the specified symbol


**Returns**

orderbook object

----


### get_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L99)
```python
.get_orders(
   symbol, status, start_time, end_time, limit = 500, page = 0
)
```


----


### get_price
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L106)
```python
.get_price(
   symbol
)
```

---
Get prices for the specified pair from the server


**Returns**

current price of the pair

----


### get_depth
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L121)
```python
.get_depth(
   symbol, depth = 100
)
```

---
Get depth for specified symbol from the Ultrade exchange


**Args**

* **symbol** (str) : symbol represent existing pair, for example: 'algo_usdt'
* **depth** (int) : depth for specific pair, max_value=100


**Returns**

depth object for the specified pair

----


### get_last_trades
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L140)
```python
.get_last_trades(
   symbol
)
```

---
Get last trades for the specified symbol from the Ultrade exchange


**Returns**

last trades from the exchange

----


### get_symbols
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L155)
```python
.get_symbols(
   mask
)
```

---
Return example: For mask="algo_u" -> [{'pairKey': 'algo_usdt'}]


**Returns**

list of symbols matched the mask  

----


### get_history
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L170)
```python
.get_history(
   symbol, interval = '', start_time = '', end_time = '', limit = ''
)
```

---
Get trade history with graph data from the Ultrade exchange


**Returns**

history object

----


### get_address_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L185)
```python
.get_address_orders(
   address, status = 1, symbol = None
)
```

---
Get orders list for specified address
With default status it return only open orders
If symbol not specified, return orders for all pairs


**Returns**

list of order objects
