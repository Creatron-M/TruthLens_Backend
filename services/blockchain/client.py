import json, os
from web3 import Web3
from dotenv import load_dotenv

load_dotenv()

BSC_RPC = os.getenv("BSC_TESTNET_RPC", "https://bsc-testnet.publicnode.com")
PRIVATE_KEY = os.getenv("ORACLE_SIGNER_KEY")
CONTRACT_ADDR_RAW = os.getenv("ORACLE_CONTRACT", "0x0000000000000000000000000000000000000000")
CONTRACT_ADDR = Web3.to_checksum_address(CONTRACT_ADDR_RAW)

with open(os.path.join(os.path.dirname(__file__), 'abi.json')) as f:
    ABI = json.load(f)

w3 = Web3(Web3.HTTPProvider(BSC_RPC))
acct = w3.eth.account.from_key(PRIVATE_KEY) if PRIVATE_KEY else None
contract = w3.eth.contract(address=CONTRACT_ADDR, abi=ABI)

def submit_attestation(market_id_bytes32: bytes, cred: int, risk: int, meta_uri: str = "") -> str:
    if not acct:
        raise ValueError("ORACLE_SIGNER_KEY environment variable is required for blockchain operations")
    if not (0 <= cred <= 100) or not (0 <= risk <= 100):
        raise ValueError("Credibility and risk scores must be between 0 and 100")
    nonce = w3.eth.get_transaction_count(acct.address)
    tx = contract.functions.submitAttestation(market_id_bytes32, cred, risk, meta_uri).build_transaction({
        'from': acct.address,
        'nonce': nonce,
        'gas': 250000,
        'gasPrice': w3.eth.gas_price
    })
    signed = acct.sign_transaction(tx)
    # Use signed.raw_transaction for newer web3.py versions, fallback to rawTransaction
    raw_tx = getattr(signed, 'raw_transaction', getattr(signed, 'rawTransaction', None))
    tx_hash = w3.eth.send_raw_transaction(raw_tx)
    return tx_hash.hex()

def read_latest(market_id_bytes32: bytes):
    return contract.functions.latest(market_id_bytes32).call()