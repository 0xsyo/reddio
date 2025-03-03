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

# Konfigurasi untuk auto-claim tasks
BASE_URL = "https://points-mainnet.reddio.com/v1"
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "id-ID,id;q=0.5",
    "content-type": "application/json",
    "origin": "https://points.reddio.com",
    "priority": "u=1, i",
    "referer": "https://points.reddio.com/",
    "sec-ch-ua": '"Not(A:Brand";v="99", "Brave";v="133", "Chromium";v="133"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36"
}
TASKS = {
    "c2cf2c1d-cb46-406d-b025-dd6a00369215": "Complete one Testnet transfer on your wallet",
    "c2cf2c1d-cb46-406d-b025-dd6a00369216": "Execute one Bridge transaction"
}

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
    print(Fore.LIGHTYELLOW_EX + "\nPlease wait...\n")
    time.sleep(2)
    os.system("clear" if os.name == "posix" else "cls")
    for i, char in enumerate(banner):
        print(colors[i % len(colors)] + char, end="")
    print(Fore.LIGHTYELLOW_EX + "\n")

def countdown_timer(seconds):
    while seconds:
        time_display = str(timedelta(seconds=seconds))
        print(f"✅ {Fore.CYAN}Restarting in: {time_display}", end="\r")
        time.sleep(1)
        seconds -= 1
    print("\nStarting new cycle...")

def send_eth(account, amount):
    web3 = connect_to_web3(REDDIO_RPC_URL)

    balance_wei = web3.eth.get_balance(account.address)
    balance_eth = web3.from_wei(balance_wei, 'ether')
    print(f"✅ {Fore.GREEN}Balance of {account.address}: {balance_eth} {REDDIO_COIN_NAME}")

    nonce = web3.eth.get_transaction_count(account.address)
    print(f"✅ {Fore.GREEN}Nonce of {account.address}: {nonce}")

    tx = {
        'nonce': nonce,
        'to': account.address,
        'value': web3.to_wei(amount, 'ether'),
        'gas': 1000000,
        'gasPrice': web3.to_wei(2.5, 'gwei')
    }

    signed_tx = web3.eth.account.sign_transaction(tx, account.key)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)

    tx_hash_link = f"https://reddio-devnet.l2scan.co/tx/{web3.to_hex(tx_hash)}"
    print(f"✅ {Fore.CYAN}Transaction hash: {tx_hash_link}")

    time.sleep(3)

    receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)

    txStatus = "Success" if receipt.status == 1 else "Failed"
    print(f"✅ {Fore.CYAN}Transaction hash: {receipt.transactionHash.hex()} ({txStatus})")

def bridge_eth(account, amount_eth):
    web3 = connect_to_web3(SEPOLIA_RPC_URL)

    balance_wei = web3.eth.get_balance(account.address)
    balance_eth = web3.from_wei(balance_wei, 'ether')
    print(f"✅ {Fore.MAGENTA}Balance of {account.address}: {balance_eth} ETH")

    if balance_eth < amount_eth:
        print(f"{Fore.RED}Insufficient funds for bridging. Skipping account {account.address}.")
        return

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

    signed_tx = web3.eth.account.sign_transaction(tx, account.key)
    try:
        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_link = f"https://sepolia.etherscan.io/tx/{web3.to_hex(tx_hash)}"
        print(f"✅ {Fore.CYAN}Transaction hash: {tx_hash_link}")

        receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)

        txStatus = "Success" if receipt.status == 1 else "Failed"
        print(f"✅ {Fore.CYAN}Transaction hash: {receipt.transactionHash.hex()} ({txStatus})")
    except Exception as e:
        print(f"❌ {Fore.RED}Failed to bridge ETH for account {account.address}: {str(e)}")

