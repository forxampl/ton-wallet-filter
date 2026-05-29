# TON Wallet Filter

Инструмент для сбора и фильтрации TON-кошельков по заданным параметрам. Собирает адреса из блокчейна или из файла, обогащает данными (баланс, токены, NFT, история пополнений) и выдаёт отфильтрованный список в `result.txt`.

---

## Установка

**1. Клонировать и перейти в папку проекта**

```bash
cd ton-wallet-filter
```

**2. Установить зависимости**

```bash
pip install -r requirements.txt
```

**3. Прописать API-ключ**

Открыть файл `.env` и вставить свой ключ от [tonapi.io](https://tonapi.io):

```
TONAPI_KEY=ваш_ключ_здесь
```

Бесплатный тариф: 1 запрос/сек. Для комфортной работы с большими объёмами лучше взять платный (~$20/мес).

---

## Быстрый старт

Полный прогон — собрать адреса из последних 50 блоков, обогатить и отфильтровать:

```bash
python main.py
```

Результат окажется в `result.txt` — один адрес на строку, в формате `UQ...`.

---

## Режимы запуска

Можно запускать всё сразу или по частям.

```bash
# Полный цикл (по умолчанию)
python main.py --mode full

# Только собрать адреса (без обогащения)
python main.py --mode collect

# Только обогатить уже собранные адреса
python main.py --mode enrich

# Только применить фильтры к уже обогащённым данным
python main.py --mode filter
```

Если данных уже много в базе, удобно гонять `--mode filter` с разными параметрами — быстро, без повторных запросов к API.

---

## Источник адресов

По умолчанию берёт последние 50 блоков. Можно указать больше или загрузить свой список.

```bash
# Сканировать 200 блоков
python main.py --blocks 200

# Загрузить адреса из файла (поддерживает UQ..., EQ..., 0:hex — любой формат)
python main.py --input-file addresses.txt
```

---

## Фильтры

Все фильтры можно комбинировать между собой.

### Баланс (TON)

```bash
--min-balance 10           # не меньше 10 TON
--max-balance 1000         # не больше 1000 TON
```

### Возраст кошелька (в днях)

Считается по первой транзакции в истории.

```bash
--min-age 30               # кошельку не меньше 30 дней
--max-age 365              # кошельку не больше года
```

### NFT

```bash
--min-nft 1                # хотя бы один NFT
--max-nft 10               # не больше 10 NFT
```

### Количество разных токенов

```bash
--min-tokens 2             # хотя бы 2 разных токена
```

### Баланс конкретного токена

```bash
--token USDT --token-min 100      # не меньше 100 USDT
--token NOT  --token-min 10000    # не меньше 10 000 NOT
```

### Пополнение с определённых адресов

Указываются названия из файла `known_addresses.json`. Сейчас там: `Bybit`, `CryptoBot`, `Xrocket`.

```bash
# Кошельки, которые пополнялись хотя бы с одного из перечисленных
--funded-from "Bybit,CryptoBot,Xrocket"

# Кошельки, которые пополнялись со всех перечисленных одновременно
--funded-from "Bybit,CryptoBot" --funded-from-all
```

Чтобы добавить новую биржу — просто дописать в `known_addresses.json`:

```json
{
  "Bybit": ["UQA17iV3NYcu_Kx13EPJDPylBH41pPh8JrN8DrIgQuGQJoZO"],
  "CryptoBot": ["UQBKTLTjEpnGnmfUccAKVmOkmv5HfDObYxyjWhFGcOyYWuUk"],
  "Xrocket": ["UQD2vzt1G_OtL73SgxBKILLdr4YLMYo3C17c6uFVu7K0nMXZ"],
  "Binance": ["UQ...адрес..."]
}
```

---

## Примеры

Кошельки с балансом от 5 до 500 TON, старше 30 дней:

```bash
python main.py --mode filter --min-balance 5 --max-balance 500 --min-age 30
```

Кошельки с USDT больше 100, пополнявшиеся с Bybit или CryptoBot:

```bash
python main.py --mode filter --token USDT --token-min 100 --funded-from "Bybit,CryptoBot"
```

Активные кошельки с NFT, пополнявшиеся с любого из трёх сервисов:

```bash
python main.py --mode filter --min-nft 1 --min-tokens 1 --funded-from "Bybit,CryptoBot,Xrocket"
```

Полный прогон по 100 блокам с фильтром по балансу, результат в отдельный файл:

```bash
python main.py --blocks 100 --min-balance 10 --output my_result.txt
```

---

## Структура проекта

```
collector/
├── main.py                  — точка входа, аргументы командной строки
├── collector.py             — сбор адресов из блоков или файла
├── enricher.py              — обогащение: баланс, токены, NFT, история
├── filters.py               — логика фильтрации
├── exporter.py              — сохранение результата в файл
├── database.py              — SQLite-кэш (чтобы не запрашивать одно дважды)
├── convert_address.py       — конвертер адресов (UQ ↔ EQ ↔ 0:hex)
├── config.py                — настройки (ключ, лимиты, пути)
├── known_addresses.json     — адреса бирж и сервисов для --funded-from
├── requirements.txt
├── .env                     — API-ключ (не коммитить в git)
└── result.txt               — сюда попадает результат
```

---

## Адреса

Инструмент принимает адреса в любом формате — `UQ...`, `EQ...` или `0:hex`. На выходе всегда `UQ...`.
