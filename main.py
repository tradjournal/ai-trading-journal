from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from passlib.context import CryptContext
from pydantic import BaseModel
import google.generativeai as genai
import os

# १. तुमची API KEY आणि AI कॉन्फिगरेशन
genai.configure(api_key="AIzaSyDMLlj5P6PMYaTxoSoL6urtovMgpnJTRKE")
model = genai.GenerativeModel('gemini-1.5-flash')

# २. डेटाबेस सेटअप (SaaS Level)
SQLALCHEMY_DATABASE_URL = "sqlite:///./onefeb_investment.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# ३. डेटाबेस मॉडेल्स
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

class Trade(Base):
    __tablename__ = "trades"
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String)
    profit = Column(Float)
    action = Column(String) # BUY/SELL
    volume = Column(Float)
    user_id = Column(Integer, ForeignKey("users.id"))

class CopyRelation(Base):
    __tablename__ = "copy_relations"
    id = Column(Integer, primary_key=True)
    master_id = Column(Integer, ForeignKey("users.id"))
    follower_id = Column(Integer, ForeignKey("users.id"))

Base.metadata.create_all(bind=engine)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
app = FastAPI()

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# ४. Schemas
class UserAuth(BaseModel):
    username: str
    password: str

class TradeCreate(BaseModel):
    username: str
    symbol: str
    profit: float
    action: str
    volume: float

# ५. AI ॲनालिसिस सिस्टीम
@app.get("/get_ai_mentor/{username}")
def get_ai_mentor(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    user_trades = db.query(Trade).filter(Trade.user_id == user.id).all()
    
    if not user_trades:
        return {"advice": "तुमचा पहिला ट्रेड रेकॉर्ड करा, मग मी तुम्हाला सल्ला देऊ शकेन."}
    
    # AI साठी डेटा तयार करणे
    summary = str([f"{t.symbol} {t.action}: {t.profit}" for t in user_trades[-5:]]) # शेवटचे ५ ट्रेड्स
    prompt = f"मी हे ट्रेड्स केले आहेत: {summary}. एक प्रोफेशनल ट्रेडिंग मेंटॉर म्हणून माझे रिस्क मॅनेजमेंट तपासा आणि मला सुधारण्यासाठी मराठीत ३ प्रभावी टिप्स द्या."
    
    response = model.generate_content(prompt)
    return {"advice": response.text}

# ६. मुख्य ऑपरेशन्स
@app.get("/")
async def serve_home():
    return FileResponse('index.html')

@app.post("/register")
def register(user: UserAuth):
    db = SessionLocal()
    hashed = pwd_context.hash(user.password)
    new_user = User(username=user.username, hashed_password=hashed)
    db.add(new_user)
    db.commit()
    return {"status": "Success"}

@app.post("/sync_trade")
def sync_trade(trade: TradeCreate):
    db = SessionLocal()
    user = db.query(User).filter(User.username == trade.username).first()
    
    # ट्रेड सेव्ह करणे
    new_trade = Trade(symbol=trade.symbol, profit=trade.profit, action=trade.action, volume=trade.volume, user_id=user.id)
    db.add(new_trade)
    
    # कॉपी ट्रेडिंग (Beta): या मास्टरच्या फॉलोअर्सना ट्रेड पाठवणे
    followers = db.query(CopyRelation).filter(CopyRelation.master_id == user.id).all()
    for f in followers:
        # फॉलोअरच्या अकाउंटमध्ये ही ऑर्डर 'Execution' साठी टाका
        pass 
    
    db.commit()
    return {"status": "Trade Synced with OneFeb AI"}

@app.get("/history/{username}")
def history(username: str):
    db = SessionLocal()
    user = db.query(User).filter(User.username == username).first()
    return db.query(Trade).filter(Trade.user_id == user.id).all()