def deploy_contract(account):
    web3 = connect_to_web3(REDDIO_RPC_URL)
    try:
        contract_name, token_name, symbol = generate_creative_token()

        initial_supply = generate_initial_supply()

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
        print(f"✅ {Fore.YELLOW}Gas estimate for {token_name} ({symbol}) deployment: {gas_estimate}")

        transaction = TokenContract.constructor(initial_supply).build_transaction({
            'from': account.address,
            'nonce': web3.eth.get_transaction_count(account.address),
            'gas': gas_estimate + 10000,
            'gasPrice': web3.eth.gas_price,
        })

        signed_tx = web3.eth.account.sign_transaction(transaction, account.key)

        tx_hash = web3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_hash_link = f"https://reddio-devnet.l2scan.co/tx/{web3.to_hex(tx_hash)}"
        print(f"✅ {Fore.CYAN}Deployment transaction for {token_name} sent. Hash: {tx_hash_link}")

        receipt = retry(lambda: web3.eth.wait_for_transaction_receipt(tx_hash, timeout=120), max_retries=5, wait_time=2)
        print(f"✅ {Fore.GREEN}{token_name} contract deployed at: {receipt.contractAddress}")
    except Exception as e:
        print(f"❌ {Fore.RED}Failed to deploy contract: {str(e)}")

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
        data = response.json().get("data", {})
        print(Fore.GREEN + f"✅ Informasi akun {wallet_address}:" + Style.RESET_ALL)
        print(f"✅ Points: {data.get('points', 'N/A')}")
        print(f"✅ Task Points: {data.get('task_points', 'N/A')}")
        print(f"✅ Discord Username: {data.get('discord_username', 'N/A')}")
        print(f"✅ Twitter Handle: {data.get('twitter_handle', 'N/A')}")
        print(f"✅ Devnet Daily Bridged: {data.get('devnet_daily_bridged', 'N/A')}")
        print(f"✅ Devnet Daily Transferred: {data.get('devnet_daily_transferred', 'N/A')}")
        return data
    except requests.exceptions.RequestException as e:
        print(Fore.RED + f"❌ Failed to retrieve account information {wallet_address}: " + Style.RESET_ALL)
        print(response.text)
        return None

def verify_task(wallet_address, task_id, task_name):
    url = f"{BASE_URL}/points/verify"
    payload = {"wallet_address": wallet_address, "task_uuid": task_id}
    
    try:
        print(Fore.YELLOW + f"🔄 Verifying task: {task_name}..." + Style.RESET_ALL)
        response = requests.post(url, json=payload, headers=HEADERS)
        response.raise_for_status()
        print(Fore.GREEN + f"✅ Task {task_name} successfully verified for {wallet_address}" + Style.RESET_ALL)
        return True
    except requests.exceptions.RequestException as e:
        if "Already verified today" in response.text:
            print(Fore.YELLOW + f"ℹ️ Task {task_name} it was verified today." + Style.RESET_ALL)
            return True
        else:
            print(Fore.RED + f"❌ Task verification failed {task_name} for {wallet_address}: " + Style.RESET_ALL)
            print(response.text)
            return False

def auto_claim_tasks(wallet_address):
    account_info = fetch_account_info(wallet_address)
    if not account_info:
        return

    for task_id, task_name in TASKS.items():
        print(Fore.CYAN + f"🔄 Processing tasks: {task_name}..." + Style.RESET_ALL)
        if verify_task(wallet_address, task_id, task_name):
            print(Fore.GREEN + f"✅ Task {task_name} completed successfully!" + Style.RESET_ALL)
        else:
            print(Fore.RED + f"⚠️ Failed to process task {task_name}." + Style.RESET_ALL)

if __name__ == "__main__":
    rainbow_banner()

    deploy_choice = input(f"🛠 {Fore.CYAN}Do you want to deploy a token? (y/n): ").strip().lower()
    deploy_contract_flag = deploy_choice == 'y'

    web3 = connect_to_web3(REDDIO_RPC_URL)

    with open('data/private_keys.txt') as f:
        private_keys = f.readlines()

    private_keys = [x.strip() for x in private_keys]
    
    while True:
        for i, private_key in enumerate(private_keys):
            account = get_account(web3, private_key)
            send_amount = random_between(0.0001, 0.001)
            wallet_link = f"https://reddio-devnet.l2scan.co/address/{account.address}"
            print(f"✅ {Fore.CYAN}Sending {send_amount} RED to {wallet_link}")
            send_eth(account, send_amount)
            bridge_amount = random_between(0.0001, 0.0009)
            print(f"✅ {Fore.CYAN}Bridging {bridge_amount} ETH from Sepolia to Reddio ({wallet_link})")
            bridge_eth(account, bridge_amount)

            if deploy_contract_flag:
                print(f"✅ {Fore.CYAN}Deploying contract for {wallet_link}")
                deploy_contract(account)

            # Jalankan auto-claim tasks setelah semua proses selesai
            print(f"✅ {Fore.CYAN}Starting auto-claim tasks for {wallet_link}")
            auto_claim_tasks(account.address)

            print(f"{Fore.CYAN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")

        delay_seconds = random_between(21600, 25200)
        countdown_timer(int(delay_seconds))
