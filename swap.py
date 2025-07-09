#!/usr/bin/env python3
import os
import time
from datetime import datetime
from web3 import Web3
from dotenv import load_dotenv
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, BarColumn, TextColumn, TimeRemainingColumn
from rich.table import Table
from rich import box
from rich.style import Style
from rich.text import Text

# Inisialisasi rich console
console = Console()

# Perbaikan tema warna - format yang benar
THEME = {
    "primary": "bold cyan",
    "secondary": "blue",
    "success": "bold green",
    "warning": "bold yellow",
    "error": "bold red",
    "info": "cyan",
    "accent": "magenta",
    "dark": "black",
    "light": "white"
}

# Banner aplikasi
def show_banner():
    console.print(Panel(
        Text("Injective Automation BOT", justify="center", style=THEME["accent"]),
        Text("Allowindo VIP Edition", justify="center", style=THEME["secondary"]),
        box=box.ROUNDED,
        style=Style(color=THEME["primary"], bgcolor=THEME["dark"]),
        width=80,
        padding=(1, 2),
        title="[bold]🚀 CRYPTO SWAP BOT[/bold]",
        subtitle=f"[{THEME['info']}]{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    ))

# Logger dengan rich - format warna diperbaiki
class Logger:
    @staticmethod
    def info(msg):
        console.print(f"[{THEME['primary']}]•[/] {msg}")
    
    @staticmethod
    def warn(msg):
        console.print(f"[{THEME['warning']}][!][/] [bold]{THEME['warning']}Warning:[/] {msg}")
    
    @staticmethod
    def error(msg):
        console.print(f"[{THEME['error']}][✗][/] [bold]{THEME['error']}Error:[/] {msg}")
    
    @staticmethod
    def success(msg):
        console.print(f"[{THEME['success']}][✓][/] [bold]{THEME['success']}Success:[/] {msg}")
    
    @staticmethod
    def loading(msg):
        console.print(f"[{THEME['info']}][⟳][/] {THEME['info']}{msg}")
    
    @staticmethod
    def step(msg):
        console.print(f"[{THEME['accent']}][→][/] [bold]{msg}[/bold]")
    
    @staticmethod
    def transaction_status(hash, status, tx_num=None):
        if status == "pending":
            style = THEME["warning"]
            icon = "⏳"
        elif status == "success":
            style = THEME["success"]
            icon = "✅"
        else:
            style = THEME["error"]
            icon = "❌"
        
        tx_text = f" [dim](TX {tx_num})[/dim]" if tx_num else ""
        console.print(
            f"[{style}]{icon} [bold]Transaction:[/bold] [link=https://testnet.blockscout.injective.network/tx/{hash}]{hash[:12]}...[/link]{tx_text}"
        )

# Konfigurasi jaringan
RPC_URL = 'https://k8s.testnet.json-rpc.injective.network'
ROUTER_ADDRESS = '0x4069f8Ada1a4d3B705e6a82F9A3EB8624Cd4Cb1E'
WINJ_ADDRESS = '0xe1c64DDE0A990ac2435B05DCdac869a17fE06Bd2'
PMX_ADDRESS = '0xeD0094eE59492cB08A5602Eb8275acb00FFb627d'
PAIR_ADDRESS = '0x54Ba382CED996738c2A0793247F66dE86C441987'

# ABI kontrak
ROUTER_ABI = [
    {
        "name": "swapExactTokensForTokens",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {"name": "amountOutMin", "type": "uint256"},
            {
                "name": "routes",
                "type": "tuple[]",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "stable", "type": "bool"}
                ]
            },
            {"name": "to", "type": "address"},
            {"name": "deadline", "type": "uint256"}
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}]
    },
    {
        "name": "getAmountsOut",
        "type": "function",
        "inputs": [
            {"name": "amountIn", "type": "uint256"},
            {
                "name": "routes",
                "type": "tuple[]",
                "components": [
                    {"name": "tokenIn", "type": "address"},
                    {"name": "tokenOut", "type": "address"},
                    {"name": "stable", "type": "bool"}
                ]
            }
        ],
        "outputs": [{"name": "amounts", "type": "uint256[]"}],
        "stateMutability": "view"
    }
]

