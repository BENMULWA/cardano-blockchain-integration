from pycardano import BlockFrostChainContext, Network, Address
import os

PROJECT_ID = os.getenv("BLOCKFROST_PROJECT_ID", "preprodjay9yDspQlStomPpCjwJUFFLQ3rqXBqL")



context = BlockFrostChainContext(
    project_id=PROJECT_ID,
    network=Network.TESTNET   # covers Preprod in your version
)

print("Blockfrost TESTNET context initialized successfully")

def validate_address(addr: str) -> bool:
    try:
        a = Address.from_primitive(addr)
        if a.network != Network.TESTNET:
            raise ValueError("Address is not testnet")
        return True
    except Exception:
        return False
