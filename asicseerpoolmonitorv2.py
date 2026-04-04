import os
import re
import json
import time
import subprocess
from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich import box

# --- CONFIGURATION ---
VERSION = "V2.1.8"
LOG_PATH = "/home/crypto/asicseer-pool/logs/asicseer-pool.log"
CLI_PATH = "/home/crypto/digibyte-8.26.2/bin/digibyte-cli"

console = Console()

# --- STATE MANAGEMENT ---
state = {
    "difficulty": "0",
    "block_hash": "Unknown",
    "reward": "0",
    "runtime": "00:00:00:00",
    "total_users": 0,
    "total_workers": 0,
    "hash_1m": "0", "hash_5m": "0", "hash_1h": "0", "hash_1d": "0",
    "accepted_shares": 0,
    "rejected_shares": 0,
    "sps_1m": 0, "sps_5m": 0, "sps_15m": 0, "sps_1h": 0,
    "current_effort": "0",
    "blocks_solved_total": 0,
    "last_block_time": "Never",
    "solved_height": "N/A",
    "winner_worker": "N/A",
    "solved_effort": "0",
    "solved_share_diff": "0",
    "last_updated_time": "Never"
}

active_workers = [] 
share_history = []  
client_to_ip = {} 
client_to_worker = {}

# --- HELPER FUNCTIONS ---

def format_runtime(seconds):
    try:
        seconds = int(seconds)
        days = seconds // 86400
        remaining_sec = seconds % 86400
        hours = remaining_sec // 3600
        remaining_sec %= 3600
        minutes = remaining_sec // 60
        secs = remaining_sec % 60
        return f"{days:02}:{hours:02}:{minutes:02}:{secs:02}"
    except: return "00:00:00:00"

def format_value(n):
    try:
        n = float(n)
        if n >= 1_000_000_000_000: return f"{n / 1_000_000_000_000:.2f} Th/s"
        if n >= 1_000_000_000: return f"{n / 1_000_000_000:.2f} Gh/s"
        if n >= 1_000_000: return f"{n / 1_000_000:.2f} Mh/s"
        if n >= 1_000: return f"{n / 1_000:.2f} Kh/s"
        return f"{n:.2f} H/s"
    except: return "0"

def format_hashrate_str(s):
    if not s: return "0"
    return str(s).replace("T", " Th/s").replace("G", " Gh/s").replace("M", " Mh/s").replace("K", " Kh/s")

def format_username(u):
    if not u or u == "None": return "NA"
    u = u.strip()
    if ":" in u: u = u.split(":")[-1]
    return u if len(u) <= 31 else f"{u[:20]}...{u[-6:]}"

def get_cli_reward():
    try:
        result = subprocess.run([CLI_PATH, "getblockreward"], capture_output=True, text=True, timeout=3)
        if result.returncode == 0:
            data = json.loads(result.stdout)
            return str(data.get("blockreward", "0"))
    except: pass
    return "0"

# --- LOG PARSING ENGINE ---