ERC20_ABI = [
    {
        "name": "approve",
        "type": "function",
        "inputs": [
            {"name": "spender", "type": "address"},
            {"name": "amount", "type": "uint256"}
        ],
        "outputs": [{"name": "", "type": "bool"}]
    },
    {
        "name": "allowance",
        "type": "function",
        "inputs": [
            {"name": "owner", "type": "address"},
            {"name": "spender", "type": "address"}
        ],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    },
    {
        "name": "balanceOf",
        "type": "function",
        "inputs": [{"name": "account", "type": "address"}],
        "outputs": [{"name": "", "type": "uint256"}],
        "stateMutability": "view"
    }
]

PAIR_ABI = [
    {
        "anonymous": False,
        "inputs": [
            {"indexed": True, "name": "sender", "type": "address"},
            {"indexed": False, "name": "amount0In", "type": "uint256"},
            {"indexed": False, "name": "amount1In", "type": "uint256"},
            {"indexed": False, "name": "amount0Out", "type": "uint256"},
            {"indexed": False, "name": "amount1Out", "type": "uint256"},
            {"indexed": True, "name": "to", "type": "address"}
        ],
        "name": "Swap",
        "type": "event"
    }
]

# Inisialisasi Web3
def init_web3():
    Logger.loading("Menghubungkan ke jaringan Injective...")
    w3 = Web3(Web3.HTTPProvider(RPC_URL))
    if not w3.is_connected():
        Logger.error("Gagal terhubung ke RPC Injective")
        exit(1)
    Logger.success(f"Terhubung ke Injective Testnet (Chain ID: {w3.eth.chain_id})")
    return w3

# Load environment variables
def load_private_keys():
    load_dotenv()
    private_keys = [v for k, v in os.environ.items() if k.startswith('PRIVATE_KEY_')]

    if not private_keys:
        Logger.error("Tidak ada private key yang ditemukan di file .env")
        exit(1)
    
    Logger.success(f"Loaded {len(private_keys)} wallet")
    return private_keys

def create_wallet_table(w3, wallets):
    table = Table(show_header=True, header_style=f"bold {THEME['primary']}", box=box.ROUNDED)
    table.add_column("#", style="dim", width=4)
    table.add_column("Address", min_width=20)
    table.add_column("Balance", justify="right")
    
    for i, pk in enumerate(wallets, 1):
        wallet = w3.eth.account.from_key(pk)
        balance = w3.eth.get_balance(wallet.address)
        table.add_row(
            str(i),
            wallet.address,
            f"{w3.from_wei(balance, 'ether'):.6f} INJ"
        )
    
    return table

def approve_token(w3, wallet, token_address, spender, amount):
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    allowance = token_contract.functions.allowance(wallet.address, spender).call()
    
    if allowance < amount:
        Logger.step(f"Meng-approve {w3.from_wei(amount, 'ether'):.6f} token")
        tx = token_contract.functions.approve(spender, amount).build_transaction({
            'from': wallet.address,
            'nonce': w3.eth.get_transaction_count(wallet.address),
            'gas': 200000,
            'gasPrice': w3.eth.gas_price
        })
        
        signed_tx = wallet.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TimeRemainingColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Menunggu konfirmasi...", total=1)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            progress.update(task, advance=1)
        
        if receipt.status == 1:
            Logger.success(f"Approval berhasil")
        else:
            raise Exception(f"Transaksi approval gagal")
    else:
        Logger.info(f"Allowance sudah cukup")

def get_expected_output(w3, amount_in, token_in, token_out):
    router_contract = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
    routes = [(
        token_in,
        token_out,
        False
    )]
    amounts_out = router_contract.functions.getAmountsOut(amount_in, routes).call()
    return amounts_out[1]

