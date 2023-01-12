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


**Args**

* **identifier** (str|int)(optional) : symbol or pair id

---
Return object with pair info
If identifier is not specified return list of pairs info

----


### ping
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L40)
```python
.ping()
```

---
Check server connections

Return latency of the request in ms

----


### get_order_by_id
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L56)
```python
.get_order_by_id(
   symbol, order_id
)
```

---
Find order with specified id and symbol

Return order object

----


### get_open_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L76)
```python
.get_open_orders(
   symbol
)
```

---
Get orderbook for the specified symbol

Return orderbook object

----


### get_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L95)
```python
.get_orders(
   symbol, status, start_time, end_time, limit = 500, page = 0
)
```


----


### get_price
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L102)
```python
.get_price(
   symbol
)
```

---
Get prices of specified pair from the server

----


### get_depth
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L114)
```python
.get_depth(
   symbol, depth = 100
)
```

---
Get depth for specified symbol from the Ultrade exchange

Parameters:
symbol (str): symbol represent existing pair, example: 'algo_usdt'

depth (int): depth for specific pair, max_value=100

----


### get_last_trades
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L130)
```python
.get_last_trades(
   symbol
)
```

---
Get last trades for the specified symbol from the Ultrade exchange

----


### get_symbols
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L142)
```python
.get_symbols(
   mask
)
```

---
Return a list of dictionaries with matched pair keys

Return example: [{'pairKey': 'algo_usdt'}]

----


### get_history
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L156)
```python
.get_history(
   symbol, interval = '', start_time = '', end_time = '', limit = ''
)
```

---
Get trade history with graph data from the Ultrade exchange

----


### get_address_orders
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L168)
```python
.get_address_orders(
   address, status = 1, symbol = None
)
```

---
Get orders list for specified address

With default status it return only open orders
If symbol not specified, return orders for pairs
