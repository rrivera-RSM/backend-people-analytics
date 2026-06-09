import base64

import httpx
import msal
from fastapi import HTTPException
from fastapi_azure_auth import SingleTenantAzureAuthorizationCodeBearer

from settings import Settings

settings = Settings()
AUTHORITY = f"https://login.microsoftonline.com/{settings.TENANT_ID}"
GRAPH_SCOPES = ["https://graph.microsoft.com/.default"]

cca = msal.ConfidentialClientApplication(
    client_id=settings.APP_CLIENT_ID,
    client_credential=settings.APP_CLIENT_SECRET,
    authority=AUTHORITY,
)

azure_scheme = SingleTenantAzureAuthorizationCodeBearer(
    app_client_id=settings.APP_CLIENT_ID,
    tenant_id=settings.TENANT_ID,
    scopes=settings.SCOPES,
)


def acquire_graph_token_obo(user_access_token: str) -> str:
    # user_access_token = token que te llega del front para tu API
    # (Authorization: Bearer ...)
    result = cca.acquire_token_on_behalf_of(
        user_assertion=user_access_token, scopes=GRAPH_SCOPES
    )
    if "access_token" not in result:
        error = result.get("error")
        description = result.get("error_description")
        raise RuntimeError(
            f"OBO failed: {error} - {description}"
        )
    return result["access_token"]


def extract_bearer_token(authorization: str) -> str:
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(status_code=401, detail="Missing Bearer token")
    return authorization.split(" ", 1)[1].strip()


async def get_me(
    user: dict, authorization: str, include_photo: bool, size: str
):

    user_basic_info = {
        "displayName": user.get("name"),
        "userPrincipalName": user.get("preferred_username"),
        "oid": user.get("oid"),
        "roles": user.get("roles", []),
    }

    # 2) Si no quieres foto embebida, devuelves solo JSON
    if not include_photo:
        return user_basic_info

    # 3) Si quieres foto embebida, lees access token del header (NO query)
    user_access_token = extract_bearer_token(authorization)

    # 4) OBO => token de Graph
    try:
        graph_token = acquire_graph_token_obo(user_access_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # 5) Llamada a Graph (foto)
    photo_url = (
        f"https://graph.microsoft.com/v1.0/me/photos/{size}/$value".format(
            size=size
        )
    )
    headers = {"Authorization": f"Bearer {graph_token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(photo_url, headers=headers)

    if r.status_code == 404:
        user_basic_info["photo"] = None
        return user_basic_info

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    content_type = r.headers.get("content-type", "image/jpeg")
    photo_b64 = base64.b64encode(r.content).decode("utf-8")

    user_basic_info["photo"] = {
        "contentType": content_type,
        "base64": photo_b64,
    }

    return user_basic_info


async def graph_get_user_photo_by_oid(
    oid: str, authorization: str, size: str
) -> dict:
    # 1) Extraer token del header
    user_access_token = extract_bearer_token(authorization)

    # 2) OBO => token de Graph
    try:
        graph_token = acquire_graph_token_obo(user_access_token)
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))

    # 3) Llamada a Graph (foto)
    photo_url = (
        f"https://graph.microsoft.com/v1.0/users/{oid}/photos/{size}/$value"
    )
    headers = {"Authorization": f"Bearer {graph_token}"}

    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(photo_url, headers=headers)

    if r.status_code == 404:
        return None

    if r.status_code != 200:
        raise HTTPException(status_code=r.status_code, detail=r.text)

    content_type = r.headers.get("content-type", "image/jpeg")
    photo_bytes = r.content

    return {
       "photo": {
            "contentType": content_type,
            "bytes": photo_bytes,
        }
    }
