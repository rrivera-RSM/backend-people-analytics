from contextlib import asynccontextmanager
import os
from typing import AsyncGenerator

import uvicorn
from fastapi import APIRouter, Depends, FastAPI, Query, Request, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from app.api.v1.employees import employee_router
from app.api.v1.ona import ona_router
from app.api.v1.kpis import kpis_router
from app.api.v1.app_managers import app_managers_router
from app.api.v1.evaluations import router as evaluations_router
from app.api.v1.salary_offers import salary_offers_router
from app.api.v1.assistant import assistant_router

from app.auth import get_me, azure_scheme
from settings import Settings

settings = Settings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Load OpenID config on startup.
    """
    await azure_scheme.openid_config.load_config()
    yield


app = FastAPI(
    title="Analytics API",
    swagger_ui_oauth2_redirect_url="/oauth2-redirect",
    swagger_ui_init_oauth={
        "usePkceWithAuthorizationCodeGrant": True,
        "clientId": settings.OPENAPI_CLIENT_ID,
        "scopes": [
            "openid",
            "profile",
            f"api://{settings.APP_CLIENT_ID}/user_impersonation",
        ],
        "appName": "RSM Analytics",
    },
    lifespan=lifespan,
)

if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            str(origin) for origin in settings.BACKEND_CORS_ORIGINS
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# Protected Router: Requires Azure AD authentication
# All endpoints in this router will enforce security dependencies, requiring
# valid Azure AD tokens with the "user_impersonation" scope. Use this for
# endpoints that should only be accessible to authenticated users.
protected = APIRouter(
    dependencies=[Security(azure_scheme, scopes=["user_impersonation"])]
)

# Public Router: No authentication required
# Endpoints in this router are accessible without authentication. Use this for
# endpoints like health checks, redirects, or any other public operations.
public = APIRouter()


@public.get("/", include_in_schema=False)
async def root():
    """
    Root endpoint that redirects to API documentation.

    This endpoint serves as the entry point for the API. When accessed,
    it automatically redirects users to the interactive API documentation
    page provided by FastAPI's Swagger UI.

    Returns:
        RedirectResponse: A redirect response pointing to the Swagger UI
                        documentation interface at /docs endpoint.

    Note:
        - This endpoint is excluded from the OpenAPI schema
        to avoid duplication in the API documentation.
        - The hardcoded localhost URL assumes the application is running
        on the local machine at port 8000. Consider using environment
        variables or configuration for production deployments.
        - HTTP GET method is used as this is a read-only redirect operation.

    Example:
        Accessing GET / will automatically redirect the browser to
        http://localhost:8000/docs
    """
    return RedirectResponse(url="/docs")


@protected.get("/me", dependencies=[Depends(azure_scheme)])
async def me(
    request: Request,
    include_photo: bool = Query(False),
    size: str = Query("96x96"),
):
    # 1) Usuario desde fastapi-azure-auth
    user = request.state.user.model_dump()
    authorization = request.headers.get("authorization")
    return await get_me(user, authorization, include_photo, size)


# This combines all endpoints from both the public and protected routers into
# the main app. The order doesn't matter, routes from both routers are equally
# available.

app.include_router(public)
app.include_router(protected)
app.include_router(app_managers_router)
app.include_router(employee_router)
app.include_router(ona_router)
app.include_router(kpis_router)
app.include_router(evaluations_router)
app.include_router(salary_offers_router)
app.include_router(assistant_router)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=os.getenv("HOST", "localhost"),
        port=int(os.getenv("PORT", "8000")),
        log_level=os.getenv("LOG_LEVEL", "debug"),
        reload=False,
    )
