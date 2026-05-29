import asyncio
import aiohttp
import json
from pytoniq_core import Address as TonAddress
from config import API_KEY, BASE_URL, DELAY, TX_LIMIT, EXCHANGES_FILE
from database import get_queue, save

hdrs = {"Authorization": f"Bearer {API_KEY}"}


def to_raw(addr_str: str) -> str:
    try:
        a = TonAddress(addr_str.strip())
        return f"0:{a.hash_part.hex()}"
    except Exception:
        return addr_str.strip().lower()


def to_friendly(addr_str: str, bounceable: bool = False) -> str:
    try:
        a = TonAddress(addr_str.strip())
        return a.to_str(is_user_friendly=True, is_bounceable=bounceable)
    except Exception:
        return addr_str.strip()


with open(EXCHANGES_FILE) as f:
    _raw = json.load(f)

exchange_map: dict[str, str] = {}
for name, addrs in _raw.items():
    for a in addrs:
        exchange_map[to_raw(a)] = name


async def get(session, url, params=None):
    try:
        async with session.get(url, params=params, headers=hdrs) as r:
            if r.status == 200:
                return await r.json()
            return None
    except Exception:
        return None


async def fetch_account(session, addr):
    return await get(session, f"{BASE_URL}/accounts/{addr}")


async def fetch_jettons(session, addr):
    data = await get(session, f"{BASE_URL}/accounts/{addr}/jettons", {"currencies": "ton"})
    if not data:
        return []
    result = []
    for item in data.get("balances", []):
        j = item.get("jetton", {})
        symbol = j.get("symbol", "").strip()
        if not symbol:
            continue
        dec = int(j.get("decimals", 9))
        raw = item.get("balance", "0")
        try:
            bal = int(raw) / (10 ** dec)
        except Exception:
            bal = 0.0
        if bal > 0:
            result.append({"symbol": symbol, "balance": bal})
    return result


async def fetch_nft_count(session, addr):
    data = await get(session, f"{BASE_URL}/accounts/{addr}/nfts", {"limit": 1000, "indirect_ownership": "false"})
    return len(data.get("nft_items", [])) if data else 0


async def fetch_first_seen(session, addr):
    data = await get(session, f"{BASE_URL}/accounts/{addr}/events", {"limit": TX_LIMIT, "subject_only": "false"})
    if not data:
        return None
    ts = [e["timestamp"] for e in data.get("events", []) if e.get("timestamp")]
    return min(ts) if ts else None


async def fetch_sources(session, addr):
    data = await get(session, f"{BASE_URL}/accounts/{addr}/events", {"limit": TX_LIMIT, "subject_only": "true"})
    if not data:
        return []
    found = set()
    for event in data.get("events", []):
        for action in event.get("actions", []):
            for key in ("TonTransfer", "JettonTransfer"):
                sender = (action.get(key) or {}).get("sender", {})
                raw_sender = to_raw(sender.get("address", ""))
                if raw_sender in exchange_map:
                    found.add(exchange_map[raw_sender])
    return list(found)


async def process_wallet(session, addr):
    info = await fetch_account(session, addr)
    if not info:
        return None

    if info.get("status") == "nonexist":
        return None

    ifaces = info.get("interfaces") or []
    is_wallet = (
        not ifaces or
        any(i.startswith("wallet") for i in ifaces)
    )
    if not is_wallet:
        return None

    bal = int(info.get("balance", 0)) / 1e9

    await asyncio.sleep(DELAY)
    jettons = await fetch_jettons(session, addr)

    await asyncio.sleep(DELAY)
    nfts = await fetch_nft_count(session, addr)

    await asyncio.sleep(DELAY)
    first_seen = await fetch_first_seen(session, addr)

    await asyncio.sleep(DELAY)
    sources = await fetch_sources(session, addr)

    friendly_addr = to_friendly(addr, bounceable=False)

    return {
        "address": friendly_addr,
        "balance": bal,
        "first_seen": first_seen,
        "nfts": nfts,
        "tokens": len(jettons),
        "tokens_list": jettons,
        "sources": sources,
    }


async def run(batch=200):
    addrs = get_queue(batch)
    if not addrs:
        print("[enricher] нечего обрабатывать")
        return
    print(f"[enricher] обрабатываю {len(addrs)} адресов...")

    sem = asyncio.Semaphore(3)

    async def job(session, addr):
        async with sem:
            try:
                w = await process_wallet(session, addr)
                if w:
                    save(w)
                    tokens_str = ", ".join(t["symbol"] for t in w["tokens_list"]) or "—"
                    print(f"[enricher] ✓ {w['address'][:30]}  {w['balance']:.2f} TON  {w['nfts']} NFT  токены: {tokens_str}")
                else:
                    print(f"[enricher] ✗ {addr[:22]}  не кошелёк")
            except Exception as e:
                print(f"[enricher] ! {addr[:22]}  ошибка: {e}")

    async with aiohttp.ClientSession() as session:
        await asyncio.gather(*[job(session, a) for a in addrs])

    print("[enricher] готово")
