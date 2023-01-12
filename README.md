# ultrade-python-sdk

## Sources:

### ultrade_sdk.Client:

    https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/docs/client.md

### ultrade_sdk.api:

    https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/docs/api.md

## Quick start

```python
from algosdk.v2client import algod
from ultrade.sdk_client import Client

algod_token = "your algod token here"
algod_address = "your algod address"

# create algod client
algod_client = algod.AlgodClient(algod_token, algod_address)


options = {
    "network": "testnet",
    "algo_sdk_client": algod_client,
    "api_url": None,
    "websocket_url": "wss://dev-ws.ultradedev.net/socket.io"
    }

credentials = {"mnemonic": "your mnemonic here"}

# create ultrade-sdk client
client = Client(credentials, options)
```
