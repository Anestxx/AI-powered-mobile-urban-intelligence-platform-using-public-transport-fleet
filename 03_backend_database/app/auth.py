import secrets
import time
from fastapi import APIRouter, HTTPException, Request, Response
from .schemas import Login

router = APIRouter(prefix="/api/auth")
COOKIE = "codyssey_session"
SESSION_SECONDS = 8 * 60 * 60


def authenticated(request):
    token = request.cookies.get(COOKIE)
    expiry = request.app.state.sessions.get(token, 0)
    return expiry > time.time()


def require_operator(request: Request):
    if not authenticated(request):
        raise HTTPException(401, "Operator sign-in required")
    origin = request.headers.get("origin")
    if origin and origin not in request.app.state.settings.allowed_origins:
        raise HTTPException(403, "Origin is not allowed")


@router.post("/login")
def login(data: Login, request: Request, response: Response):
    now = time.time()
    address = request.client.host if request.client else "local"
    failures = [value for value in request.app.state.login_failures.get(address, []) if now - value < 60]
    if len(failures) >= 10:
        raise HTTPException(429, "Too many failed attempts; retry in a minute")
    if not secrets.compare_digest(data.password.encode("utf-8"), request.app.state.settings.operator_password.encode("utf-8")):
        request.app.state.login_failures[address] = failures + [now]
        raise HTTPException(401, "Incorrect operator password")
    request.app.state.login_failures.pop(address, None)
    request.app.state.sessions = {key: expiry for key, expiry in request.app.state.sessions.items() if expiry > now}
    token = secrets.token_urlsafe(32)
    request.app.state.sessions[token] = now + SESSION_SECONDS
    response.set_cookie(COOKIE, token, httponly=True, samesite="strict", secure=request.url.scheme == "https", max_age=SESSION_SECONDS, path="/api")
    return {"authenticated": True}


@router.get("/session")
def session(request: Request):
    return {"authenticated": authenticated(request)}


@router.post("/logout")
def logout(request: Request, response: Response):
    request.app.state.sessions.pop(request.cookies.get(COOKIE), None)
    response.delete_cookie(COOKIE, path="/api")
    return {"authenticated": False}
