import sys
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.core.config import settings, verify_configuration_or_warn
from backend.api.routes import router as api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup validation
    print("\n[INFO] Starting PULSE BRIDGE API Backend...")
    verify_configuration_or_warn()
    yield
    print("[INFO] Shutting down PULSE BRIDGE API Backend...")


app = FastAPI(
    title="PULSE BRIDGE Healthcare API",
    description=(
        "Next-generation AI-powered healthcare accessibility platform for Pakistan. "
        "Encompassing Medical Report Explanation (EN/UR), Emergency Blood Donor Matching, "
        "and Grounded Doctor Discovery using RAG."
    ),
    version="2.0.0",
    lifespan=lifespan
)

# Configure CORS for Next.js Frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list + ["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router)


@app.get("/", tags=["Root"])
def root():
    return {
        "service": "PULSE BRIDGE Healthcare API",
        "version": "2.0.0",
        "status": "ONLINE",
        "docs_url": "/docs"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.main:app", host=settings.HOST, port=settings.PORT, reload=True)
