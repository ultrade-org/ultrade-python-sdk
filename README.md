# ultrade-python-sdk

## Sources:

- [ultrade_sdk.Client](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/docs/client.md) — main client, requires credentials

- [ultrade_sdk.api](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/docs/api.md) — module for interaction with ultrade public API

## Quick start

```python
from algosdk.v2client import algod
from ultrade.sdk_client import Client

algod_token = ""    # your algod token here, empty if use a public node
algod_address = https://node.testnet.algoexplorerapi.io     # Your algod node adress. Pass this for default public testnet nide

# create algod client
algod_client = algod.AlgodClient(algod_token, algod_address)


options = {
    "network": "testnet",
    "algo_sdk_client": algod_client,
    "api_url": None,
    "websocket_url": "wss://testnet-ws.ultradedev.net/socket.io"
    }

credentials = {"mnemonic": 'alpha bravo charlie delta'}

# create ultrade-sdk client
client = Client(credentials, options)
```

### Testing:

To run tests, type:

```bash
pytest -n auto tests
```

### Generating Documentation:

To generate .md documentation, run:

```bash
gendocs --config mkgendocs.yml
```

Docs will be located in the `docs/` directory.
