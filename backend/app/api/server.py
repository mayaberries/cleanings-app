from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from app.core import config, tasks
from app.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    start_app = tasks.create_start_app_handler(app)
    stop_app = tasks.create_stop_app_handler(app)
    await start_app()
    yield
    await stop_app()


def get_application():
    app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.include_router(api_router, prefix="/api")

    return app


app = get_application()
