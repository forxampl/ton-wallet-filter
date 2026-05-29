import asyncio
import aiohttp
from config import API_KEY, BASE_URL, DELAY
from database import add_to_queue
from convert_address import to_friendly, to_raw

hdrs = {"Authorization": f"Bearer {API_KEY}"}


async def get(session, url, params=None):
    try:
        async with session.get(url, params=params, headers=hdrs) as r:
            return await r.json() if r.status == 200 else None
    except:
        return None


async def last_seqno(session):
    data = await get(session, f"{BASE_URL}/blockchain/masterchain-head")
    return data.get("seqno") if data else None


async def block_addresses(session, seqno):
    data = await get(session, f"{BASE_URL}/blockchain/masterchain/{seqno}/transactions", {"limit": 256})
    if not data:
        return []
    addrs = set()
    for tx in data.get("transactions", []):
        a = tx.get("account", {}).get("address")
        if a:
            addrs.add(to_friendly(a))
        src = tx.get("in_msg", {}).get("source", {}).get("address")
        if src:
            addrs.add(to_friendly(src))
    return list(addrs)


async def from_blocks(n=50):
    print(f"[collector] сканирую {n} блоков...")
    async with aiohttp.ClientSession() as session:
        seqno = await last_seqno(session)
        if not seqno:
            print("[collector] не получилось достать последний блок")
            return
        all_addrs = set()
        for i in range(n):
            addrs = await block_addresses(session, seqno - i)
            all_addrs.update(addrs)
            print(f"[collector] блок {seqno - i}: +{len(addrs)} (итого {len(all_addrs)})")
            await asyncio.sleep(DELAY)
    add_to_queue(list(all_addrs))
    print(f"[collector] добавлено {len(all_addrs)} адресов")


def from_file(path):
    with open(path) as f:
        lines = [line.strip() for line in f if line.strip()]

    addrs = []
    for line in lines:
        try:
            addrs.append(to_friendly(line))
        except Exception:
            print(f"[collector] не смог распознать адрес: {line}")

    add_to_queue(addrs)
    print(f"[collector] загружено {len(addrs)} адресов из файла")
