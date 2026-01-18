from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()

# १. CORS सेटिंग (तुमच्या डोमेनवरून ॲप एक्सेस करण्यासाठी)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# २. तुमची Gemini API Key इथे टाका
genai.configure(api_key="AIzaSyA4MVsPp8EB4uVFRcIe0uoOmqnDry_OrK0") 

trades = []

class Trade(BaseModel):
    symbol: str
    profit: float
    reason: str

# ३. होम पेजसाठी रूट (Not Found एरर घालवण्यासाठी)
@app.get("/")
async def read_index():
    return FileResponse('index.html')

@app.post("/add_trade")
async def add_trade(trade: Trade):
    trades.append(trade)
    return {"message": "Trade saved successfully"}

@app.get("/get_trades")
async def get_trades():
    return trades

@app.get("/get_ai_analysis")
async def get_ai_analysis():
    if not trades:
        return {"advice": "कृपया आधी काही ट्रेड्स ॲड करा."}
    
    trade_summary = str([f"{t.symbol}: {t.profit} ({t.reason})" for t in trades])
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(f"मी हे ट्रेड्स केले आहेत: {trade_summary}. माझे रिस्क मॅनेजमेंट आणि सायकॉलॉजी कशी आहे ते सांगा आणि सुधारण्यासाठी मराठीत सल्ला द्या.")
    
    return {"advice": response.text}

if __name__ == "__main__":
    import uvicorn
    # Render साठी पोर्ट १०००० वापरणे आवश्यक आहे
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)