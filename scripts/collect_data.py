import os
import time
import pandas as pd
import requests
from dotenv import load_dotenv


load_dotenv()

API_KEY = os.getenv("ETHERSCAN_API_KEY")
ETHERSCAN_API_URL = "https://api.etherscan.io/v2/api?chainid=1"

COMPOUND_V2_COMPTROLLER = "0x3d9819210a31b4961b30ef54be2aed79b9c9cd3b".lower()

COMPOUND_CONTRACTS = [
    COMPOUND_V2_COMPTROLLER,
    "0x5d3a536e4d6dbd6114cc1ead35777bab948e3643".lower(), 
    "0x39aa39c021dfbae8fac545936693ac917d5e7563".lower(),  
    "0xc3d688b66703497daa19211eedff47f25384cdc3".lower(),  
    
]
INPUT_WALLETS_FILE = "data/wallets.csv"
OUTPUT_TRANSACTIONS_FILE = "data/compound_v2_v3_transactions.csv"

def fetch_all_transactions(wallet_address):
    """Fetches all transactions for a single wallet address, handling pagination."""
    all_transactions = []
    page = 1
    while True:
        params = {
            "module": "account",
            "action": "txlist",
            "address": wallet_address,
            "startblock": 0,
            "endblock": 99999999,
            "page": page,
            "offset": 1000,
            "sort": "asc",
            "apikey": API_KEY,
        }
        
        try:
            response = requests.get(ETHERSCAN_API_URL, params=params)
            response.raise_for_status()
            data = response.json()

            if data["status"] == "1" and isinstance(data["result"], list):
                transactions = data["result"]
                all_transactions.extend(transactions)
                if len(transactions) < 1000:
                    break
                page += 1
            else:
                break
        
        except requests.exceptions.RequestException as e:
            print(f"Error fetching data for {wallet_address}: {e}")
            break

        time.sleep(0.25)
        
    return all_transactions

def main():
    """Main function to run the data collection and filtering process."""
    print("Starting data collection...")
    
    try:
        wallets_df = pd.read_csv(INPUT_WALLETS_FILE)
        wallet_addresses = wallets_df['wallet_id'].tolist()
    except FileNotFoundError:
        print(f"Error: Input file not found at {INPUT_WALLETS_FILE}")
        return
    except KeyError:
        print(f"Error: The CSV must have a column named 'wallet_id'.")
        return

    all_compound_transactions = []

    for i, address in enumerate(wallet_addresses):
        print(f"Processing wallet {i+1}/{len(wallet_addresses)}: {address}")
        
        wallet_txs = fetch_all_transactions(address)
        
        for tx in wallet_txs:
            to_address = tx.get("to", "").lower()
            if to_address in COMPOUND_CONTRACTS:
                tx['wallet_address'] = address
                tx['protocol_version'] = "V2" if to_address == COMPOUND_V2_COMPTROLLER else "V3" 
                all_compound_transactions.append(tx)

    if not all_compound_transactions:
        print("No Compound V2 or V3 transactions were found for any of the wallets.")
    else:
        output_df = pd.DataFrame(all_compound_transactions)
        output_df.to_csv(OUTPUT_TRANSACTIONS_FILE, index=False)
        print(f"\n✅ Success! {len(output_df)} Compound V2/V3 transactions saved to {OUTPUT_TRANSACTIONS_FILE}")

if __name__ == "__main__":
    main()