import base64
import json
import requests
from solders.message import  to_bytes_versioned # type: ignore
from solders.keypair import Keypair # type: ignore
from solders.transaction import VersionedTransaction # type: ignore
from solana.rpc.api import Client
from solana.rpc.commitment import Processed, Finalized
from solana.rpc.types import TxOpts

RPC = "https://api.mainnet-beta.solana.com"
SOL = "So11111111111111111111111111111111111111112"  

def get_quote(input_mint, output_mint, amount, slippage_bps):
    try:
        url = "https://quote-api.jup.ag/v6/quote"
        params = {
            'inputMint': input_mint,
            'outputMint': output_mint,
            'amount': amount,
            'slippageBps': slippage_bps
        }
        headers = {'Accept': 'application/json'}
        response = requests.get(url, headers=headers, params=params)
        return response.json()
    except Exception as e:
        print(f"Error in get_quote: {e}")
        return None

def get_swap(user_public_key, quote_response):
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
        return response.json()
    except Exception as e:
        print(f"Error in get_swap_instructions: {e}")
        return None

def swap(priv_key, input_mint, output_mint, amount_lamports, slippage_bps):
    try:
        client = Client(RPC)
        keypair = Keypair().from_base58_string(priv_key)
        pub_key_str = str(keypair.pubkey())
        amount_lamports = int(amount_lamports * 1e9)
        
        quote_response = get_quote(input_mint, output_mint, amount_lamports, slippage_bps)
        if not quote_response:
            print("No quote response.")
            return False
        print(quote_response)
        
        swap_transaction = get_swap(pub_key_str, quote_response)
        if not swap_transaction:
            print("No swap transaction response.")
            return False
        print(swap_transaction)
        
        raw_transaction = VersionedTransaction.from_bytes(base64.b64decode(swap_transaction['swapTransaction']))
        signature = keypair.sign_message(to_bytes_versioned(raw_transaction.message))
        signed_txn = VersionedTransaction.populate(raw_transaction.message, [signature])
        opts = TxOpts(skip_preflight=False, preflight_commitment=Processed)
        tx_sig = client.send_raw_transaction(txn=bytes(signed_txn), opts=opts).value
        print(f"Transaction Signature: {tx_sig}")
        
        confirmation = client.confirm_transaction(tx_sig, commitment=Finalized).value
        print(f"Confirm Transaction: {confirmation}")
        return True
    except Exception as e:
        print(e)
        return False
        
def buy_token(priv_key_str, output_mint, amount, slippage_bps=5000):
    return swap(priv_key_str, SOL, output_mint, amount, slippage_bps)

def sell_token(priv_key_str, input_mint, amount, slippage_bps=5000):
    return swap(priv_key_str, input_mint, SOL, amount, slippage_bps)