import random
from ai_model import AIModel
from market_data import MarketData
from predictor import Predictor
from signal import Signal
from config import CONFIG
import time
from engine import TradingEngine
from logger import log
from config import CONFIG
import ccxt
import torch
import torch.nn as nn
import numpy as np
from torch.utils.data import Dataset
from torch.utils.data import DataLoader
from ai_model import LSTMModel
from dataset import TradingDataset
from torch.utils.data import Dataset
from datetime import datetime
from engine import TradingEngine
from fastapi import FastAPI
from api import get_signal





#CONFIG
"""
Engine Configuration
"""
CONFIG = {"exchange": "binance",
    "symbol": "BTC/USDT",
    "timeframe": "5m",
    "limit": 1000,
    "history_limit": 5000,
    "sequence_length": 50,
    "model_path": "model.pth",
    "model_type": "lstm",
    "model_type": "transformer",
    "model_type": "transformer",
    "model_path": "model.pth"}


# SIGNAL
"""
Signal Response Object
"""
class Signal:
    def __init__(self, symbol, direction, confidence, model, probability):
        self.symbol = symbol
        self.direction = direction
        self.confidence = confidence
        self.model = model
        self.probability = probability
        self.time = datetime.utcnow().isoformat()
        
    def json(self):
        return {"symbol": self.symbol,
            "signal": self.direction,
            "confidence": round(self.confidence, 4),
            "model": self.model,
            "probability": self.probability,
            "timestamp": self.time}
    
    
    
# MARKET DATA
"""
Real Market Data Provider
Powered by CCXT
"""
class MarketData:
    def __init__(self):
        exchange_name = CONFIG["exchange"]
        exchange_class = getattr(ccxt, exchange_name)
        self.exchange = exchange_class({"apiKey": CONFIG["api_key"],
            "secret": CONFIG["secret"],
            "enableRateLimit": True})
    def get_data(self, symbol=None, timeframe=None):
        if symbol is None:
            symbol = CONFIG["symbol"]
        if timeframe is None:
            timeframe = CONFIG["timeframe"]
        candles = self.exchange.fetch_ohlcv(symbol, timeframe, limit=CONFIG["limit"]) 
        formatted = []
        for candle in candles:
            formatted.append({"timestamp": candle[0],
                "open": candle[1],
                "high": candle[2],
                "low": candle[3],
                "close": candle[4],
                "volume": candle[5]})
        return formatted
    
    
    
    
#HISTORICAL DATA
"""
Historical Market Data Loader

Download historical OHLCV
using CCXT
"""
class HistoricalData:
    def __init__(self):
        exchange_class = getattr(ccxt, CONFIG["exchange"])
        self.exchange = exchange_class({"enableRateLimit": True})
    def fetch_history(self):
        symbol = CONFIG["symbol"]
        timeframe = CONFIG["timeframe"]
        limit = CONFIG["history_limit"]
        all_candles = []
        since = None
        while len(all_candles) < limit:
            candles = self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=1000)
            if not candles:
                break
            all_candles.extend(candles)
            since = candles[-1][0]
            time.sleep(self.exchange.rateLimit / 1000)
        return self.format(all_candles[:limit])
    def format(self, candles):
        result = []
        for candle in candles:
            result.append({"timestamp":candle[0],
                "open":candle[1],
                "high":candle[2],
                "low":candle[3],
                "close":candle[4],
                "volume": candle[5]})
        return result
    
    
    
    
#AI MODEL
"""
AI Trading Models

Contains:
- LSTM Model
- Transformer Model

Input:
OHLCV sequence

Output:
LONG
SHORT
HOLD
"""

# LSTM MODEL
class LSTMModel(nn.Module):
    def __init__(self, input_size=5, hidden_size=128, output_size=3):
        super().__init__()
        self.lstm = nn.LSTM( input_size=input_size, hidden_size=hidden_size, num_layers=2, batch_first=True, dropout=0.3)
        self.dropout = nn.Dropout(0.3)
        self.fc = nn.Linear(hidden_size, output_size)
        
    def forward(self, x):
        output, _ = self.lstm(x)
        last = output[:, -1, :]
        last = self.dropout(last)
        result = self.fc(last)
        return result
    
        # TRANSFORMER MODEL
class TransformerModel(nn.Module):
    def __init__(self, input_size=5, d_model=64, heads=4, layers=3, output_size=3):
        super().__init__()
        
        # Converting OHLCV to embedding
        self.input_projection = nn.Linear( input_size, d_model)
        encoder_layer = nn.TransformerEncoderLayer(d_model=d_model, nhead=heads, dim_feedforward=256, dropout=0.2, batch_first=True)
        self.transformer = nn.TransformerEncoder(encoder_layer, num_layers=layers)
        self.dropout = nn.Dropout(0.2)
        self.fc = nn.Linear(d_model, output_size)
        
    def forward(self, x):
        # [batch, sequence, features]
        x = self.input_projection(x)
        x = self.transformer(x)
        
        # Last Candle
        x = x[:, -1, :]
        x = self.dropout(x)
        output = self.fc(x)
        return output
    
        # AI MODEL WRAPPER
