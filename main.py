import time
import random
from datetime import timedelta 
from core.config import BRIDGE_CONTRACT_ABI, BRIDGE_CONTRACT_ADDRESS, REDDIO_RPC_URL, REDDIO_COIN_NAME, SEPOLIA_CHAIN_ID, SEPOLIA_RPC_URL
from core.utils import connect_to_web3, get_account, random_between, retry
from solcx import install_solc, set_solc_version, compile_source
from colorama import Fore, Style, init

# Install Solidity Compiler
install_solc('0.8.0')
set_solc_version('0.8.0')

# Initialize colorama for terminal color support
init(autoreset=True)

# ASCII art with red and white colors
ASCII_ART = r"""

 ░▒▓███████▓▒░▒▓█▓▒░░▒▓█▓▒░░▒▓██████▓▒░░▒▓████████▓▒░░▒▓██████▓▒░  
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░      ░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░░▒▓█▓▒░    ░▒▓██▓▒░░▒▓█▓▒░░▒▓█▓▒░ 
 ░▒▓██████▓▒░ ░▒▓██████▓▒░░▒▓████████▓▒░  ░▒▓██▓▒░  ░▒▓████████▓▒░ 
       ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░░▒▓██▓▒░    ░▒▓█▓▒░░▒▓█▓▒░ 
       ░▒▓█▓▒░  ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓█▓▒░      ░▒▓█▓▒░░▒▓█▓▒░ 
░▒▓███████▓▒░   ░▒▓█▓▒░   ░▒▓█▓▒░░▒▓█▓▒░▒▓████████▓▒░▒▓█▓▒░░▒▓█▓▒░ 
                                                                   
                                                                   
"""

# Red and White colors
RED = Fore.RED
WHITE = Fore.WHITE

def print_red_white_ascii_art():
    """Prints ASCII art with the top half in red and bottom half in white."""
    # Split ASCII art into lines
    ascii_lines = ASCII_ART.split('\n')
    
    # Calculate the middle of the ASCII art (to split it into red and white parts)
    mid_point = len(ascii_lines) // 2
    
    # Print the upper half in red
    for i in range(mid_point):
        print(RED + ascii_lines[i] + Style.RESET_ALL)
    
    # Print the lower half in white
    for i in range(mid_point, len(ascii_lines)):
        print(WHITE + ascii_lines[i] + Style.RESET_ALL)
    
    # Add the 'Reddio Onchain' text at the bottom right in white
    text_to_add = "Reddio Onchain"
    
    # Find the length of the longest line in ASCII art
    max_line_length = max(len(line) for line in ascii_lines)  # Find the longest line
    
    # Adjust the text position to be closer to the bottom right (exact alignment)
    text_position = max_line_length - len(text_to_add)  # Position text at the exact right
    
    # Print the text with no extra spaces and apply white color
    print(WHITE + " " * text_position + text_to_add + Style.RESET_ALL)

CONTRACT_SOURCE_CODE = '''
pragma solidity ^0.8.0;

contract SimpleStorage {
    uint256 storedData;

    constructor() {
        storedData = 100;
    }

    function set(uint256 x) public {
        storedData = x;
    }

    function get() public view returns (uint256) {
        return storedData;
    }
}
'''

def countdown_timer(seconds):
    while seconds:
        time_display = str(timedelta(seconds=seconds))
        print(f"Restarting in: {time_display}", end="\r")
        time.sleep(1)
        seconds -= 1
    print("\nStarting new cycle...")

def send_eth(account, amount):
    web3 = connect_to_web3(REDDIO_RPC_URL)

    balance_wei = web3.eth.get_balance(account.address)
    balance_eth = web3.from_wei(balance_wei, 'ether')
    print(f"Balance of {account.address}: {balance_eth} {REDDIO_COIN_NAME}")

    nonce = web3.eth.get_transaction_count(account.address)
    print(f"nonce of {account.address}: {nonce}")

    tx = {
        'nonce': nonce,
        'to': account.address,
        'value': web3.to_wei(amount, 'ether'),
        'gas': 1000000,
        'gasPrice': web3.to_wei(2.5, 'gwei')
    }

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    print(web3.to_hex(tx_hash))

    time.sleep(3)

    receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)

    txStatus = "Success" if receipt.status == 1 else "Failed"
    print(f"Transaction hash: {receipt.transactionHash.hex()} ({txStatus})")

