from config import OUT


def save_txt(wallets, path=OUT):
    if not wallets:
        print("[exporter] ничего нет")
        return
    with open(path, "w", encoding="utf-8") as f:
        for w in wallets:
            f.write(w["address"] + "\n")
    print(f"[exporter] сохранено {len(wallets)} адресов → {path}")
