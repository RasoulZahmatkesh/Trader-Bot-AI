from historical_data import HistoricalData
from train import train

"""
Training Runner Download market data and train AI
"""

def start_training():
    loader = HistoricalData()
    candles = loader.fetch_history()
    print(f"Downloaded {len(candles)} candles")
    train(candles)
if __name__ == "__main__":
    start_training()
