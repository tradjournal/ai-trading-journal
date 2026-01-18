from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
import google.generativeai as genai
import os

app = FastAPI()

# CORS सेटिंग (तुमच्या डोमेनवरून ॲप एक्सेस करण्यासाठी आवश्यक)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# तुमची API Key (Render वर सुरक्षित ठेवणे चांगले, पण सध्या कोडिंगमध्ये)
genai.configure(api_key="AIzaSyA4MVsPp8EB4uVFRcIe0uoOmqnDry_OrK0") # तुमची खरी की इथे टाका

# डेटा स्टोअर करण्यासाठी तात्पुरती लिस्ट (Data Persistence साठी भविष्यात Database वापरू)
trades = []

class Trade(BaseModel):
    symbol: str
    profit: float
    reason: str

# १. होम पेजसाठी रूट (हेच तुमचे index.html उघडेल)
@app.get("/")
async def read_index():
    return FileResponse('index.html')

# २. नवीन ट्रेड सेव्ह करण्यासाठी
@app.post("/add_trade")
async def add_trade(trade: Trade):
    trades.append(trade)
    return {"message": "Trade saved successfully"}

# ३. सर्व ट्रेड्स पाहण्यासाठी
@app.get("/get_trades")
async def get_trades():
    return trades

# ४. AI एनालिसिस करण्यासाठी
@app.get("/get_ai_analysis")
async def get_ai_analysis():
    if not trades:
        return {"advice": "कृपया आधी काही ट्रेड्स ॲड करा."}
    
    # AI साठी प्रॉम्ट तयार करणे
    trade_summary = str([f"{t.symbol}: {t.profit} ({t.reason})" for t in trades])
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content(f"मी हे ट्रेड्स केले आहेत: {trade_summary}. माझे रिस्क मॅनेजमेंट आणि सायकॉलॉजी कशी आहे ते सांगा आणि मला सुधारण्यासाठी मराठीत सल्ला द्या.")
    
    return {"advice": response.text}

if __name__ == "__main__":
    import uvicorn
    # Render साठी पोर्ट १०००० वापरणे अनिवार्य आहे
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)