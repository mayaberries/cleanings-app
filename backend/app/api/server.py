from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.core import config, tasks
from app.core.limiter import key_limiter
from app.api.routes import router as api_router


def get_application():
    app = FastAPI(title=config.PROJECT_NAME, version=config.VERSION)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    app.add_event_handler("startup", tasks.create_start_app_handler(app))
    app.add_event_handler("shutdown", tasks.create_stop_app_handler(app))

    # Required by slowapi's default exception handler to compute
    # Retry-After. Only one Limiter instance can occupy this slot; key_limiter
    # is used here since it's the primary/expected-traffic limiter. This
    # does NOT mean ip_limiter's limits go unenforced -- both limiters'
    # @limit(...) decorators independently raise RateLimitExceeded, and
    # this single handler formats the 429 response for either of them.
    app.state.limiter = key_limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    app.include_router(api_router, prefix="/api")

    return app


app = get_application()