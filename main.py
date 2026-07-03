from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from starlette.routing import Match
from sqlalchemy import inspect, text
from app.config import settings
from app.database import engine, Base, SessionLocal
from app.routers import auth, users, applications, assignments
from app.routers import tenants
from app.llm_provider.router import router as llm_provider_router
from app.ai_generator.router import router as ai_generator_router
from app.auth.security import get_password_hash
from app.models.user import User, UserRole
from app.connectors.router import router as connectors_router

def ensure_userrole_enum():
    with engine.begin() as conn:
        result = conn.execute(
            text(
                "SELECT pg_enum.enumlabel "
                "FROM pg_enum "
                "JOIN pg_type ON pg_enum.enumtypid = pg_type.oid "
                "WHERE pg_type.typname = :enum_name "
                "ORDER BY pg_enum.enumsortorder"
            ),
            {"enum_name": "userrole"},
        ).all()

        existing_labels = [row[0] for row in result]
        role_names = [member.name for member in UserRole]

        if not existing_labels:
            formatted_values = ", ".join(f"'{name}'" for name in role_names)
            conn.execute(text(f"CREATE TYPE userrole AS ENUM ({formatted_values})"))
            print("Created missing Postgres enum type 'userrole'.")
            return

        missing_values = [name for name in role_names if name not in existing_labels]
        for value in missing_values:
            conn.execute(text(f"ALTER TYPE userrole ADD VALUE '{value}'"))
            print(f"Added missing enum value '{value}' to Postgres type 'userrole'.")


ensure_userrole_enum()
Base.metadata.create_all(bind=engine)


def ensure_db_schema():
    inspector = inspect(engine)
    if "users" in inspector.get_table_names():
        user_columns = [column["name"] for column in inspector.get_columns("users")]
        if "tenant_id" not in user_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE users ADD COLUMN tenant_id INTEGER"))
    
    if "applications" in inspector.get_table_names():
        app_columns = [column["name"] for column in inspector.get_columns("applications")]
        if "tenant_id" not in app_columns:
            with engine.begin() as conn:
                conn.execute(text("ALTER TABLE applications ADD COLUMN tenant_id INTEGER"))
                print("Added tenant_id column to applications table")


ensure_db_schema()

app = FastAPI(
    title="PromptXL Enterprise",
    description="Multi-Tenant App Access Management Platform",
    version="1.0.0",
    redirect_slashes=False
)


def _path_matches(scope) -> bool:
    """Return True if the given ASGI scope matches a registered route."""
    for route in app.router.routes:
        match, _ = route.matches(scope)
        if match == Match.FULL:
            return True
    return False


@app.middleware("http")
async def flexible_trailing_slash(request: Request, call_next):
    """Accept requests with or without a trailing slash without issuing a
    cross-origin redirect (which would drop the Authorization header)."""
    scope = request.scope
    path = scope["path"]
    if not _path_matches(scope):
        toggled = path[:-1] if path.endswith("/") and len(path) > 1 else path + "/"
        probe = dict(scope)
        probe["path"] = toggled
        if _path_matches(probe):
            scope["path"] = toggled
    return await call_next(request)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vue dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def create_default_superadmin():
    if not settings.SUPERADMIN_EMAIL or not settings.SUPERADMIN_PASSWORD:
        print("Skipping default superadmin creation; SUPERADMIN_EMAIL or SUPERADMIN_PASSWORD is not set.")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter(User.role == UserRole.SUPERADMIN).first()
        if existing:
            print("Default superadmin already exists.")
            return

        db_user = User(
            email=settings.SUPERADMIN_EMAIL,
            hashed_password=get_password_hash(settings.SUPERADMIN_PASSWORD),
            full_name=settings.SUPERADMIN_FULL_NAME,
            role=UserRole.SUPERADMIN,
            is_active=True
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        print(f"Created default superadmin: {settings.SUPERADMIN_EMAIL}")
    finally:
        db.close()

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(applications.router, prefix="/api/applications", tags=["Applications"])
app.include_router(assignments.router, prefix="/api/assignments", tags=["Assignments"])
app.include_router(tenants.router, prefix="/api/tenants", tags=["Tenants"])
app.include_router(llm_provider_router, prefix="/api/llm-providers", tags=["LLM Providers"])
app.include_router(ai_generator_router, prefix="/api/ai-generator", tags=["AI Generator"])
app.include_router(connectors_router, prefix="/api/connectors",tags=["connectors"])
@app.get("/")
def root():
    return {"message": "PromptXL Enterprise API", "version": "1.0.0"}

@app.get("/health")
def health_check():
    return {"status": "healthy"}


