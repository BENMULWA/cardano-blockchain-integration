import os
from fastapi import FastAPI
import pycardano as pyc
from cardano_Apis import app
from dotenv import load_dotenv
from pycardano import (
    BlockFrostChainContext, 
    Address, 
    TransactionBuilder, 
    TransactionOutput, 
    PaymentSigningKey,
    Network,
    PaymentVerificationKey
)

# --- 1. CONFIGURATION ---
# Load env first
load_dotenv()

# Your verified Blockfrost Project ID for Preprod
PROJECT_ID = os.getenv("PROJECT_ID")

# Addresses from your payload
SENDER_ADDR = os.getenv("SENDER_ADDR") 
RECIPIENT_ADDR = os.getenv("RECIPIENT_ADDR") 
AMOUNT_LOVELACE = int(os.getenv("AMOUNT_LOVELACE", "1000000"))

# Path to your signing key inside my directory
KEY_PATH = os.getenv("MASTER_KEY_PATH")   # FIXED: match .env variable name

# --- 2. INITIALIZE CONTEXT ---
# Use base_url instead of deprecated network arg
from blockfrost import ApiUrls

# Correct initialization for Preprod
context = BlockFrostChainContext(
    project_id=PROJECT_ID,
    base_url=ApiUrls.preprod.value
)


# --- 3. VALIDATION LOGIC ---

# --- 3. VALIDATION LOGIC ---
def validate_address_setup(sender_addr: str, key_path: str):
    try:
        if not os.path.exists(key_path):
            print(f"Validation Error: Signing key not found at {key_path}")
            return False

        a = Address.from_primitive(sender_addr)
        
        # FIX 1: Compare against the Network enum
        if a.network != Network.TESTNET: 
            print(f"Validation Error: {sender_addr} is not a Testnet address.")
            return False

        skey = PaymentSigningKey.load(key_path)
        vkey = PaymentVerificationKey.from_signing_key(skey)
        
        # FIX 2: Use Network.TESTNET instead of 0
        derived_addr = Address(payment_part=vkey.hash(), network=Network.TESTNET)

        if str(derived_addr) != sender_addr:
            print(f"Validation Error: The signing key does not match the address.")
            print(f"Expected: {derived_addr}")
            print(f"Actual:   {sender_addr}")
            return False

        return skey
    except Exception as e:
        print(f"Setup Validation Error: {e}")
        return False

# --- 4. TRANSACTION LOGIC ---
def run_transaction():
    print("--- Starting Cardano Transaction (2026 Conway Era) ---")
    
    # Validate addresses before proceeding
    if not validate_address_setup(SENDER_ADDR, KEY_PATH):
        print("Sender address validation failed.")
        return

    try:
        # Load the signing key from my folder
        psk = PaymentSigningKey.load(KEY_PATH)
        print("Successfully loaded signing key.")

        # Initialize Builder
        builder = TransactionBuilder(context)
        
        # Add inputs from the sender
        builder.add_input_address(Address.from_primitive(SENDER_ADDR))
        
        # Add output for the recipient
        builder.add_output(
            TransactionOutput(Address.from_primitive(RECIPIENT_ADDR), AMOUNT_LOVELACE)
        )

        # 5 Build and Sign
        signed_tx = builder.build_and_sign(
            signing_keys=[psk],
            change_address=Address.from_primitive(SENDER_ADDR)
        )

        # Check UTXOs at the sender address
        utxos = context.utxos(Address.from_primitive(SENDER_ADDR))
        if not utxos:
            print(f"Error: No UTXOs found at {SENDER_ADDR}. Please fund this wallet.")
            return
        
        print(f"Found {len(utxos)} UTXO(s). Building transaction...")

        # Inspect transaction details before signing
        print("\n Transaction Details Before Signing")
        print("-" * 30)
        print("Transaction Fee:", builder.fee) 
        print("Outputs:", builder.outputs)
        print(f"Network Fee: {signed_tx.transaction_body.fee / 1_000_000} ADA")
        print(f"Transaction ID: {signed_tx.id}")
        print("Inputs:", builder.inputs)
        print("-" * 30)

        # Submit to the blockchain via Blockfrost api
        print("\nSubmitting transaction to the network...")
        print(f"Transaction Built. ID: {signed_tx.id}")
        context.submit_tx(signed_tx)
        
        print("\n--- SUCCESS ---")
        print(f"Transaction submitted to Preprod network.")
        print(f"Explorer Link: https://preprod.cardanoscan.io/transaction/{signed_tx.id}")
        print("\n--- End of Transaction ---")

    except Exception as e:
        print(f"\nFailed to execute transaction: {e}")

if __name__ == "__main__":
    run_transaction()
