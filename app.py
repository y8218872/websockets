# app.py
import asyncio
import json
import os
import websockets

CLIENTS = set()

async def handler(websocket):
    CLIENTS.add(websocket)
    try:
        async for message in websocket:
            for client in CLIENTS:
                if client != websocket:
                    await client.send(message)
    finally:
        CLIENTS.remove(websocket)

async def main():
    # استخدام المنفذ المخصص من Render أو 8765 كخيار افتراضي محلية
    port = int(os.environ.get("PORT", 8765))
    async with websockets.serve(handler, "0.0.0.0", port):
        print(f"الخادم يعمل على المنفذ: {port}")
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())