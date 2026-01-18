from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
import google.generativeai as genai

# AI Configuration
genai.configure(api_key="AIzaSyDMLlj5P6PMYaTxoSoL6urtovMgpnJTRKE")
model = genai.GenerativeModel('gemini-1.5-flash')

# Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./trading_journal.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    entry_price = Column(Float)
    exit_price = Column(Float)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    profit_loss = Column(Float)
    reason = Column(String)
    date = Column(String) # YYYY-MM-DD format sathi

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class TradeCreate(BaseModel):
    symbol: str
    entry_price: float
    exit_price: float
    stop_loss: float
    take_profit: float
    reason: str

@app.get("/")
async def home():
    return FileResponse('index.html')

@app.post("/add_trade")
def add_trade(trade: TradeCreate):
    db = SessionLocal()
    pl = round(trade.exit_price - trade.entry_price, 2)
    today = datetime.now().strftime("%Y-%m-%d")
    
    new_trade = Trade(
        symbol=trade.symbol, entry_price=trade.entry_price, exit_price=trade.exit_price,
        stop_loss=trade.stop_loss, take_profit=trade.take_profit,
        profit_loss=pl, reason=trade.reason, date=today
    )
    db.add(new_trade)
    db.commit()
    return {"message": "Saved"}

@app.get("/history")
def history():
    db = SessionLocal()
    return db.query(Trade).all()

@app.get("/get_ai_advice")
def get_ai_advice():
    db = SessionLocal()
    trades = db.query(Trade).all()
    if not trades: return {"advice": "ट्रेड्स ॲड करा."}
    summary = str([f"{t.symbol}: {t.profit_loss}" for t in trades[-5:]])
    response = model.generate_content(f"माझे ट्रेड्स: {summary}. मराठीत सायकोलोजी सल्ला द्या.")
    return {"advice": response.text}