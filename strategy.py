def rule_based_strategy(df):
    last = df.iloc[-1]
    if last['rsi'] < 30 and last['ema_fast'] > last['ema_slow']:
        return 'BUY'
    elif last['rsi'] > 70 and last['ema_fast'] < last['ema_slow']:
        return 'SELL'
    else:
        return 'HOLD'

def execute_trade(exchange, symbol, side, amount):
    try:
        if side == 'BUY':
            order = exchange.create_market_buy_order(symbol, amount)
        elif side == 'SELL':
            order = exchange.create_market_sell_order(symbol, amount)
        else:
            return None
        print(f"Executed {side} on {symbol}: {order}")
        return order
    except Exception as e:
        print(f"Trade error: {e}")
        return None
