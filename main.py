import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn
import sqlite3

app = FastAPI()

# ==========================================
# तुमची API KEY इथे टाका
# ==========================================
GOOGLE_API_KEY = "AIzaSyA4MVsPp8EB4uVFRcIe0uoOmqnDry_OrK0"  # <-- इथे तुमची तीच Key टाका

genai.configure(api_key=GOOGLE_API_KEY)
model = genai.GenerativeModel('gemini-2.5-flash-lite') # किंवा list मधील नाव

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- DATABASE SETUP (हे कोड आपोआप डेटाबेस बनवेल) ---
def init_db():
    conn = sqlite3.connect("trading_journal.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS trades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            symbol TEXT,
            profit REAL,
            reason TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db() # ॲप चालू होताना टेबल बनवणे

class Trade(BaseModel):
    symbol: str
    profit: float
    reason: str

@app.post("/add_trade")
def add_trade(trade: Trade):
    conn = sqlite3.connect("trading_journal.db")
    cursor = conn.cursor()
    cursor.execute("INSERT INTO trades (symbol, profit, reason) VALUES (?, ?, ?)", 
                   (trade.symbol, trade.profit, trade.reason))
    conn.commit()
    conn.close()
    return {"message": "Trade Database मध्ये सेव्ह झाला!"}

@app.get("/get_trades")
def get_trades():
    conn = sqlite3.connect("trading_journal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, profit, reason FROM trades")
    trades = cursor.fetchall() # सर्व डेटा आणणे
    conn.close()
    
    # डेटा लिस्ट स्वरूपात पाठवणे
    return [{"symbol": t[0], "profit": t[1], "reason": t[2]} for t in trades]

@app.get("/get_ai_analysis")
def analyze():
    conn = sqlite3.connect("trading_journal.db")
    cursor = conn.cursor()
    cursor.execute("SELECT symbol, profit, reason FROM trades")
    trades = cursor.fetchall()
    conn.close()

    if not trades:
        return {"advice": "डेटाबेस रिकामी आहे. पहिले काही ट्रेड्स ॲड करा."}
    
    total_profit = sum(t[1] for t in trades)
    
    # AI साठी प्रश्न
    trades_text = "\n".join([f"Symbol={t[0]}, P&L={t[1]}, Reason={t[2]}" for t in trades])
    
    prompt = f"""
    Acting as a strict Trading Coach, analyze these last trades:
    {trades_text}
    
    Total P&L: {total_profit}
    
    Give me advice in MARATHI (2 lines max) focusing on mistakes.
    """
    
    try:
        response = model.generate_content(prompt)
        advice = response.text
    except:
        advice = "AI Error. API Key तपासा."

    return {"total_profit": total_profit, "advice": advice}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=10000)