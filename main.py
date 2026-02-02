from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from pycardano import (
    Address,
    TransactionBuilder,
    TransactionOutput,
    Value,
    Transaction
)
from cardano import context
import binascii

app = FastAPI(title="Cardano Mainnet API Gateway")

# -------------------- Pydantic Models --------------------
class BuildTxRequest(BaseModel):
    sender_address: str
    recipient_address: str
    amount_lovelace: int

class SubmitTxRequest(BaseModel):
    tx_cbor: str  # signed CBOR HEX

# -------------------- Helpers --------------------
def validate_address(addr: str) -> bool:
    try:
        Address.from_primitive(addr)
        return True
    except Exception:
        return False

# -------------------- Routes --------------------
@app.get("/wallet/ping/")
def wallet_ping():
    return {"status": "wallet route active"}


@app.post("/tx/build/")
def build_transaction(req: BuildTxRequest):
    # Validate Bech32 addresses
    if not validate_address(req.sender_address):
        raise HTTPException(status_code=400, detail="Invalid sender address")
    if not validate_address(req.recipient_address):
        raise HTTPException(status_code=400, detail="Invalid recipient address")

    try:
        sender = Address.from_primitive(req.sender_address)
        recipient = Address.from_primitive(req.recipient_address)

        # Initialize transaction builder with Blockfrost context
        builder = TransactionBuilder(context)

        # Add sender inputs (requires funded UTxOs)
        builder.add_input_address(sender)

        # Add recipient output
        builder.add_output(TransactionOutput(recipient, Value(req.amount_lovelace)))

        # Build unsigned transaction
        tx = builder.build(change_address=sender)

        return {
            "tx_cbor": tx.to_cbor_hex(),
            "message": "Unsigned transaction built. Sign this CBOR in wallet."
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/tx/submit/")
def submit_transaction(req: SubmitTxRequest):
    try:
        # Convert hex → bytes
        tx_bytes = binascii.unhexlify(req.tx_cbor)

        # Submit raw transaction bytes
        tx_hash = context.submit_tx(tx_bytes)

        return {
            "tx_hash": str(tx_hash),
            "status": "Transaction submitted successfully"
        }

    except Exception as e:
        raise HTTPException(400, str(e))
