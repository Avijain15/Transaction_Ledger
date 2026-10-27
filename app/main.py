import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.db import create_tables
from app.errors import AppError, error_body
from app.routers import accounts, transactions, transfers


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(application: FastAPI) -> AsyncIterator[None]:
    create_tables()
    yield


app = FastAPI(title="Transaction Ledger API", lifespan=lifespan)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(transfers.router)
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.exception_handler(AppError)
def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=jsonable_encoder(error_body(exc.code, exc.message, exc.details)),
    )


@app.exception_handler(RequestValidationError)
def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors = exc.errors()
    is_pagination = any(
        error.get("loc", (None,))[0] == "query"
        and len(error.get("loc", ())) > 1
        and error["loc"][1] in ("page", "limit")
        for error in errors
    )
    code = "INVALID_PAGINATION" if is_pagination else "VALIDATION_ERROR"
    message = "Invalid pagination parameters" if is_pagination else "Request validation failed"
    details: list[dict[str, Any]] = [
        {key: error[key] for key in ("loc", "msg", "type") if key in error}
        for error in errors
    ]
    return JSONResponse(
        status_code=400,
        content=jsonable_encoder(error_body(code, message, details)),
    )


@app.exception_handler(StarletteHTTPException)
def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    codes = {404: "NOT_FOUND", 405: "METHOD_NOT_ALLOWED"}
    code = codes.get(exc.status_code, "HTTP_ERROR")
    message = str(exc.detail) if exc.detail else "Request could not be completed"
    return JSONResponse(status_code=exc.status_code, content=error_body(code, message))


@app.exception_handler(Exception)
def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unexpected API failure", exc_info=exc)
    return JSONResponse(
        status_code=500,
        content=error_body("INTERNAL_ERROR", "An unexpected error occurred"),
    )


@app.get("/", include_in_schema=False)
def frontend() -> FileResponse:
    return FileResponse(static_dir / "index.html")
