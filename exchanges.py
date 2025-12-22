import ccxt

def connect_exchange(name, api_key, secret):
    exchange_class = getattr(ccxt, name)
    exchange = exchange_class({
        'apiKey': api_key,
        'secret': secret,
        'enableRateLimit': True
    })
    return exchange
