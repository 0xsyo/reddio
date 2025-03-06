import time
import random
import os
from datetime import timedelta
from core.config import (BRIDGE_CONTRACT_ABI, BRIDGE_CONTRACT_ADDRESS, REDDIO_RPC_URL, 
                         REDDIO_COIN_NAME, SEPOLIA_CHAIN_ID, SEPOLIA_RPC_URL)
from core.utils import connect_to_web3, get_account, random_between, retry
from solcx import install_solc, set_solc_version, compile_source
from colorama import Fore, Style, init
import requests

# Install Solidity Compiler
install_solc('0.8.0')
set_solc_version('0.8.0')

# Initialize colorama for terminal color support
init(autoreset=True)

# Configuration for auto-claim tasks
BASE_URL = "https://points-mainnet.reddio.com/v1"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:115.0) Gecko/20100101 Firefox/115.0",
    "referer": "https://points.reddio.com/",
    "origin": "https://points.reddio.com"
}

TASKS = {
    "c2cf2c1d-cb46-406d-b025-dd6a00369215": "Complete one Testnet transfer on your wallet",
    "c2cf2c1d-cb46-406d-b025-dd6a00369216": "Execute one Bridge transaction"
}

# Define log prefixes for different message types
LOG_INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
LOG_SUCCESS = f"{Fore.GREEN}[SUCCESS]{Style.RESET_ALL}"
LOG_WARNING = f"{Fore.YELLOW}[WARNING]{Style.RESET_ALL}"
LOG_ERROR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
LOG_ACTION = f"{Fore.MAGENTA}[ACTION]{Style.RESET_ALL}"
LOG_STATUS = f"{Fore.BLUE}[STATUS]{Style.RESET_ALL}"

# Horizontal line for section separation
SEPARATOR = f"{Fore.CYAN}{'━' * 80}{Style.RESET_ALL}"

def log_info(message):
    print(f"{LOG_INFO} {message}")

def log_success(message):
    print(f"{LOG_SUCCESS} {message}")

def log_warning(message):
    print(f"{LOG_WARNING} {message}")

def log_error(message):
    print(f"{LOG_ERROR} {message}")
    
def log_action(message):
    print(f"{LOG_ACTION} {message}")
    
def log_status(message):
    print(f"{LOG_STATUS} {message}")

def print_separator():
    print(f"\n{SEPARATOR}\n")

def rainbow_banner():
    os.system("clear" if os.name == "posix" else "cls")
    colors = [Fore.RED, Fore.YELLOW, Fore.GREEN, Fore.CYAN, Fore.BLUE, Fore.MAGENTA]
    banner = """
  _______                          
 |     __|.--.--.---.-.-----.---.-.
 |__     ||  |  |  _  |-- __|  _  |
 |_______||___  |___._|_____|___._|
          |_____|                   
    """
    
    for i, char in enumerate(banner):
        print(colors[i % len(colors)] + char, end="")
        time.sleep(0.007)
    print(f"\n{LOG_INFO} Please wait...\n")
    time.sleep(2)
    os.system("clear" if os.name == "posix" else "cls")
    for i, char in enumerate(banner):
        print(colors[i % len(colors)] + char, end="")
    print("\n")

def countdown_timer(seconds):
    while seconds:
        time_display = str(timedelta(seconds=seconds))
        print(f"{LOG_INFO} Restarting in: {time_display}", end="\r")
        time.sleep(1)
        seconds -= 1
    log_info("Starting new cycle...")

def send_eth(account, amount):
    web3 = connect_to_web3(REDDIO_RPC_URL)

    balance_wei = web3.eth.get_balance(account.address)
    balance_eth = web3.fromWei(balance_wei, 'ether')
    log_success(f"Balance of {account.address}: {balance_eth} {REDDIO_COIN_NAME}")

    nonce = web3.eth.get_transaction_count(account.address)
    log_info(f"Nonce of {account.address}: {nonce}")

    tx = {
        'nonce': nonce,
        'to': account.address,
        'value': web3.toWei(amount, 'ether'),
        'gas': 1000000,
        'gasPrice': web3.toWei(2.5, 'gwei')
    }

    signed_tx = web3.eth.account.sign_transaction(tx, account.key)
    tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)

    tx_hash_link = f"https://reddio-devnet.l2scan.co/tx/{web3.toHex(tx_hash)}"
    log_info(f"Transaction submitted: {tx_hash_link}")

    time.sleep(3)

    receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)

    txStatus = "Success" if receipt.status == 1 else "Failed"
    log_success(f"Transaction completed: {receipt.transactionHash.hex()} ({txStatus})")

