# Reddio
REDDIO_RPC_URL="https://reddio-dev.reddio.com"
REDDIO_CHAIN_ID=50341
REDDIO_COIN_NAME="RED"

# Sepolia
SEPOLIA_RPC_URL="https://endpoints.omniatech.io/v1/eth/sepolia/public"
SEPOLIA_CHAIN_ID=11155111
SEPOLIA_COIN_NAME="ETH"

BRIDGE_CONTRACT_ADDRESS = "0xB74D5Dba3081bCaDb5D4e1CC77Cc4807E1c4ecf8"
BRIDGE_CONTRACT_ABI = [
    {
        "constant": False,
        "inputs": [
            {"name": "_from", "type": "address"},
            {"name": "amount", "type": "uint256"},
            {"name": "escrowFee", "type": "uint256"}
        ],
        "name": "depositETH",
        "outputs": [{"name": "", "type": "bool"}],
        "payable": True,
        "stateMutability": "payable",
        "type": "function",
    }
]
