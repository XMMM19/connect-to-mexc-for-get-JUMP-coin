

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MEXC spot WebSocket: subscribe to JUMP/USDT bookTicker (best bid/ask) stream.

• Endpoint: wss://wbs-api.mexc.com/ws
• Channel example: "spot@public.aggre.bookTicker.v3.api.pb@100ms@JUMPUSDT"

By default, MEXC V3 websocket market streams push data in Google Protocol Buffers (protobuf).
This script connects and subscribes. If protobuf Python classes are available, it will decode
and pretty-print messages; otherwise it will just show that binary data is received.

Requirements (any of these two modes):
  Minimal (no decode):
    pip install websocket-client

  With protobuf decoding:
    1) pip install websocket-client protobuf
    2) Clone https://github.com/mexcdevelop/websocket-proto and generate Python classes, e.g.:
         protoc --python_out=. *.proto
       Ensure the generated module `PushDataV3ApiWrapper_pb2.py` is importable
       (same directory as this script or in PYTHONPATH).

References:
  - Websocket Market Streams (Spot V3): https://www.mexc.com/api-docs/spot-v3/websocket-market-streams
  - Announcement about using wss://wbs-api.mexc.com/ws endpoint (2025): https://www.mexc.com/support/articles/17827791522393
"""

import json
import threading
import time
import traceback
from typing import Optional

import websocket  # type: ignore

# --- Configuration ---
SYMBOL = "JUMPUSDT"  # Trading pair must be uppercase per docs
INTERVAL = "100ms"   # Supported: 100ms or 10ms (10ms = higher throughput)
CHANNEL = f"spot@public.aggre.bookTicker.v3.api.pb@{INTERVAL}@{SYMBOL}"
WS_URL = "wss://wbs-api.mexc.com/ws"
PING_INTERVAL_SEC = 20  # Send PING periodically to keep the connection alive

# Try to import protobuf wrapper if available
try:
    from PushDataV3ApiWrapper_pb2 import PushDataV3ApiWrapper  # type: ignore
except Exception:  # noqa: BLE001
    PushDataV3ApiWrapper = None  # type: ignore


def _send_ping_forever(ws: websocket.WebSocketApp) -> None:
    """Background task that sends PING frames as JSON messages."""
    while True:
        try:
            ws.send(json.dumps({"method": "PING"}))
        except Exception:
            # Socket likely closed; exit thread
            break
        time.sleep(PING_INTERVAL_SEC)


def on_open(ws: websocket.WebSocketApp) -> None:
    print("[open] Connected. Subscribing to:", CHANNEL)
    sub = {"method": "SUBSCRIPTION", "params": [CHANNEL]}
    ws.send(json.dumps(sub))

    # Start periodic PINGs
    threading.Thread(target=_send_ping_forever, args=(ws,), daemon=True).start()


def on_message(ws: websocket.WebSocketApp, message: bytes | str) -> None:
    # Server replies to SUBSCRIPTION/PING with small JSON texts
    if isinstance(message, str):
        print("[text]", message)
        return

    # Binary frame (protobuf). Try to decode if the proto class is present.
    if PushDataV3ApiWrapper is None:
        print(f"[binary] {len(message)} bytes (protobuf). Install and generate proto classes to decode.")
        return

    try:
        wrapper = PushDataV3ApiWrapper()
        wrapper.ParseFromString(message)
        channel = getattr(wrapper, "channel", "")
        symbol = getattr(wrapper, "symbol", "")
        # For bookTicker, the payload field is `publicbookticker`
        pbt = getattr(wrapper, "publicbookticker", None)
        if pbt and (pbt.bidprice or pbt.askprice):
            print(
                f"[bookTicker] {symbol} | bid {pbt.bidprice} x {pbt.bidquantity}  "
                f"ask {pbt.askprice} x {pbt.askquantity}  (channel={channel})"
            )
        else:
            # Fallback: just show known meta fields
            send_time = getattr(wrapper, "sendtime", None)
            print(f"[protobuf] channel={channel} symbol={symbol} sendtime={send_time}")
    except Exception:
        print("[error] Failed to decode protobuf message:")
        traceback.print_exc()


def on_error(ws: websocket.WebSocketApp, error: Exception) -> None:
    print("[error]", error)


def on_close(ws: websocket.WebSocketApp, code: Optional[int], reason: Optional[str]) -> None:
    print(f"[close] code={code} reason={reason}")


if __name__ == "__main__":
    # Note: some environments require `websocket.enableTrace(True)` for debugging
    # websocket.enableTrace(True)
    app = websocket.WebSocketApp(
        WS_URL,
        on_open=on_open,
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )

    # Run forever with simple reconnect on unexpected exit
    while True:
        try:
            app.run_forever(ping_interval=None, ping_timeout=None)
        except KeyboardInterrupt:
            print("Interrupted by user. Bye!")
            break
        except Exception as e:  # noqa: BLE001
            print("[run_forever error]", e)
            time.sleep(3)