def swap_tokens(w3, wallet, amount_in, token_in, token_out, tx_num):
    router_contract = w3.eth.contract(address=ROUTER_ADDRESS, abi=ROUTER_ABI)
    pair_contract = w3.eth.contract(address=PAIR_ADDRESS, abi=PAIR_ABI)
    deadline = int(time.time()) + 1200  # 20 menit
    
    routes = [(
        token_in,
        token_out,
        False
    )]
    
    amount_out_min = get_expected_output(w3, amount_in, token_in, token_out)
    slippage_adjusted = int(amount_out_min * 0.95)
    
    token_in_name = "wINJ" if token_in == WINJ_ADDRESS else "PMX"
    token_out_name = "PMX" if token_out == PMX_ADDRESS else "wINJ"
    
    Logger.info(f"Output diharapkan: [bold]{w3.from_wei(amount_out_min, 'ether'):.6f}[/bold] {token_out_name}")
    Logger.info(f"Dengan slippage: [bold]{w3.from_wei(slippage_adjusted, 'ether'):.6f}[/bold] {token_out_name}")
    
    # Approve token jika diperlukan
    approve_token(w3, wallet, token_in, ROUTER_ADDRESS, amount_in)
    
    Logger.step(f"Memulai swap: [bold]{w3.from_wei(amount_in, 'ether'):.6f}[/bold] {token_in_name} → {token_out_name}")
    
    try:
        # Bangun transaksi swap
        tx = router_contract.functions.swapExactTokensForTokens(
            amount_in,
            slippage_adjusted,
            routes,
            wallet.address,
            deadline
        ).build_transaction({
            'from': wallet.address,
            'nonce': w3.eth.get_transaction_count(wallet.address),
            'gas': 600000,
            'gasPrice': w3.eth.gas_price
        })
        
        # Tandatangani dan kirim transaksi
        signed_tx = wallet.sign_transaction(tx)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
        Logger.transaction_status(tx_hash.hex(), "pending", tx_num)
        
        with Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(bar_width=None),
            TimeRemainingColumn(),
            transient=True
        ) as progress:
            task = progress.add_task("[cyan]Mengkonfirmasi transaksi...", total=1)
            receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            progress.update(task, advance=1)
        
        if receipt.status != 1:
            raise Exception(f"Transaksi gagal")
        
        Logger.transaction_status(tx_hash.hex(), "success", tx_num)
        
        # Proses event logs
        for log in receipt['logs']:
            if log['address'].lower() == PAIR_ADDRESS.lower():
                try:
                    event = pair_contract.events.Swap().process_log(log)
                    amount0_out = w3.from_wei(event.args['amount0Out'], 'ether')
                    amount1_out = w3.from_wei(event.args['amount1Out'], 'ether')
                    Logger.info(f"Swap berhasil: [bold]{amount0_out:.6f}[/bold] wINJ ⇄ [bold]{amount1_out:.6f}[/bold] PMX")
                except:
                    continue
        return True
    except Exception as e:
        Logger.error(f"Swap gagal: {str(e)}")
        return False

def get_token_balance(w3, wallet, token_address, token_name):
    token_contract = w3.eth.contract(address=token_address, abi=ERC20_ABI)
    balance = token_contract.functions.balanceOf(wallet.address).call()
    Logger.info(f"Balance {token_name}: [bold]{w3.from_wei(balance, 'ether'):.6f}[/bold]")
    return balance

def main_menu():
    console.print(Panel(
        "PILIH ARAH SWAP",
        box=box.ROUNDED,
        style=Style(color=THEME["secondary"]),
        width=40
    ))
    
    options = [
        ("1", "Swap wINJ ke PMX"),
        ("2", "Swap PMX ke wINJ")
    ]
    
    grid = Table.grid(expand=True)
    grid.add_column(width=4)
    grid.add_column()
    
    for num, text in options:
        grid.add_row(
            f"[{THEME['accent']}][bold]{num}[/bold][/]",
            text
        )
    
    console.print(grid, justify="center")
    
    choice = console.input(f"[{THEME['primary']}]»[/] Masukkan pilihan [1-2]: ")
    return choice

