import asyncio
import json
import websockets

async def price_stream(symbol="btcusdt"):
    url = f"wss://stream.binance.com:9443/ws/{symbol}@kline_1m"
    async with websockets.connect(url) as ws:
        while True:
            data = json.loads(await ws.recv())
            kline = data['k']
            yield {
                'symbol': symbol,
                'open': float(kline['o']),
                'high': float(kline['h']),
                'low': float(kline['l']),
                'close': float(kline['c']),
                'volume': float(kline['v'])
            }
