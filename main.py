"""
LanceGuardAI — API (public waitlist + admin)
Run: uvicorn main:app --reload --port 8000
"""
import csv
import io
import os
import secrets

from dotenv import load_dotenv

load_dotenv()

from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from auth import create_token, require_admin
from database import (
    get_all,
    get_all_for_export,
    get_count,
    get_stats,
    init_db,
    insert_signup,
)
from email_service import send_welcome_email
from models import (
    CountResponse,
    LoginRequest,
    SignupRequest,
    SignupResponse,
    StatsResponse,
    TokenResponse,
    WaitlistEntry,
    WaitlistListResponse,
)

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "admin@123")
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://localhost:5174").split(",")
]

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="LanceGuardAI API", version="1.0.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    init_db()
    print(f"✓ Database ready v6 (UTM tracking) | CORS origins: {ALLOWED_ORIGINS}")


# ── Public ────────────────────────────────────────────────────────────────────


@app.get("/api/waitlist/count", response_model=CountResponse)
def waitlist_count():
    return {"count": get_count()}


@app.post("/api/waitlist", response_model=SignupResponse)
@limiter.limit("5/minute")
async def join_waitlist(request: Request, body: SignupRequest):
    ip = request.client.host if request.client else "unknown"
    ua = request.headers.get("user-agent", "")

    position = insert_signup(
        email=body.email,
        name=body.name,
        source=body.source,
        freelance_type=body.freelance_type,
        pain_point=body.pain_point,
        current_tool=body.current_tool,
        ip=ip,
        user_agent=ua,
        utm_source=body.utm_source,
        utm_medium=body.utm_medium,
        utm_campaign=body.utm_campaign,
    )

    count = get_count()

    if position is None:
        return SignupResponse(position=count, count=count, already_registered=True)

    send_welcome_email(body.email, body.name, position)
    return SignupResponse(position=position, count=count)


# ── Admin auth ────────────────────────────────────────────────────────────────


@app.post("/api/admin/login", response_model=TokenResponse)
def admin_login(body: LoginRequest):
    ok = secrets.compare_digest(body.username, ADMIN_USERNAME) and \
         secrets.compare_digest(body.password, ADMIN_PASSWORD)
    if not ok:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    return {"token": create_token(body.username)}


# ── Admin data (JWT required) ─────────────────────────────────────────────────


@app.get("/api/admin/stats", response_model=StatsResponse)
def admin_stats(_: str = Depends(require_admin)):
    try:
        return get_stats()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/admin/waitlist", response_model=WaitlistListResponse)
def admin_waitlist(
    page: int = 1,
    per_page: int = 50,
    _: str = Depends(require_admin),
):
    rows, total = get_all(page=page, per_page=per_page)
    return WaitlistListResponse(
        entries=[WaitlistEntry(**r) for r in rows],
        total=total,
        page=page,
        per_page=per_page,
    )


@app.get("/api/admin/export")
def admin_export(_: str = Depends(require_admin)):
    rows = get_all_for_export()
    buf = io.StringIO()
    fields = ["id", "name", "email", "source", "freelance_type", "pain_point", "current_tool", "signed_up_at"]
    writer = csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    writer.writerows(rows)
    buf.seek(0)
    return StreamingResponse(
        iter([buf.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=waitlist.csv"},
    )
