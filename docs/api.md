#


### get_exchange_info
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L47)
```python
.get_exchange_info(
   symbol
)
```

---
Get info about specified pair


**Args**

* **symbol** (str) : symbol represents existing pair, example: 'algo_usdt'


**Returns**

dict

----


### ping
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L68)
```python
.ping()
```

---
Check connection with server


**Returns**

* **int**  : latency of the sent request in ms


----


### get_price
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L85)
```python
.get_price(
   symbol
)
```

---
Get prices for the specified pair


**Args**

* **symbol** (str) : symbol represents existing pair, example: 'algo_usdt'


**Returns**

dict

----


### get_depth
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L103)
```python
.get_depth(
   symbol, depth = 100
)
```

---
Get depth for specified symbol from the Ultrade exchange


**Args**

* **symbol** (str) : symbol represents existing pair, example: 'algo_usdt'
depth (int, default=100, max_value=100)


**Returns**

* **dict**  : order book for the specified pair


----


### get_symbols
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L122)
```python
.get_symbols(
   mask
)
```

---
Return example: For mask="algo_usdt" -> [{'pairKey': 'algo_usdt'}]


**Returns**

list

----


### get_history
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L137)
```python
.get_history(
   symbol, interval = None, start_time = None, end_time = None, limit = None, page = None
)
```


**Returns**

dict