def main():
    show_banner()
    
    # Inisialisasi Web3
    w3 = init_web3()
    
    # Load private keys
    private_keys = load_private_keys()
    
    # Tampilkan daftar wallet
    console.print(Panel(
        create_wallet_table(w3, private_keys),
        title="[bold]WALLET TERDETEKSI[/bold]",
        border_style=Style(color=THEME["primary"])
    ))
    
    # Pilih arah swap
    choice = main_menu()
    
    if choice == '1':
        token_in = WINJ_ADDRESS
        token_out = PMX_ADDRESS
        token_in_name = "wINJ"
    elif choice == '2':
        token_in = PMX_ADDRESS
        token_out = WINJ_ADDRESS
        token_in_name = "PMX"
    else:
        Logger.error("Pilihan tidak valid")
        return
    
    # Input jumlah token
    amount_str = console.input(
        f"[{THEME['primary']}]»[/] Masukkan jumlah {token_in_name} per swap: ")
    try:
        amount_in = w3.to_wei(float(amount_str), 'ether')
    except ValueError:
        Logger.error("Jumlah tidak valid")
        return
    
    # Input jumlah transaksi
    tx_count_str = console.input(
        f"[{THEME['primary']}]»[/] Jumlah swap per wallet: ")
    try:
        tx_count = int(tx_count_str)
        if tx_count <= 0:
            raise ValueError
    except ValueError:
        Logger.error("Jumlah tidak valid")
        return
    
    # Ringkasan eksekusi
    console.print(Panel(
        f"[bold]RINCIAN EKSEKUSI[/bold]\n\n"
        f"• Arah swap: [bold]{token_in_name} → {'PMX' if token_out == PMX_ADDRESS else 'wINJ'}[/bold]\n"
        f"• Jumlah per swap: [bold]{w3.from_wei(amount_in, 'ether'):.6f} {token_in_name}[/bold]\n"
        f"• Swap per wallet: [bold]{tx_count}[/bold]\n"
        f"• Total wallet: [bold]{len(private_keys)}[/bold]",
        title="[bold]KONFIRMASI[/bold]",
        border_style=Style(color=THEME["accent"])
    ))
    
    confirm = console.input(f"[{THEME['primary']}]»[/] Lanjutkan? (y/N): ")
    if confirm.lower() != 'y':
        Logger.warn("Eksekusi dibatalkan")
        return
    
    # Statistik keseluruhan
    total_swaps = len(private_keys) * tx_count
    successful_swaps = 0
    start_time = time.time()
    
    # Proses untuk setiap private key
    for idx, pk in enumerate(private_keys, 1):
        try:
            wallet = w3.eth.account.from_key(pk)
            if not wallet.address:
                Logger.error(f"Wallet tidak valid: {pk[:6]}...")
                continue
            
            console.print(Panel(
                f"[bold]{wallet.address}[/bold]\n"
                f"Wallet [bold]{idx}[/bold] dari [bold]{len(private_keys)}[/bold]",
                title=f"🚀 PROSES WALLET {idx}",
                border_style=Style(color=THEME["info"])
            ))
            
            # Cek balance
            balance = get_token_balance(w3, wallet, token_in, token_in_name)
            total_required = amount_in * tx_count
            
            if balance < total_required:
                Logger.error(f"Saldo tidak mencukupi! Diperlukan: {w3.from_wei(total_required, 'ether'):.6f} {token_in_name}")
                continue
            
            # Eksekusi swap
            for tx_num in range(1, tx_count + 1):
                console.rule(f"Swap [bold]{tx_num}[/bold] dari [bold]{tx_count}[/bold]", style=Style(color=THEME["secondary"]))
                success = swap_tokens(w3, wallet, amount_in, token_in, token_out, tx_num)
                if success:
                    successful_swaps += 1
                
                # Jeda antar transaksi
                if tx_num < tx_count:
                    time.sleep(3)
        
        except Exception as e:
            Logger.error(f"Error pada wallet: {str(e)}")
    
    # Ringkasan akhir
    elapsed_time = time.time() - start_time
    panel_content = (
        f"[bold]• TOTAL SWAP:[/bold] {total_swaps}\n"
        f"[bold]• BERHASIL:[/bold] {successful_swaps}\n"
        f"[bold]• GAGAL:[/bold] {total_swaps - successful_swaps}\n"
        f"[bold]• WAKTU:[/bold] {elapsed_time:.2f} detik\n"
        f"[bold]• RATA-RATA:[/bold] {elapsed_time/total_swaps if total_swaps > 0 else 0:.2f} detik/swap"
    )
    
    border_style = THEME["success"] if successful_swaps == total_swaps else THEME["warning"]
    
    console.print(
        Panel(
            panel_content,
            title="[bold]📊 HASIL AKHIR[/bold]",
            border_style=Style(color=border_style),
            padding=(1, 4)
    )

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        Logger.warn("Program dihentikan oleh pengguna")
        exit(0)
    except Exception as e:
        Logger.error(f"Error fatal: {str(e)}")
        exit(1)
