# main.py  (the FastAPI service)
from fastapi import FastAPI, HTTPException
from src.geniesupport.schemas import ChatRequest, ChatResponse, HealthResponse, Source
from src.geniesupport.logging_config import setup_logging
from src.geniesupport.agent import handle_message

logger = setup_logging()
app = FastAPI(title="SupportGenie", version="1.0.0")

@app.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(status="ok")

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    try:
        r = handle_message(req.message, req.session_id)
    except Exception:
        logger.exception("chat failed")
        raise HTTPException(status_code=500, detail="internal error")
    logger.info("chat", extra={"latency_ms": r["latency_ms"], "escalated": r["escalated"],
                               "cost_usd": r["cost_usd"], "session": req.session_id})
    return ChatResponse(reply=r["reply"], escalated=r["escalated"], reason=r["reason"],
                        sources=[Source(**s) for s in r["sources"]],
                        latency_ms=r["latency_ms"], cost_usd=r["cost_usd"])