class AIModel:
    def __init__(self, model_type="lstm"):
        if model_type == "transformer":
            self.model = TransformerModel()
        else:
            self.model = LSTMModel()
        self.model.eval()
    def predict(self, features):
        tensor = torch.tensor(features, dtype=torch.float32)
        tensor = tensor.unsqueeze(0)
        with torch.no_grad():
            output = self.model(tensor)
            probability = torch.softmax(output, dim=1)
        confidence, index = torch.max(probability, dim=1)
        labels = ["LONG", "SHORT", "HOLD"]
        
        return {"signal": labels[index.item()],
            "confidence": confidence.item(),
            "probability":{"LONG": probability[0][0].item(),
                "SHORT": probability[0][1].item(),
                "HOLD": probability[0][2].item()}}
        
        
        
        
        
        
        
        
        
        
        
# PREDICTORY
"""
AI Prediction Controller

Responsible for:
- Loading AI model
- Preparing market features
- Generating signal
"""

class Predictor:
    def __init__(self):
        self.model = AIModel(model_type = CONFIG.get("model_type", "lstm"))
        self.load_model()
        
    def load_model(self):
        try:
            self.model.model.load_state_dict(
                torch.load(CONFIG.get("model_path", "model.pth"),
                    weights_only=True))
            print("AI model loaded")
        except Exception:
            print("No trained model found - using fresh model")
            
    def prepare_features(self, candles):
        features = []
        
        for candle in candles:
            features.append([
                candle["open"],
                candle["high"],
                candle["low"],
                candle["close"],
                candle["volume"]])
            
        return np.array(features, dtype=np.float32)
        
    def run(self, candles):
        features = self.prepare_features(candles)
        prediction = self.model.predict(features)
        return prediction
    
    
    
    
    
    
    
#DATASET 
"""
AI Trading Dataset
Creates training samples
from market history
"""
class TradingDataset(Dataset):
    def __init__(self, candles, sequence_length=100, future_window=5):
        self.samples = []
        self.labels = []
        
        for i in range(len(candles)- sequence_length - future_window):
            history = candles[i: i + sequence_length]
            current_price = candles[i + sequence_length]["close"]
            future_price = candles[i + sequence_length + future_window]["close"]
            features = []
            
            for candle in history:
                features.append([candle["open"], candle["high"], candle["low"], candle["close"], candle["volume"]])                
            change = (future_price - current_price) / current_price
            
            if change > 0.002: label = 0     # Labels
            elif change < -0.002: label = 1     # LONG
            else:       # SHORT
                label = 2
                
            self.samples.append(features)       # HOLD
            self.labels.append(label)
            
    def __len__(self):
        return len(self.samples)
        
    def __getitem__(self, index):
        return (torch.tensor(self.samples[index], dtype=torch.float32),
            torch.tensor(self.labels[index], dtype=torch.long))      
        
        
        
        
        
        
# TRAIN
"""
AI Model Training
Train LSTM using market data
"""
def train(candles):
    dataset = TradingDataset(candles)
    loader = DataLoader(dataset, batch_size=32, shuffle=True)
    model = LSTMModel()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.001)
    loss_function = torch.nn.CrossEntropyLoss()
    epochs = 50
    
    for epoch in range(epochs):
        total_loss = 0
        for x,y in loader:
            optimizer.zero_grad()
            output = model(x)
            loss = loss_function(output, y)
            loss.backward()
            optimizer.step()
            total_loss += loss.item()
        print(f"Epoch {epoch+1} Loss {total_loss}")
    torch.save(model.state_dict(),"model.pth")
    print("AI Model Saved")
        
        
        
        
        
        
# ENGINE    
"""
Main AI Trading Engine
"""
class TradingEngine:
    def __init__(self):
        self.market = MarketData()
        self.predictor = Predictor()
    
    def run_cycle(self):
        try:data = self.market.get_data(CONFIG["symbol"], CONFIG["timeframe"])
        
        except Exception as error:
            print(f"Market Data Error: {error}")
            
            return None
        CONFIG["symbol"], CONFIG["timeframe"]
        prediction = self.predictor.run( data)
        
        if prediction["confidence"] < CONFIG["min_confidence"]:
            return None
    
        signal = Signal(symbol=CONFIG["symbol"],
            direction=prediction["direction"],
            confidence=prediction["confidence"],
            model="default_ai")
        return signal
    
    
    
    
#API    
"""
Signal API Controller
"""
engine = TradingEngine()
def get_signal():
    result = engine.run_cycle()
    
    if result is None:
        return {"status": "no_signal"}
    return {"status":"success",
        "data":result.json()}
    
    
    
    
    
# SERVER    
"""
FastAPI Signal Server
"""
app = FastAPI(title="AI Trading Signal Engine",
    version="1.0")

@app.get("/")
def home():
    return {"name": "AI Trading Signal Engine",
        "status": "running"}
    
@app.get("/signal")
def signal():
    return get_signal()
    
    
    
    
    
    
    
# LOGGER    
"""
Simple Logger
"""
def log(message):
    print(f"[ENGINE] {message}")
    
    
    
    
    
    
# MAIN
"""
AI Trading Signal Engine Entry Point
"""
engine = TradingEngine()

def start():
    log("AI Signal Engine Started")
    while True:
        result = engine.run_cycle()
        if result:
            log(result)
        else:
            log("No valid signal")
        time.sleep(CONFIG["loop_delay"])
        
if __name__ == "__main__":
    start()
    
    