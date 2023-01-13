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


### get_price
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L58)
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
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L73)
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

order book for the specified pair

----


### get_symbols
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L92)
```python
.get_symbols(
   mask
)
```

---
Return example: For mask="algo_u" -> [{'pairKey': 'algo_usdt'}]


**Returns**

list of symbols matching the mask

----


### get_history
[source](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/ultrade/api.py/#L107)
```python
.get_history(
   symbol, interval = '', start_time = '', end_time = '', limit = ''
)
```

---
Get trade history with graph data from the Ultrade exchange


**Returns**

history object
