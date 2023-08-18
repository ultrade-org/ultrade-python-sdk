# ultrade-python-sdk

## Sources:

- [ultrade_sdk.Client](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/docs/client.md) — main client, requires credentials

- [ultrade_sdk.api](https://github.com/ultrade-org/ultrade-python-sdk/blob/develop/docs/api.md) — module for interaction with ultrade public API

## Quick start

```python
from algosdk.v2client import algod
from ultrade.sdk_client import Client

algod_token = ""    # Your algod token here, for public node usage pass an empty string
algod_address = "https://testnet-api.algonode.cloud"    # Your algod node address.

# create algod client
algod_client = algod.AlgodClient(algod_token, algod_address)


options = {
    "network": "testnet",
    "algo_sdk_client": algod_client,
    "api_url": None,
    }

credentials = {"mnemonic": 'alpha bravo charlie delta...'}

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
