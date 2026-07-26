from signal import Signal
import numpy as np
from ai_model import AIModel
from predictor import Predictor
from market_data import MarketData
from engine import TradingEngine
from fastapi.testclient import TestClient
from server import app





# TESR SIGNAL
def test_signal_creation():
    signal = Signal(symbol="BTC/USDT",
        direction="LONG",
        confidence=0.90,
        model="ensemble",
        probability={"LONG":0.90, "SHORT":0.05, "HOLD":0.05})
    result = signal.json()
    assert result["symbol"] == "BTC/USDT"
    assert result["signal"] == "LONG"
    assert result["confidence"] == 0.90
    assert result["model"] == "ensemble"
    
    
# TEST AI MADEL
def test_lstm_prediction():
    model = AIModel("lstm")
    data = np.random.random((100,5))
    result = model.predict(data)
    assert "signal" in result
    assert "confidence" in result
    assert result["signal"] in ["LONG", "SHORT", "HOLD"]
    
def test_transformer_prediction():
    model = AIModel("transformer")
    data = np.random.random((100,5))
    result = model.predict(data)
    assert result["signal"] in ["LONG", "SHORT", "HOLD"]
    
#TEST PREDICTOR
def fake_candles():
    data=[]
    for i in range(100):
        data.append({"open":100+i,
            "high":105+i,
            "low":95+i,
            "close":102+i,
            "volume":1000})
    return data

def test_predictor():
    predictor = Predictor()
    result = predictor.run(fake_candles())
    assert "signal" in result
    assert "confidence" in result
    
# MARKET DATA
def test_market_data_format():
    market = MarketData()
    candles = [[1, 100, 105, 95, 102, 500]]
    result = market.format(candles)
    assert result[0]["close"] == 102
    assert result[0]["volume"] == 500
    
#ENGINE
def test_engine_creation():
    engine = TradingEngine()
    assert engine.market is not None
    assert engine.predictor is not None
    
#API
client = TestClient(app)

def test_home():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data