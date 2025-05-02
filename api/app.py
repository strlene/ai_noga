
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from handler.ocr_handler import analyze_images
from schema.schema import AnalyzeResponse, AnalyzeRequest

SOURCES = {
    "nutrition_info": "http://localhost:3000/uploads/nutrition_info/nutrition_info-y6r718o4f8b.jpeg"
}


app = FastAPI(
    title="Food-Scanner OCR API",
    version="0.3.1",
    description="OCR + Gemini → Ingredients & Nutrition Facts (EN).",
)

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "status": exc.status_code,
            "error": exc.detail
        },
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello World"}


@app.post("/ocr-nutrition-info", response_model=AnalyzeResponse)
def analyze_default(req: AnalyzeRequest):
    try:
        sources = {
            "nutrition_info": str(req.nutrition_info),
        }
        return analyze_images(req.session_id, sources)
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

