import uuid

from fastapi import FastAPI, Request

from app.api.lifespan import lifespan
from app.api.routers.query_router import query_router
from app.core.context import request_id_context_var

app = FastAPI(lifespan=lifespan)

app.include_router(query_router)


@app.middleware("http")
async def bind_request_id(request: Request, call_next):
    token = request_id_context_var.set(str(uuid.uuid4()))
    try:
        return await call_next(request)
    finally:
        request_id_context_var.reset(token)
