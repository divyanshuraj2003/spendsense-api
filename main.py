from fastapi import FastAPI

app = FastAPI(title="SpendSense API", version="1.0")

@app.get("/")
def health_check():
    return {"status": "ok", "service": "SpendSense Backend running"}
