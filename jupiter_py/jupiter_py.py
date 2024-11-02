import base64
import json
import requests
from typing import Any, Dict, Optional, Union
from solders.message import to_bytes_versioned  # type: ignore
from solders.transaction import VersionedTransaction  # type: ignore
from solana.rpc.api import Client
from solana.rpc.commitment import Processed
from solana.rpc.types import TxOpts
from utils import confirm_txn, get_token_balance_lamports
from config import payer_keypair, RPC

SOL = "So11111111111111111111111111111111111111112"

def get_quote(input_mint: str, output_mint: str, amount: int, slippage_bps: int) -> Optional[Dict[str, Any]]:
    try:
        url = "https://quote-api.jup.ag/v6/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps,
            'onlyDirectRoutes': 'true'
        }
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error in get_quote: {e}")
        return None

def get_swap(user_public_key: str, quote_response: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    try:
        url = "https://quote-api.jup.ag/v6/swap"
        payload = json.dumps({
            "userPublicKey": user_public_key,
            "wrapAndUnwrapSol": True,
            "useSharedAccounts": True,
            "quoteResponse": quote_response
        })
        headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
        response = requests.post(url, headers=headers, data=payload)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Error in get_swap: {e}")
        return None

def swap(input_mint: str, output_mint: str, amount_lamports: int, slippage_bps: int) -> bool:
    client = Client(RPC)
    pub_key_str = str(payer_keypair.pubkey())
    
    quote_response = get_quote(input_mint, output_mint, amount_lamports, slippage_bps)
    if not quote_response:
        print("No quote response.")
        return False
    print("Quote response:\n", json.dumps(quote_response, indent=4), "\n")
    
    swap_transaction = get_swap(pub_key_str, quote_response)
    if not swap_transaction:
        print("No swap transaction response.")
        return False
    print("Swap transaction:", json.dumps(swap_transaction, indent=4), "\n")
    
    raw_transaction = VersionedTransaction.from_bytes(
        base64.b64decode(swap_transaction['swapTransaction'])
    )
    signature = payer_keypair.sign_message(to_bytes_versioned(raw_transaction.message))
    signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
    opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)

    try:
        txn_sig = client.send_raw_transaction(
            txn=bytes(signed_txn), opts=opts
        ).value
        print("Transaction Signature:", txn_sig)
        
        print("Confirming transaction...")
        confirmed = confirm_txn(txn_sig)
        print("Transaction confirmed:", confirmed)
        
        return confirmed
    
    except Exception as e:
        print(f"Failed to send transaction: {e}")
        return False

def buy(token_address: str, sol_in: Union[int, float], slippage: int = 5) -> bool:
    amount_lamports = int(sol_in * 1e9)
    slippage_bps = slippage * 100
    return swap(SOL, token_address, amount_lamports, slippage_bps)

def sell(token_address: str, percentage: int = 100, slippage: int = 5) -> bool:

    if not (1 <= percentage <= 100):
        print("Percentage must be between 1 and 100.")
        return False
    
    token_balance = get_token_balance_lamports(token_address)
    print("Token Balance:", token_balance)    
    
    if token_balance == 0:
        print("No token balance available to sell.")
        return False
    
    sell_amount = int(token_balance * (percentage / 100))
    slippage_bps = slippage * 100
    
    return swap(token_address, SOL, sell_amount, slippage_bps)
