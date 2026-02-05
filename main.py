import os
from fastapi import FastAPI
import pycardano as pyc
from cardano_Apis import app
from pycardano import (
                        BlockFrostChainContext, 
                        Network, 
                        Address, 
                        TransactionBuilder, 
                        TransactionOutput, 
                        PaymentSigningKey,
                        PaymentVerificationKey
                    )

# --- 1. CONFIGURATION ---
# Your verified Blockfrost Project ID for Preprod
PROJECT_ID = "preprodjay9yDspQlStomPpCjwJUFFLQ3rqXBqL"

# Addresses from your payload
SENDER_ADDR = "addr_test1vps2yazypdvh9h9vjwqm52c32a6gaj79528ed9jcdtrs6cgk7f65k"
RECIPIENT_ADDR = "addr_test1vqeux7xwusdju9dvsj8h7mca9aup2k439kfmwy773xxc2hcu7zy99"
AMOUNT_LOVELACE = 1000000  # 1 ADA

# Path to your signing key inside my directory
KEY_PATH = "/home/software-engineer/mam-laka/cardano/wallet/sender/payment.skey"

# --- 2. INITIALIZE CONTEXT ---
# Network.TESTNET maps to the Preprod/Preview environments in PyCardano
context = BlockFrostChainContext(
    project_id=PROJECT_ID,
    network=Network.TESTNET
)

# --- 3. VALIDATION LOGIC ---
def validate_address_setup(sender_addr: str,KEY_PATH: str) -> bool:
    """Checks if the address is a valid Cardano Testnet address and matches it to the appropratesigning key."""
    try:
        if not os.path.exists(KEY_PATH):
            print(f"Validation Error: Signing key not found at {KEY_PATH}")
            return False
        
        a = Address.from_primitive(sender_addr)
        if a.network != Network.TESTNET:
            print(f"Validation Error: {sender_addr} is not a Testnet address.")
            return False
        
        skey= PaymentSigningKey.load(KEY_PATH)
        vkey= PaymentVerificationKey.from_signing_key(skey)

        derived_addr = Address(payment_part=vkey.hash(), network=Network.TESTNET)
        if str(derived_addr) != sender_addr:
            print(f"Validation Error: The signing key does not match the address {sender_addr}.")
        
        
        return skey
    except Exception as e:
        print(f"setup -Validation Error: {e}")
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
        if not os.path.exists(KEY_PATH):
            print(f"Error: Signing key not found at {KEY_PATH}")
            return
        
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
        # This automatically calculates fees and handles 'change' back to sender
        signed_tx = builder.build_and_sign(
            signing_keys=[psk],
            change_address=Address.from_primitive(SENDER_ADDR)
        )

        # Check UTXOs at the sender address
        utxos = context.utxos(SENDER_ADDR)
        if not utxos:
            print(f"Error: No UTXOs found at {SENDER_ADDR}. Please fund this wallet.")
            return
        
        print(f"Found {len(utxos)} UTXO(s). Building transaction...")


    # inspect trasction details before signing
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