def bridge_eth(account, amount_eth):
    web3 = connect_to_web3(SEPOLIA_RPC_URL)

    balance_wei = web3.eth.get_balance(account.address)
    balance_eth = web3.fromWei(balance_wei, 'ether')
    log_success(f"Balance of {account.address}: {balance_eth} ETH")

    if balance_eth < amount_eth:
        log_error(f"Insufficient funds for bridging. Skipping account {account.address}.")
        return

    nonce = web3.eth.get_transaction_count(account.address)

    contract = web3.eth.contract(address=BRIDGE_CONTRACT_ADDRESS, abi=BRIDGE_CONTRACT_ABI)

    recipient_address = account.address
    amount_in_wei = web3.toWei(amount_eth, 'ether')
    escrow_fee = 3000000

    gas_price = round(float(web3.fromWei(web3.eth.gas_price, 'gwei')) * random_between(1.3, 1.4), 2)

    tx = contract.functions.depositETH(
        recipient_address,
        amount_in_wei,
        escrow_fee
    ).build_transaction({
        'chainId': SEPOLIA_CHAIN_ID,
        'gas': 100000,
        'gasPrice': web3.toWei(gas_price, 'gwei'),
        'nonce': nonce,
        'value': amount_in_wei,
    })

    signed_tx = web3.eth.account.sign_transaction(tx, account.key)
    try:
        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_hash_link = f"https://sepolia.etherscan.io/tx/{web3.toHex(tx_hash)}"
        log_info(f"Bridge transaction submitted: {tx_hash_link}")

        receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)

        txStatus = "Success" if receipt.status == 1 else "Failed"
        log_success(f"Bridge transaction completed: {receipt.transactionHash.hex()} ({txStatus})")
    except Exception as e:
        log_error(f"Failed to bridge ETH for account {account.address}: {str(e)}")

def deploy_contract(account):
    web3 = connect_to_web3(REDDIO_RPC_URL)
    try:
        contract_name, token_name, symbol = generate_creative_token()

        initial_supply = generate_initial_supply()
        log_info(f"Preparing to deploy {token_name} ({symbol}) with initial supply of {initial_supply}")

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
                _totalSupply = initialSupply * (10 ** uint256(decimals)); 
                _balances[msg.sender] = _totalSupply;
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

        compiled_sol = compile_source(updated_contract_code)
        contract_interface = compiled_sol[f'<stdin>:{contract_name}']
        abi = contract_interface['abi']
        bytecode = contract_interface['bin']

        TokenContract = web3.eth.contract(abi=abi, bytecode=bytecode)

        gas_estimate = TokenContract.constructor(initial_supply).estimate_gas({'from': account.address})
        log_info(f"Gas estimate for {token_name} ({symbol}) deployment: {gas_estimate}")

        transaction = TokenContract.constructor(initial_supply).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': gas_estimate + 10000,
            'gasPrice': web3.eth.gas_price,
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, account.key)

        tx_hash = web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_hash_link = f"https://reddio-devnet.l2scan.co/tx/{web3.toHex(tx_hash)}"
        log_info(f"Deployment transaction for {token_name} sent: {tx_hash_link}")

        receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)
        log_success(f"{token_name} contract deployed at: {receipt.contractAddress}")
    except Exception as e:
        log_error(f"Failed to deploy contract: {str(e)}")

def generate_creative_token():
    adjectives = [
        "Quantum", "Stellar", "Lunar", "Solar", "Crypto", "Nebula", "Galaxy", "Ether", "Cosmic", "Radiant", 
        "Celestial", "Ethereal", "Digital", "Futuristic", "Ancient", "Nova", "Atomic", "Eclipse", "Infinite", "Vortex",
        "Decentralized", "Immutable", "Transparent", "Trustless", "Encrypted", "Dynamic", "Lightning", "Hybrid", 
        "Pioneering", "NextGen", "Scalable", "Adaptive", "Synthetic", "Metaverse", "Defi", "Programmable", 
        "Autonomous", "Layered", "Hyper", "Spectral", "Interstellar"
    ]
    
    nouns = [
        "Chain", "Element", "Coin", "Token", "Crystal", "Verse", "Galaxy", "Universe", "Sphere", "Orbit", 
        "Network", "Link", "Foundation", "Block", "Core", "Matrix", "Circuit", "Realm", "Force", "Core", "System",
        "Protocol", "Ledger", "Node", "Wallet", "Stake", "Mining", "Contract", "Layer", "Liquidity", "Consensus",
        "Governance", "Bridge", "Oracle", "Ecosystem", "Hash", "Nonce", "Validator", "Beacon", "Cluster", 
        "Sharding", "Dapp", "SmartContract", "Gateway"
    ]
    
    adjective = random.choice(adjectives)
    noun = random.choice(nouns)
    
    name = f"{adjective} {noun}"
    
    contract_name = name.replace(" ", "_")

    symbol = generate_symbol(name)
    
    return contract_name, name, symbol

