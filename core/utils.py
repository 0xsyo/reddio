import random
import time
from web3 import Web3

def random_between(min, max):
    delta = (max - min) * (random.random() % 10)
    return round(min + delta , 4)

def connect_to_web3(rpc_url):
    web3 = Web3(Web3.HTTPProvider(rpc_url))
    return web3

def get_account(web3, private_key):
    account = web3.eth.account.from_key(private_key)
    return account

def get_nonce(web3, address):
    return web3.eth.get_transaction_count(address)


def retry(lambda_func, max_retries=3, wait_time=2):
    for attempt in range(1, max_retries + 1):
        try:
            return lambda_func()
        except Exception as e:
            print(f"Attempt {attempt} failed: {e}")
            if attempt < max_retries:
                time.sleep(wait_time)
            else:
                print("All retries failed.")
                raise