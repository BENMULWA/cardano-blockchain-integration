from fastapi import FastAPI, HTTPException, status
from dotenv import load_dotenv
from pycardano import(
    BlockFrostChainContext,
    Network,
    TransactionBuilder,
    TransactionOutput,
    PaymentSigningKey,
    PaymentVerificationKey,
    Address
    
)
import os

# Load env
load_dotenv()

app = FastAPI(title="Cardano Shelley APIs for transaction", version="1.0")

PROJECT_ID = os.getenv("PROJECT_ID")
MASTER_KEY_PATH = os.getenv("MASTER_KEY_PATH")
SENDER_ADDR = os.getenv("SENDER_ADDR")

print("DEBUG PROJECT_ID:", PROJECT_ID) 
print("DEBUG MASTER_KEY_PATH:", MASTER_KEY_PATH) 
print("DEBUG SENDER_ADDR:", SENDER_ADDR)    

# Guard clause
if not PROJECT_ID or not MASTER_KEY_PATH or not SENDER_ADDR:
    raise RuntimeError("Missing environment variables. Check your .env file.")

# Load signing key
MASTER_SKEY = PaymentSigningKey.load(MASTER_KEY_PATH)

# Convert sender address string into Address object
MASTER_ADD = Address.from_primitive(SENDER_ADDR)

# Use base_url instead of deprecated network arg
context = BlockFrostChainContext(
    project_id=PROJECT_ID,
    network=Network.TESTNET
)


# 1. APi -- generating the shelly adresses

@app.post("/adress/create-new", status_code=status.HTTP_201_CREATED)
def create_new_address():
    skey = PaymentSigningKey.generate()
    vkey = PaymentVerificationKey.from_signing_key(skey)

    # am now using shelly era (decentralized  leger era)
    new_address = Address(payment_part=vkey.hash(), network=Network.TESTNET)
    return {
        "id": str(new_address),
        "state": "unused shelly address",
        "derivation_path": ["1852H"],
        "skey_cbor": skey.to_cbor().hex(), # stores this key in my enctrypted db 
        "vkey_cbor": vkey.to_cbor().hex() # this is the public key that i can use to derive the address and also to verify signatures
    
    }


# 2.Withdraw funds from customer wallet to mater wallep( sweep logic to withdrwaw all funds from customer wallet)

@app.post("/transaction/withdraw-funnds", status_code=status.HTTP_200_OK)
def withdraw_funds(sender_addr: str, sender_skey_cbor: str):
    try:
        skey = PaymentSigningKey.from_cbor(sender_skey_cbor)
        vkey = PaymentVerificationKey.from_signing_key(skey)
        builder= TransactionBuilder(context)

        # Automate UTXO selection and fee handling
        builder.add_input_address(Address.from_primitive(sender_addr))
        
    
        signed_tx = builder.build_and_sign( # handles the calculation and balances automatically
            signing_keys=[skey],
            change_address=MASTER_ADD
        )
        context.submit_tx(signed_tx.to_cbor())
        return {"tx_id": signed_tx, "status": "Withdrawal successful"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction failed: {e}")
    

# 3 Feching the wallet balance 

@app.get("/wallet/{address}/balance", status_code=status.HTTP_200_OK)
def get_wallet_balance(address:str):
    try:
        utxos = context.utxos(address)
        total_balance = sum([utxo.output.amount for utxo in utxos])
        return{"address":address, "balance_ada": total_balance / 1_000_000} # convert lovelace to ada
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch balance: {e}")    
   

# 4 Customer to customer Tansfer Logic

@app.post("/transaction/send-ada", status_code=status.HTTP_200_OK)
def send_ada(sender_addr: str, sender_skey_cbor: str, recipient_addr: str, amount_ada: float):
    try:
        skey= PaymentSigningKey.from_cbor(sender_skey_cbor)
        builder= TransactionBuilder(context)

        # Add inputs from the sender
        lovelace_amount = int(amount_ada * 1_000_000) # convert ada to lovelace
        builder.add_input_address(Address.from_primitive(sender_addr))

        # Add output for the recipient
        builder.add_output(
            TransactionOutput(Address.from_primitive(recipient_addr), lovelace_amount))
        signed_tx = builder.build_and_sign([skey], change_address=Address.from_primitive(sender_addr))
    
        context.submit_tx(signed_tx)
        
        return {"txtx_id": signed_tx.id, "status": "Transaction successful", "explorer_link": f"https://preprod.cardanoscan.io/transaction/{signed_tx.id}"}
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transaction failed: {e}")
    
    