def parse_line(line):
    global active_workers, share_history, client_to_ip, client_to_worker
    updated = False
    line = line.strip()

    ts_match = re.search(r'\[(\d{4}-\d{2}-\d{2}\s(\d{2}:\d{2}:\d{2}))', line)
    log_ts = ts_match.group(1) if ts_match else ""
    short_ts = ts_match.group(2) if ts_match else time.strftime('%H:%M:%S')

    # 1. IP discovery
    if "Mining configure requested from" in line:
        conf_match = re.search(r'requested from (\d+) ([\d\.]+)', line)
        if conf_match:
            cid, ip = conf_match.groups()
            client_to_ip[cid] = ip

    # 2. Worker Authorization
    if "authorized client" in line or "authorised client" in line:
        auth_match = re.search(r'(?:authorized|authorised) client (\d+) worker ([^\s]+) as user ([^\s]+)', line)
        if auth_match:
            cid, full_worker, full_user = auth_match.groups()
            ip_val = client_to_ip.get(cid)
            if not ip_val:
                ip_search = re.search(r'(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})', line)
                ip_val = ip_search.group(1) if ip_search else "NA"
            
            worker_name = full_worker.split('.')[-1] if '.' in full_worker else full_worker
            client_to_worker[cid] = worker_name
            entry = f"{worker_name} / {ip_val} / {format_username(full_user)}"
            active_workers = [w for w in active_workers if not w.startswith(worker_name + " /")]
            active_workers.insert(0, entry)
            if len(active_workers) > 25: active_workers.pop()
            updated = True

    # 3. Handle Dropped Client (The Fix)
    if "Dropped client" in line:
        drop_match = re.search(r'worker ([^\s]+)', line)
        if drop_match:
            full_w = drop_match.group(1).strip()
            target = full_w.split('.')[-1] if '.' in full_w else full_w
            # Remove from active display list
            active_workers = [w for w in active_workers if not w.startswith(target + " /")]
            updated = True

    # 4. Share History
    if "Accepted client" in line and "share diff" in line:
        m = re.search(r'Accepted client (\d+) share diff ([\d.]+)/', line)
        if m:
            cid, raw_diff = m.groups()
            worker_name = client_to_worker.get(cid, f"ID:{cid}")
            formatted_diff = format_value(raw_diff)
            share_history.insert(0, (short_ts, worker_name, formatted_diff))
            if len(share_history) > 60: share_history.pop()
            updated = True

    # 5. Pool Stats (JSON)
    if "Pool:{" in line:
        try:
            json_str = "{" + line.split("Pool:{")[1]
            data = json.loads(json_str)
            if "reward" in data: state["reward"] = str(data["reward"])
            if "runtime" in data:
                state["runtime"] = format_runtime(data["runtime"])
                state["total_users"] = data.get("Users", state["total_users"])
                state["total_workers"] = data.get("Workers", state["total_workers"])
            if "hashrate1m" in data:
                state["hash_1m"] = format_hashrate_str(data["hashrate1m"])
                state["hash_5m"] = format_hashrate_str(data["hashrate5m"])
                state["hash_1h"] = format_hashrate_str(data["hashrate1hr"])
                state["hash_1d"] = format_hashrate_str(data["hashrate1d"])
            if "SPS1m" in data:
                state["sps_1m"] = data.get("SPS1m", 0)
                state["sps_5m"] = data.get("SPS5m", 0)
                state["sps_15m"] = data.get("SPS15m", 0)
                state["sps_1h"] = data.get("SPS1h", 0)
            if "accepted" in data:
                state["accepted_shares"] = data["accepted"]
                state["rejected_shares"] = data["rejected"]
                state["current_effort"] = data.get("diff", "0")
            updated = True
        except: pass

    # 6. Network / Block Logic
    if "Network difficulty changed:" in line or "Network diff set to" in line:
        val = line.split("changed: ")[1].strip() if "changed:" in line else line.split("set to ")[1].strip()
        state["difficulty"] = format_value(val)
        updated = True

    if "Block hash changed to" in line:
        state["block_hash"] = line.split("to ")[1].strip()
        updated = True

    if "BLOCK ACCEPTED!" in line:
        state["blocks_solved_total"] += 1
        state["last_block_time"] = log_ts
        updated = True

    if "Solved and confirmed block" in line:
        parts = line.split("confirmed block ")[1].split(" by ")
        state["solved_height"] = parts[0].strip()
        raw_worker = parts[1].strip()
        state["winner_worker"] = raw_worker.split('.')[-1] if '.' in raw_worker else raw_worker
        updated = True

    if "Block solved after" in line:
        effort_match = re.search(r'at ([\d.]+)% diff', line)
        if effort_match: state["solved_effort"] = effort_match.group(1)
        updated = True

    if "Submitting possible block solve share diff" in line:
        diff_val = line.split("share diff ")[1].split(" !")[0].strip()
        state["solved_share_diff"] = format_value(diff_val)
        updated = True

    if updated: state["last_updated_time"] = time.strftime('%H:%M:%S')
    return updated

# --- UI COMPONENTS ---

