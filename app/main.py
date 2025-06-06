from fastapi import FastAPI, Depends, Request, HTTPException
from fastapi.responses import JSONResponse
from app.api.documents import router as documents_router
from app.api.users import router as users_router
from app.core.auth import get_current_user
import logging

app = FastAPI(title="IngeXai Document Connector")

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s"
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger = logging.getLogger("ingexai")
    logger.info(f"Request: {request.method} {request.url}")
    response = await call_next(request)
    logger.info(f"Response status: {response.status_code}")
    return response


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logging.error(f"Unhandled error: {exc}", exc_info=True)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    logging.warning(f"HTTP error: {exc.detail}")
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


# Protect all /documents endpoints with authentication
app.include_router(documents_router, dependencies=[Depends(get_current_user)])

# Add users_router without authentication dependency
app.include_router(users_router)
