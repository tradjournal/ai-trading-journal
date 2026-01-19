from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic import BaseModel
from datetime import datetime
import google.generativeai as genai

# 1. AI Configuration
genai.configure(api_key="AIzaSyDMLlj5P6PMYaTxoSoL6urtovMgpnJTRKE")
model = genai.GenerativeModel('gemini-1.5-flash')

# 2. Database Setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./onefeb_v3.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class DetailedTrade(Base):
    __tablename__ = "detailed_trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    capital_used = Column(Float)
    entry_price = Column(Float)
    exits = Column(JSON)  # Multiple exit details
    total_pl = Column(Float)
    strategy = Column(String)
    date = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)
app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

class TradeIn(BaseModel):
    symbol: str
    capital: float
    entry: float
    exits: list
    strategy: str

@app.get("/")
async def serve_home():
    return FileResponse('index.html')

@app.post("/add_trade_v2")
def add_trade(data: TradeIn):
    db = SessionLocal()
    # P&L Calculation for Multiple Exits
    total_exit_val = sum([float(e['price']) * float(e['qty']) for e in data.exits])
    total_qty = sum([float(e['qty']) for e in data.exits])
    pl = total_exit_val - (data.entry * total_qty)
    
    new_trade = DetailedTrade(
        symbol=data.symbol, capital_used=data.capital, entry_price=data.entry,
        exits=data.exits, total_pl=round(pl, 2), strategy=data.strategy
    )
    db.add(new_trade)
    db.commit()
    return {"status": "Success", "pl": pl}

@app.get("/history_v2")
def get_history():
    db = SessionLocal()
    return db.query(DetailedTrade).order_by(DetailedTrade.date.desc()).all()

@app.get("/ai_mentor_advice")
def ai_advice():
    db = SessionLocal()
    trades = db.query(DetailedTrade).all()
    if not trades: return {"advice": "Trades add kara."}
    summary = str([f"{t.symbol}: {t.total_pl}" for t in trades[-5:]])
    response = model.generate_content(f"Maze trades: {summary}. Mazya trading psychology baddal Marathi madhe salla dya.")
    return {"advice": response.text}