"""
Утилита для конвертации TON-адресов.

Поддерживает:
  - raw (0:hex)  →  user-friendly (UQ... или EQ...)
  - user-friendly  →  raw (0:hex)
  - конвертация файлов с адресами

Использование:
  python convert_address.py <адрес>
  python convert_address.py --file result.txt
  python convert_address.py --file result.txt --bounceable
"""

import sys
import argparse
from pytoniq_core import Address


def raw_to_friendly(addr_str: str, bounceable: bool = False) -> str:
    addr = Address(addr_str)
    return addr.to_str(is_user_friendly=True, is_bounceable=bounceable)


def friendly_to_raw(addr_str: str) -> str:
    addr = Address(addr_str)
    return f"0:{addr.hash_part.hex()}"


# Короткие алиасы для использования в других модулях
def to_friendly(addr_str: str, bounceable: bool = False) -> str:
    return raw_to_friendly(addr_str, bounceable) if addr_str.startswith("0:") else raw_to_friendly(friendly_to_raw(addr_str), bounceable)


def to_raw(addr_str: str) -> str:
    return friendly_to_raw(addr_str) if not addr_str.startswith("0:") else addr_str.strip().lower()


def convert(addr_str: str, bounceable: bool = False) -> str:
    addr_str = addr_str.strip()
    if addr_str.startswith("0:"):
        return raw_to_friendly(addr_str, bounceable)
    else:
        # уже user-friendly — конвертируем в raw, потом обратно в нужный формат
        raw = friendly_to_raw(addr_str)
        return raw_to_friendly(raw, bounceable)


def convert_file(path: str, bounceable: bool = False, out_path: str = None):
    with open(path, encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]

    converted = []
    errors = []
    for line in lines:
        try:
            converted.append(convert(line, bounceable))
        except Exception as e:
            errors.append((line, str(e)))
            converted.append(line)  # оставляем как есть при ошибке

    result = "\n".join(converted)

    if out_path:
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(result + "\n")
        print(f"[convert] сохранено {len(converted)} адресов → {out_path}")
    else:
        print(result)

    if errors:
        print(f"\n[convert] ошибки ({len(errors)}):", file=sys.stderr)
        for addr, err in errors:
            print(f"  {addr}: {err}", file=sys.stderr)


def main():
    parser = argparse.ArgumentParser(
        description="Конвертер TON-адресов: raw ↔ user-friendly"
    )
    parser.add_argument("address", nargs="?", help="Адрес для конвертации")
    parser.add_argument("--file", "-f", help="Файл с адресами (по одному на строку)")
    parser.add_argument(
        "--out", "-o", help="Куда сохранить результат (по умолчанию stdout)"
    )
    parser.add_argument(
        "--bounceable",
        "-b",
        action="store_true",
        help="Выводить bounceable (EQ...) вместо non-bounceable (UQ...)",
    )
    parser.add_argument(
        "--to-raw",
        action="store_true",
        help="Конвертировать user-friendly → raw (0:hex)",
    )

    args = parser.parse_args()

    if args.file:
        if args.to_raw:
            # raw режим: читаем файл и выводим raw
            with open(args.file, encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
            result = []
            for line in lines:
                try:
                    result.append(friendly_to_raw(line))
                except Exception as e:
                    result.append(line)
                    print(f"[convert] ошибка {line}: {e}", file=sys.stderr)
            out = "\n".join(result)
            if args.out:
                with open(args.out, "w", encoding="utf-8") as f:
                    f.write(out + "\n")
                print(f"[convert] сохранено → {args.out}")
            else:
                print(out)
        else:
            convert_file(args.file, args.bounceable, args.out)

    elif args.address:
        if args.to_raw:
            print(friendly_to_raw(args.address))
        else:
            result = convert(args.address, args.bounceable)
            prefix = "EQ" if args.bounceable else "UQ"
            print(f"user-friendly ({prefix}...): {result}")
            print(f"raw (0:hex):                {friendly_to_raw(args.address)}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
