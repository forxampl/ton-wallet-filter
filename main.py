import asyncio
import argparse
from database import init_db, all_wallets
from collector import from_blocks, from_file
from enricher import run as enrich
from filters import run as filter_wallets
from exporter import save_txt
from config import OUT


def args():
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["collect", "enrich", "filter", "full"], default="full")
    p.add_argument("--input-file", default=None)
    p.add_argument("--blocks", type=int, default=50)
    p.add_argument("--batch-size", type=int, default=200)
    p.add_argument("--min-balance", type=float, default=0.0)
    p.add_argument("--max-balance", type=float, default=None)
    p.add_argument("--min-age", type=int, default=0)
    p.add_argument("--max-age", type=int, default=None)
    p.add_argument("--min-nft", type=int, default=0)
    p.add_argument("--max-nft", type=int, default=None)
    p.add_argument("--min-tokens", type=int, default=0)
    p.add_argument("--token", type=str, default=None)
    p.add_argument("--token-min", type=float, default=0.0)
    p.add_argument("--funded-from", type=str, default=None)
    p.add_argument("--funded-from-all", action="store_true")
    p.add_argument("--output", type=str, default=OUT)
    return p.parse_args()


async def main():
    a = args()
    init_db()

    if a.mode in ("collect", "full"):
        if a.input_file:
            from_file(a.input_file)
        else:
            await from_blocks(a.blocks)

    if a.mode in ("enrich", "full"):
        await enrich(a.batch_size)

    if a.mode in ("filter", "full"):
        if a.funded_from:
            a.funded_from = [s.strip() for s in a.funded_from.split(",")]
        else:
            a.funded_from = []

        wallets = all_wallets()
        result = filter_wallets(wallets, a)
        print(f"[main] {len(wallets)} → {len(result)} кошельков после фильтрации")
        save_txt(result, a.output)


asyncio.run(main())