def generate_symbol(name):
    words = name.split()
    symbol = ''.join([word[0] for word in words]).upper()
    
    for word in words:
        symbol += random.choice(word[1:3]).upper()   
    
    return symbol

def generate_initial_supply():
    return random.randint(1000000, 1000000000)

def fetch_account_info(wallet_address):
    url = f"{BASE_URL}/userinfo?wallet_address={wallet_address}"
    
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        
        try:
            data = response.json()
        except ValueError:
            log_error(f"Invalid JSON response from API for {wallet_address}")
            log_error(f"Response content: {response.text}")
            return None

        account_data = data.get("data", {})
        log_info(f"Account information for {wallet_address}:")
        print(f"  {LOG_STATUS} Points: {account_data.get('points', 'N/A')}")
        print(f"  {LOG_STATUS} Task Points: {account_data.get('task_points', 'N/A')}")
        print(f"  {LOG_STATUS} Discord Username: {account_data.get('discord_username', 'N/A')}")
        print(f"  {LOG_STATUS} Twitter Handle: {account_data.get('twitter_handle', 'N/A')}")
        print(f"  {LOG_STATUS} Devnet Daily Bridged: {account_data.get('devnet_daily_bridged', 'N/A')}")
        print(f"  {LOG_STATUS} Devnet Daily Transferred: {account_data.get('devnet_daily_transferred', 'N/A')}")
        return account_data
    except requests.exceptions.RequestException as e:
        log_error(f"Failed to retrieve account information for {wallet_address}")
        log_error(f"Error details: {str(e)}")
        return None


def verify_task(wallet_address, task_id, task_name):
    url = f"{BASE_URL}/points/verify"
    payload = {"wallet_address": wallet_address, "task_uuid": task_id}
    
    try:
        log_action(f"Verifying task: {task_name}...")
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        log_success(f"Task '{task_name}' successfully verified for {wallet_address}")
        return True
    except requests.exceptions.RequestException as e:
        if "Already verified today" in response.text:
            log_warning(f"Task '{task_name}' was already verified today")
            return True
        else:
            log_error(f"Task verification failed for '{task_name}' (wallet: {wallet_address})")
            log_error(f"Response: {response.text}")
            return False

def auto_claim_tasks(wallet_address):
    log_action(f"Starting auto-claim process for {wallet_address}")
    account_info = fetch_account_info(wallet_address)
    if not account_info:
        log_error("Failed to retrieve account information, skipping task claims")
        return

    for task_id, task_name in TASKS.items():
        log_action(f"Processing task: {task_name}")
        if verify_task(wallet_address, task_id, task_name):
            log_success(f"Task '{task_name}' completed successfully!")
        else:
            log_error(f"Failed to process task '{task_name}'")

if __name__ == "__main__":
    rainbow_banner()

    deploy_choice = input(f"{LOG_ACTION} Do you want to deploy a token? (y/n): ").strip().lower()
    deploy_contract_flag = deploy_choice == 'y'

    web3 = connect_to_web3(REDDIO_RPC_URL)

    with open('data/private_keys.txt') as f:
        private_keys = f.readlines()

    private_keys = [x.strip() for x in private_keys]
    
    while True:
        for i, private_key in enumerate(private_keys):
            account = get_account(web3, private_key)
            wallet_link = f"https://reddio-devnet.l2scan.co/address/{account.address}"
            
            print_separator()
            log_action(f"Processing wallet ({i+1}/{len(private_keys)}): {account.address}")
            print(f"  {LOG_INFO} Explorer: {wallet_link}")
            
            # Send transaction
            send_amount = random_between(0.0001, 0.001)
            log_action(f"Sending {send_amount} RED to self")
            send_eth(account, send_amount)
            
            # Bridge transaction
            bridge_amount = random_between(0.0001, 0.0009)
            log_action(f"Bridging {bridge_amount} ETH from Sepolia to Reddio")
            bridge_eth(account, bridge_amount)

            # Deploy contract if needed
            if deploy_contract_flag:
                log_action(f"Deploying contract")
                deploy_contract(account)

            # Run auto-claim tasks
            log_action(f"Starting auto-claim tasks")
            auto_claim_tasks(account.address)
            
            log_success(f"All operations completed for wallet {account.address}")
            print_separator()

        # Wait before next cycle
        delay_seconds = random_between(21600, 25200)
        countdown_timer(int(delay_seconds))
