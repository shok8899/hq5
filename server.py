import json
import asyncio
import websockets
import time
from datetime import datetime

# MT4 Server Configuration
MT4_PORT = 8085
SYMBOLS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "ADAUSDT", "DOGEUSDT",
    "XRPUSDT", "DOTUSDT", "UNIUSDT", "LTCUSDT", "LINKUSDT",
    "SOLUSDT", "MATICUSDT", "AVAXUSDT", "FILUSDT", "ATOMUSDT"
]

class PriceData:
    def __init__(self):
        self.prices = {}
        for symbol in SYMBOLS:
            self.prices[symbol] = {"bid": 0, "ask": 0}

    def update_price(self, symbol, price):
        # Add a small spread (0.1%)
        spread = float(price) * 0.001
        self.prices[symbol] = {
            "bid": float(price) - spread/2,
            "ask": float(price) + spread/2
        }

price_data = PriceData()

async def binance_websocket():
    uri = f"wss://stream.binance.com:9443/ws"
    async with websockets.connect(uri) as websocket:
        # Subscribe to all symbols
        subscribe_msg = {
            "method": "SUBSCRIBE",
            "params": [f"{symbol.lower()}@trade" for symbol in SYMBOLS],
            "id": 1
        }
        await websocket.send(json.dumps(subscribe_msg))
        
        while True:
            try:
                message = await websocket.recv()
                data = json.loads(message)
                if "s" in data and "p" in data:
                    symbol = data["s"]
                    price = data["p"]
                    price_data.update_price(symbol, price)
            except Exception as e:
                print(f"Error in Binance websocket: {e}")
                await asyncio.sleep(5)

async def mt4_handler(websocket, path):
    while True:
        try:
            # Send price updates every 100ms
            message = {
                "timestamp": int(time.time() * 1000),
                "prices": price_data.prices
            }
            await websocket.send(json.dumps(message))
            await asyncio.sleep(0.1)
        except:
            break

async def main():
    # Start Binance WebSocket connection
    binance_task = asyncio.create_task(binance_websocket())
    
    # Start MT4 WebSocket server
    server = await websockets.serve(mt4_handler, "0.0.0.0", MT4_PORT)
    print(f"MT4 Server started on port {MT4_PORT}")
    
    await asyncio.gather(binance_task, server.wait_closed())

if __name__ == "__main__":
    print("Starting Crypto Market Data Server...")
    print("Supported symbols:", ", ".join(SYMBOLS))
    asyncio.run(main())