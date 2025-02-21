
# Reddio Automation Script

## English

This Python script automates tasks for Reddio, including Ethereum bridging, deploying ERC-20 contracts, and handling random token generation. It supports automated retries, gas estimation, and creative token names.

### Features  
- Displays account balance and nonce before transactions  
- Logs auto-claim points after completing transactions  
- Automates Claim Points  
- Automates ETH bridging to Reddio  
- Generates unique token names and deploys ERC-20 contracts  
- Randomized operations for enhanced security  
- Customizable retry mechanisms for reliable transactions  
- Improved readability of transaction logs  

### Prerequisites
- Python 3.x
- Required libraries (install via `pip install -r requirements.txt`):
  - `web3`
  - `solcx`
  - `colorama`
  - `eth-abi`
  - `requests`
  - `aiohttp`
  - `parsimonious`

### How to Use
1. Clone the repository and navigate to the directory:
   ```bash
   git clone https://github.com/0xsyo/reddio.git
   cd reddio
   ```

2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure `data/private_keys.txt` with private keys, one per line.

4. Run the script:
   ```bash
   python main.py
   ```

---

## Bahasa Indonesia

Script Python ini mengotomatisasi tugas-tugas untuk Reddio, termasuk bridging Ethereum, deploy kontrak ERC-20, dan pembuatan token acak. Script ini mendukung mekanisme retry otomatis, estimasi gas, dan nama token kreatif.

### Fitur
- Mengotomatisasi bridging ETH ke Reddio.
- Menghasilkan nama token unik dan mendistribusikan kontrak ERC-20.
- Operasi acak untuk keamanan tambahan.
- Mekanisme retry yang dapat dikustomisasi untuk transaksi yang andal.

### Prasyarat
- Python 3.x
- Library yang dibutuhkan (install dengan `pip install -r requirements.txt`):
  - `web3`
  - `solcx`
  - `colorama`
  - `datetime`

### Cara Menggunakan
1. Clone repository dan buka direktori:
   ```bash
   git clone git clone https://github.com/0xsyo/reddio.git
   cd reddio
   ```

2. Install dependencies yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```

3. Konfigurasikan `data/private_keys.txt` dengan private key, satu per baris.

4. Jalankan script:
   ```bash
   python main.py
   ```
