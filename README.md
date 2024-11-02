# jupiter_py

Simple python implementation of the Jupiter Swap API.

Clone the repo, and add your Private Key (Base58 string) and RPC to the config.py.

Reference: https://station.jup.ag/docs/apis/swap-api

```
from jupiter_py import buy

# Buy Example
token_address = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr" # POPCAT
sol_in = .1
slippage = 10
buy(token_address, sol_in, slippage)
```

```
from jupiter_py import sell

# Sell Example
token_address = "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr" # POPCAT
percentage = 100
slippage = 10
sell(token_address, percentage, slippage)
```
