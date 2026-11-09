"""
Web server for Boole reduction comparison.

Start:
    pip install -r requirements.txt
    python web/app.py

Then open http://127.0.0.1:8000
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from compare_runner import reduce_expression, compare_expression, list_cases

WEB_DIR = Path(__file__).resolve().parent
STATIC_DIR = WEB_DIR / "static"

app = FastAPI(
    title="Boole Reduction",
    description="Compare Algebra of Boole reduction implementations with timing.",
    version="1.0.0",
)


class CompareRequest(BaseModel):
    expression: str = Field(..., min_length=1, description="Logic expression")
    mode: str = Field(
        "compare",
        description="'reduce' = GF(2) only (fast); 'compare' = all implementations",
    )
    include_slow: bool = Field(True, description="Include legacy SymPy (compare mode only)")
    n_minimum: int = Field(50, ge=1, le=500, description="Partition chunk size")


class CompareCaseRequest(BaseModel):
    case_id: str
    include_slow: bool = True
    n_minimum: int = 50


class ReduceRequest(BaseModel):
    expression: str = Field(..., min_length=1, description="Logic expression")


@app.get("/")
async def index():
    index_path = STATIC_DIR / "index.html"
    if not index_path.exists():
        raise HTTPException(status_code=404, detail="Frontend not found")
    return FileResponse(index_path)


@app.get("/api/health")
async def api_health():
    return {"status": "ok"}


@app.get("/api/cases")
async def api_cases():
    return {"cases": list_cases()}


@app.post("/api/reduce")
async def api_reduce(body: ReduceRequest):
    """Alias for /api/compare with mode=reduce (backward compatible)."""
    expr = body.expression.strip()
    if not expr:
        raise HTTPException(status_code=400, detail="Expression cannot be empty")
    try:
        case = reduce_expression(expr, label="Custom expression")
        return case.to_dict()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/routes")
async def api_routes():
    return {
        "reduce": "POST /api/compare {\"expression\":\"...\", \"mode\":\"reduce\"}",
        "compare": "POST /api/compare {\"expression\":\"...\", \"mode\":\"compare\"}",
    }


@app.post("/api/compare")
async def api_compare(body: CompareRequest):
    expr = body.expression.strip()
    if not expr:
        raise HTTPException(status_code=400, detail="Expression cannot be empty")
    try:
        if body.mode == "reduce":
            case = reduce_expression(expr, label="Custom expression")
        else:
            case = compare_expression(
                expr,
                case_id="custom",
                label="Custom expression",
                n_minimum=body.n_minimum,
                include_slow=body.include_slow,
            )
        return case.to_dict()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/compare-case")
async def api_compare_case(body: CompareCaseRequest):
    cases = list_cases()
    match = next((c for c in cases if c["case_id"] == body.case_id), None)
    if not match:
        raise HTTPException(status_code=404, detail=f"Unknown case: {body.case_id}")
    try:
        case = compare_expression(
            match["expression"],
            case_id=match["case_id"],
            label=match["label"],
            n_minimum=body.n_minimum,
            include_slow=body.include_slow,
        )
        return case.to_dict()
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=400, detail=str(exc)) from exc


if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


def main() -> None:
    import uvicorn

    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", "11126"))
    print(f"Boole Reduction web app: http://{host}:{port}")
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
