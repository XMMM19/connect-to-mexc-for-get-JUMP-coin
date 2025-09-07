# MEXC Spot WebSocket — BookTicker Example (JUMP/USDT)

Этот скрипт подключается к **MEXC Spot WebSocket API (V3)** и подписывается на канал `bookTicker` для пары **JUMP/USDT**, чтобы получать лучшие цены bid/ask в реальном времени.

---

## Требования

- Python 3.10+  
- Виртуальное окружение (рекомендуется)

Установка зависимостей:
```bash
python -m venv venv
source venv/bin/activate   # Linux/macOS
venv\Scripts\activate      # Windows

pip install -r requirements.txt

```

---

## Запуск

```bash
python main.py
```

После запуска вы увидите:
- Подключение к `wss://wbs-api.mexc.com/ws`
- Подтверждение подписки
- Периодические `PONG` от сервера
- Строки с лучшими bid/ask:

```
[bookTicker] JUMPUSDT | bid 0.1234 x 100  ask 0.1236 x 150  (channel=spot@...)
```

Остановить выполнение:  
Нажмите `Ctrl + C` — соединение закроется корректно.

---

## Настройки

Файл: `main.py`

- **Символ:**  
  ```python
  SYMBOL = "JUMPUSDT"
  ```
  Можно поменять на любой другой (например, `BTCUSDT`). Символ пишется только **в верхнем регистре**.

- **Интервал обновления:**  
  ```python
  INTERVAL = "100ms"
  ```
  Возможные значения: `"100ms"` (реже) или `"10ms"` (чаще, выше нагрузка).

- **Канал:**  
  По умолчанию используется `bookTicker`.  
  Можно заменить на:
  - сделки: `spot@public.aggre.deals.v3.api.pb@100ms@SYMBOL`
  - стакан: `spot@public.aggre.depth.v3.api.pb@100ms@SYMBOL`
  - свечи: `spot@public.kline.v3.api.pb@1m@SYMBOL`

---

## Технические детали

- Подключение к `wss://wbs-api.mexc.com/ws`
- Поддержка соединения через `PING/PONG`
- Сообщения в формате **Protocol Buffers (protobuf)**  
  В проект включены необходимые файлы:
  - `PushDataV3ApiWrapper_pb2.py`
  - `PublicAggreBookTickerV3Api_pb2.py`
- Используется `sslopt` с `certifi` для корректной проверки SSL на macOS/Windows