def bridge_eth(account, amount_eth):
    print(f"Bridge {amount_eth} ETH from Sepolia to Reddio ({account.address})")

    web3 = connect_to_web3(SEPOLIA_RPC_URL)

    balance_wei = web3.eth.get_balance(account.address)
    balance_eth = web3.from_wei(balance_wei, 'ether')
    print(f"Balance of {account.address}: {balance_eth} ETH")

    nonce = web3.eth.get_transaction_count(account.address)

    contract = web3.eth.contract(address=BRIDGE_CONTRACT_ADDRESS, abi=BRIDGE_CONTRACT_ABI)

    recipient_address = account.address
    amount_in_wei = web3.to_wei(amount_eth, 'ether')
    escrow_fee = 3000000

    gas_price = round(float(web3.from_wei(web3.eth.gas_price, 'gwei')) * random_between(1.3, 1.4), 2)

    tx = contract.functions.depositETH(
        recipient_address,
        amount_in_wei,
        escrow_fee
    ).build_transaction({
        'chainId': SEPOLIA_CHAIN_ID,
        'gas': 100000,
        'gasPrice': web3.to_wei(gas_price, 'gwei'),
        'nonce': nonce,
        'value': amount_in_wei,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, private_key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)

    txStatus = "Success" if receipt.status == 1 else "Failed"
    print(f"Transaction hash: {receipt.transactionHash.hex()} ({txStatus})")

# Fungsi untuk menghasilkan nama token acak dengan menggabungkan kata sifat dan kata benda
def generate_creative_token():
    # Daftar kata sifat (adjectives)
    adjectives = [
        "Quantum", "Stellar", "Lunar", "Solar", "Crypto", "Nebula", "Galaxy", "Ether", "Cosmic", "Radiant", 
        "Celestial", "Ethereal", "Digital", "Futuristic", "Ancient", "Nova", "Atomic", "Eclipse", "Infinite", "Vortex"
    ]
    
    # Daftar kata benda (nouns)
    nouns = [
        "Chain", "Element", "Coin", "Token", "Crystal", "Verse", "Galaxy", "Universe", "Sphere", "Orbit", 
        "Network", "Link", "Foundation", "Block", "Core", "Matrix", "Circuit", "Realm", "Force", "Core", "System"
    ]
    
    # Pilih kata sifat dan kata benda acak dan gabungkan untuk membuat nama token
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    
    # Gabungkan keduanya untuk menghasilkan nama token yang unik
    name = f"{adjective} {noun}"
    
    # Ganti spasi dengan garis bawah agar nama kontrak valid di Solidity
    contract_name = name.replace(" ", "_")

    # Generate simbol acak berdasarkan nama token
    symbol = generate_symbol(name)
    
    return contract_name, name, symbol

# Fungsi untuk menghasilkan simbol token berdasarkan nama token
def generate_symbol(name):
    words = name.split()
    # Ambil huruf pertama dari setiap kata dan buat simbolnya lebih dinamis
    symbol = ''.join([word[0] for word in words]).upper()
    
    # Tambahkan beberapa huruf acak dari kata-kata token
    for word in words:
        symbol += random.choice(word[1:3]).upper()  # Ambil beberapa huruf dari kata token   
    
    return symbol

# Fungsi untuk menghasilkan initial supply acak (antara 1 juta sampai 1 miliar)
def generate_initial_supply():
    return random.randint(1000000, 1000000000)

# Perbarui fungsi deploy_contract agar nama, simbol, dan supply acak digunakan
def deploy_contract(account):
    web3 = connect_to_web3(REDDIO_RPC_URL)
    try:
        # Generate nama dan simbol token acak
        contract_name, token_name, symbol = generate_creative_token()

        # Generate initial supply acak antara 1 juta sampai 1 miliar
        initial_supply = generate_initial_supply()

        # Kontrak ERC-20 yang sudah dimodifikasi
        updated_contract_code = f'''
        pragma solidity ^0.8.0;

        interface IERC20 {{
            function totalSupply() external view returns (uint256);
            function balanceOf(address account) external view returns (uint256);
            function transfer(address recipient, uint256 amount) external returns (bool);
            function allowance(address owner, address spender) external view returns (uint256);
            function approve(address spender, uint256 amount) external returns (bool);
            function transferFrom(address sender, address recipient, uint256 amount) external returns (bool);

            event Transfer(address indexed from, address indexed to, uint256 value);
            event Approval(address indexed owner, address indexed spender, uint256 value);
        }}

        contract {contract_name} is IERC20 {{
            string public name = "{token_name}";
            string public symbol = "{symbol}";
            uint8 public decimals = 18;
            uint256 private _totalSupply;
            mapping(address => uint256) private _balances;
            mapping(address => mapping(address => uint256)) private _allowances;

            constructor(uint256 initialSupply) {{
                _totalSupply = initialSupply * (10 ** uint256(decimals)); // supply adjusted by decimals
                _balances[msg.sender] = _totalSupply; // Assign the total supply to the contract creator
                emit Transfer(address(0), msg.sender, _totalSupply);
            }}

            function totalSupply() public view override returns (uint256) {{
                return _totalSupply;
            }}

            function balanceOf(address account) public view override returns (uint256) {{
                return _balances[account];
            }}

            function transfer(address recipient, uint256 amount) public override returns (bool) {{
                require(recipient != address(0), "ERC20: transfer to the zero address");
                require(_balances[msg.sender] >= amount, "ERC20: transfer amount exceeds balance");

                _balances[msg.sender] -= amount;
                _balances[recipient] += amount;

                emit Transfer(msg.sender, recipient, amount);
                return true;
            }}

            function allowance(address owner, address spender) public view override returns (uint256) {{
                return _allowances[owner][spender];
            }}

            function approve(address spender, uint256 amount) public override returns (bool) {{
                _allowances[msg.sender][spender] = amount;
                emit Approval(msg.sender, spender, amount);
                return true;
            }}

            function transferFrom(address sender, address recipient, uint256 amount) public override returns (bool) {{
                require(sender != address(0), "ERC20: transfer from the zero address");
                require(recipient != address(0), "ERC20: transfer to the zero address");
                require(_balances[sender] >= amount, "ERC20: transfer amount exceeds balance");
                require(_allowances[sender][msg.sender] >= amount, "ERC20: transfer amount exceeds allowance");

                _balances[sender] -= amount;
                _balances[recipient] += amount;
                _allowances[sender][msg.sender] -= amount;

                emit Transfer(sender, recipient, amount);
                return true;
            }}
        }}
        '''

        # Compile the updated contract source code
        compiled_sol = compile_source(updated_contract_code)
        contract_interface = compiled_sol[f'<stdin>:{contract_name}']
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']

        # Prepare the contract instance
        TokenContract = web3.eth.contract(abi=abi, bytecode=bytecode)

        # Get gas estimate
        gas_estimate = TokenContract.constructor(initial_supply).estimate_gas({'from': account.address})
        print(f"Gas estimate for {token_name} ({symbol}) deployment: {gas_estimate}")

        # Build the transaction
        transaction = TokenContract.constructor(initial_supply).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': gas_estimate + 10000,  # Adding a buffer to the gas estimate
            'gasPrice': web3.eth.gas_price,
        })

        # Sign the transaction
        signed_tx = web3.eth.account.sign_transaction(transaction, account.key)

        # Send the transaction
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        print(f"Deployment transaction for {token_name} sent. Hash: {web3.to_hex(tx_hash)}")

        # Wait for the receipt
        receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)
        print(f"{token_name} contract deployed at: {receipt.contractAddress}")
    except Exception as e:
        print(f"Failed to deploy contract: {str(e)}")

if __name__ == "__main__":
    # Pastikan untuk menampilkan ASCII art terlebih dahulu
    print_red_white_ascii_art()

    # Lanjutkan dengan eksekusi kode lainnya
    web3 = connect_to_web3(REDDIO_RPC_URL)

    with open('data/private_keys.txt') as f:
        private_keys = f.readlines()

    private_keys = [x.strip() for x in private_keys]
    
    while True:
        for i, private_key in enumerate(private_keys):
            print(f"================================================================================\n")
            account = get_account(web3, private_key)
            send_amount = random_between(0.0001, 0.001)
            print(f"Sending {send_amount} RED to {account.address}")
            send_eth(account, send_amount)
            bridge_amount = random_between(0.0001, 0.0009)
            bridge_eth(account, bridge_amount)

            # Deploy contract
            print(f"Deploying contract for {account.address}")
            deploy_contract(account)

            print(f"================================================================================\n")

        # Generate random delay between 24 to 24,1 hours
        delay_seconds = random_between(86400, 86777)  # 24 hour (86400) to 24,1 hours (86777s)
        countdown_timer(int(delay_seconds))