import asyncio
import pandas as pd
from exchanges import connect_exchange
from data_stream import price_stream
from indicators import add_indicators
from strategy import rule_based_strategy, execute_trade
from trader_ai import TraderAI, ai_decision

EXCHANGES = {
    'binance': connect_exchange('binance', 'API_KEY', 'SECRET'),
    #you can add more exchanges
}

SYMBOLS = ['btcusdt', 'ethusdt']  # a number of cryptocurrencies
MODEL = TraderAI()

async def main():
    candles = {sym: [] for sym in SYMBOLS}

    async def handle_symbol(sym):
        async for tick in price_stream(sym):
            candles[sym].append(tick)
            if len(candles[sym]) < 50:
                continue

            df = pd.DataFrame(candles[sym][-50:])
            df = add_indicators(df)

            # hybrid desision Rule + AI
            rule_signal = rule_based_strategy(df)
            ai_signal = ai_decision(MODEL, df.iloc[-1][['close','rsi','ema_fast','ema_slow','macd','volume']].values)

            final_signal = rule_signal if rule_signal != 'HOLD' else ai_signal

            execute_trade(EXCHANGES['binance'], sym.upper(), final_signal, 0.001)

    await asyncio.gather(*(handle_symbol(sym) for sym in SYMBOLS))

if __name__ == "__main__":
    asyncio.run(main())