def get_status_table():
    table = Table(show_header=False, border_style="grey23", expand=True, padding=(0,1), box=box.SQUARE)
    table.add_column("Label", style="cyan", width=25)
    table.add_column("Value", style="white")

    # NETWORK
    table.add_row("[bold underline]NETWORK[/bold underline]", "")
    table.add_row("Difficulty", f"[yellow]{state['difficulty']}[/yellow]")
    table.add_row("Block Hash", f"[green]{state['block_hash']}[/green]")
    table.add_row("Current Reward", f"[bold gold1]{state['reward']}[/bold gold1]")
    table.add_section()

    # SESSION
    table.add_row("[bold underline]SESSION[/bold underline]", "")
    table.add_row("Runtime", f"{state['runtime']} | Users: {state['total_users']} | Workers: {state['total_workers']}")
    table.add_section()

    # USER
    table.add_row("[bold underline]USER[/bold underline]", "")
    if not active_workers:
        table.add_row("Worker / IP / Username", "[dim red]No active workers[/dim red]")
    else:
        table.add_row("Worker / IP / Username", f"[bold yellow]1. {active_workers[0]}[/bold yellow]")
        for i, w in enumerate(active_workers[1:], 2):
            table.add_row("", f"[bold yellow]{i}. {w}[/bold yellow]")
    table.add_section()

    # HASHRATE
    table.add_row("[bold underline]HASHRATE[/bold underline]", "")
    table.add_row("Performance", f"1m: [bold green]{state['hash_1m']}[/bold green] | 5m: [bold green]{state['hash_5m']}[/bold green] | 1h: [bold green]{state['hash_1h']}[/bold green] | 1d: [bold green]{state['hash_1d']}[/bold green]")
    table.add_section()

    # SHARES
    rej_rate = 0.0
    if state["accepted_shares"] > 0:
        rej_rate = (state["rejected_shares"] / state["accepted_shares"]) * 100
    rate_style = "bold red" if rej_rate > 0 else "green"
    
    table.add_row("[bold underline]SHARES[/bold underline]", "")
    table.add_row("Status", f"Accepted: [green]{state['accepted_shares']}[/green] | Rejected: [red]{state['rejected_shares']}[/red] | Rate: [{rate_style}]{rej_rate:.2f}%[/{rate_style}]")
    table.add_row("SPS", f"1m: {state['sps_1m']} | 5m: {state['sps_5m']} | 15m: {state['sps_15m']} | 1h: {state['sps_1h']}")
    table.add_row("Effort", f"Current Effort: [magenta]{state['current_effort']}%[/magenta]")
    table.add_section()

    # BLOCKS
    table.add_row("[bold underline]BLOCKS[/bold underline]", "")
    table.add_row("Accepted", f"[bold green]{state['blocks_solved_total']}[/bold green]")
    table.add_row("Last Block Found", f"{state['last_block_time']}")
    table.add_row("Block Height", f"[bold cyan]{state['solved_height']}[/bold cyan]")
    table.add_row("Winner Worker", f"[bold yellow]{state['winner_worker']}[/bold yellow]")
    table.add_row("Solved Effort", f"{state['solved_effort']}%")
    table.add_row("Solved Share Difficulty", f"{state['solved_share_diff']}")
    
    return Panel(table, title="[bold cyan]Pool Status[/bold cyan]", border_style="grey23")

def get_share_activity():
    table = Table(show_header=True, header_style="bold magenta", box=None, expand=True)
    table.add_column("Time", style="dim", width=10)
    table.add_column("Worker", style="yellow")
    table.add_column("Difficulty", justify="right")
    
    for ts, worker, diff in share_history:
        diff_color = "green" 
        if "Th/s" in diff: diff_color = "red3"
        elif "Gh/s" in diff: diff_color = "white"
        elif "Mh/s" in diff: diff_color = "bright_yellow"
        elif "H/s" in diff: diff_color = "grey70"
        table.add_row(ts, worker, Text(diff, style=diff_color))
        
    return Panel(table, title="[bold white]Share Activity[/bold white]", border_style="grey23")

def make_layout():
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(name="body", ratio=1),
        Layout(name="footer", size=3)
    )
    layout["body"].split_row(
        Layout(name="status", ratio=7),
        Layout(name="share_activity", ratio=3)
    )
    return layout

# --- MAIN ---

def main():
    if not os.path.exists(LOG_PATH): return
    with open(LOG_PATH, "r") as f:
        for line in f: parse_line(line)
    if state["reward"] == "0": state["reward"] = get_cli_reward()

    ui_layout = make_layout()
    with open(LOG_PATH, "r") as f:
        f.seek(0, 2)
        with Live(ui_layout, refresh_per_second=4, screen=True) as live:
            while True:
                line = f.readline()
                if line: parse_line(line)
                
                header_text = f"ASICseer Pool Monitor | {VERSION} | {time.strftime('%Y-%m-%d %H:%M:%S')}"
                footer_text = f"Last Updated: {state['last_updated_time']} | Press Ctrl+C to Exit"
                ui_layout["header"].update(Panel(Text(header_text, justify="center", style="bold green"), border_style="green"))
                ui_layout["footer"].update(Panel(Text(footer_text, justify="center"), border_style="white"))
                ui_layout["status"].update(get_status_table())
                ui_layout["share_activity"].update(get_share_activity())
                time.sleep(0.1)

if __name__ == "__main__":
    try: main()
    except KeyboardInterrupt: pass
