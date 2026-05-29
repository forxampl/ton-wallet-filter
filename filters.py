from datetime import datetime, timezone


def age_days(first_seen):
    if first_seen is None:
        return None
    return int((datetime.now(timezone.utc).timestamp() - first_seen) / 86400)


def normalize(s):
    return s.lower().replace("₮", "t").replace("$", "s").strip()


def token_balance(tokens_list, symbol):
    sym = normalize(symbol)
    for t in tokens_list:
        if normalize(t.get("symbol", "")) == sym:
            return t.get("balance", 0.0)
    return 0.0


def run(wallets, args):
    out = []
    for w in wallets:
        if w["balance"] < args.min_balance:
            continue
        if args.max_balance and w["balance"] > args.max_balance:
            continue

        age = age_days(w.get("first_seen"))

        if args.min_age or args.max_age:
            if age is None:
                continue
            if args.min_age and age < args.min_age:
                continue
            if args.max_age and age > args.max_age:
                continue

        if w["nfts"] < args.min_nft:
            continue
        if args.max_nft and w["nfts"] > args.max_nft:
            continue

        if w["tokens"] < args.min_tokens:
            continue

        if args.token:
            bal = token_balance(w["tokens_list"], args.token)
            if bal < args.token_min:
                continue

        if args.funded_from:
            needed = set(args.funded_from)
            have = set(w.get("sources", []))
            if args.funded_from_all:
                if not needed.issubset(have):
                    continue
            else:
                if not needed & have:
                    continue

        out.append(w)
    return out
