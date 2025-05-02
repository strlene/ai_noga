
from fastapi.responses import JSONResponse
from fastapi.requests import Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI, HTTPException

from handler.handle_sumary import summarize_food_labels
from handler.handle_validate_summary import validate_fix_typo_labels
from schema.schema import AnalyzeValidateResponse, AnalyzeRequest, MakeSummaryFoodRequest

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


@app.post("/summary_foods")
def summary_foods(req: MakeSummaryFoodRequest):
    try:
        data = {
            "ingredients": [ing.dict() for ing in req.ingredients],
            "nutrition_info": [nut.dict() for nut in req.nutrition_info],
        }
        result = summarize_food_labels(data)
        if result is None:
            raise HTTPException(status_code=204, detail="No content")
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/validate-fix-typo", response_model=AnalyzeValidateResponse)
def validate_fix_typo(req: AnalyzeRequest):
    try:
        data = {
            "ingredients": req.composition,
            "nutrition_info": req.nutrition_info
        }

        validated = validate_fix_typo_labels(data)

        if not validated:
            raise HTTPException(status_code=500, detail="Validation failed")

        return {
            "session_id": req.session_id,
            "result": validated
        }

    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

