import pandas as pd
import ta

def add_indicators(df):
    df['rsi'] = ta.momentum.RSIIndicator(df['close']).rsi()
    df['ema_fast'] = ta.trend.EMAIndicator(df['close'], 12).ema_indicator()
    df['ema_slow'] = ta.trend.EMAIndicator(df['close'], 26).ema_indicator()
    df['macd'] = ta.trend.MACD(df['close']).macd()
    return df
