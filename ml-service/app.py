from fastapi import FastAPI, UploadFile, File

app = FastAPI()

@app.post("/analyze-document")
async def analyze_document(file: UploadFile = File(...)):

    return {
        "riskScore": 0.15,
        "decision": "LOW_RISK",
        "summary": "Document appears authentic"
    }