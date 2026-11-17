import os
import sys
from pathlib import Path
from typing import List, Optional
from pydantic import Field, ValidationError
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv

# Search for backend/.env or root .env
BASE_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = BASE_DIR.parent

backend_env = BASE_DIR / ".env"
root_env = ROOT_DIR / ".env"

if backend_env.exists():
    load_dotenv(dotenv_path=backend_env)
elif root_env.exists():
    load_dotenv(dotenv_path=root_env)
else:
    load_dotenv()


class Settings(BaseSettings):
    """
    Centralized Pulse Bridge Application Settings.
    Strictly validates required environment variables at application startup.
    """
    # Application Mode
    ENVIRONMENT: str = Field(default="development")
    PORT: int = Field(default=8000)
    HOST: str = Field(default="0.0.0.0")
    CORS_ORIGINS: str = Field(default="http://localhost:3000,http://127.0.0.1:3000")

    # Supabase Configuration (Mandatory Single Source of Truth)
    SUPABASE_URL: str = Field(
        default="",
        description="Supabase Project URL, e.g. https://your-project.supabase.co"
    )
    SUPABASE_ANON_KEY: str = Field(
        default="",
        description="Supabase Public Anonymous Key"
    )
    SUPABASE_SERVICE_ROLE_KEY: str = Field(
        default="",
        description="Supabase Service Role Secret Key (Backend Only)"
    )

    # AI & Vision Providers
    GEMINI_API_KEY: str = Field(
        default="",
        description="Google Gemini API Key for Multimodal Document AI and Embeddings"
    )
    NVIDIA_NIMS_API_KEY: str = Field(
        default="",
        description="NVIDIA NIM API key used by the doctor assistant RAG chatbot"
    )
    NVIDIA_NIMS_CHAT_MODEL: str = Field(
        default="deepseek-ai/deepseek-v4.1-flash",
        description="Model identifier for NVIDIA NIM doctor assistant chat"
    )
    OPENROUTER_API_KEY: Optional[str] = Field(
        default=None,
        description="Optional OpenRouter API Key for backup model inference"
    )
    OPENROUTER_CHAT_MODEL: str = Field(
        default="meta-llama/llama-3.1-8b-instruct:free",
        description="Model identifier for OpenRouter doctor assistant chat"
    )

    # Model identifiers
    # NOTE: gemini-1.5-* and text-embedding-004 are retired. Override any of these in
    # backend/.env (e.g. GEMINI_CHAT_MODEL=...) if Google renames/retires a model again.
    GEMINI_VISION_MODEL: str = Field(default="gemini-3.1-flash-lite")
    GEMINI_CHAT_MODEL: str = Field(default="gemini-3.1-flash-lite")
    GEMINI_EMBEDDING_MODEL: str = Field(default="gemini-embedding-001")
    # Must match vector(N) in supabase/migrations/02_doctors_and_pgvector.sql
    EMBEDDING_DIM: int = Field(default=768)
    # Minimum cosine similarity for a doctor to count as a semantic match
    SEMANTIC_MATCH_THRESHOLD: float = Field(default=0.45)

    # Storage Bucket Name
    STORAGE_BUCKET_REPORTS: str = Field(default="medical_reports")

    model_config = SettingsConfigDict(
        env_file=str(backend_env if backend_env.exists() else root_env),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def cors_origin_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def validate_runtime_credentials(self) -> List[str]:
        """
        Validates required runtime credentials.
        Returns a list of missing configuration warnings or errors.
        """
        missing = []
        if not self.SUPABASE_URL or "your-project" in self.SUPABASE_URL:
            missing.append("SUPABASE_URL (Set your Supabase Project URL in backend/.env)")
        if not self.SUPABASE_ANON_KEY or "your-supabase" in self.SUPABASE_ANON_KEY:
            missing.append("SUPABASE_ANON_KEY (Set your Supabase Anon Key in backend/.env)")
        if not self.SUPABASE_SERVICE_ROLE_KEY or "your-supabase" in self.SUPABASE_SERVICE_ROLE_KEY:
            missing.append("SUPABASE_SERVICE_ROLE_KEY (Set your Supabase Service Role Secret in backend/.env)")
        if not self.GEMINI_API_KEY or "your-gemini" in self.GEMINI_API_KEY:
            missing.append("GEMINI_API_KEY (Set your Google Gemini API Key in backend/.env)")
        if not self.NVIDIA_NIMS_API_KEY or "nvapi-" not in self.NVIDIA_NIMS_API_KEY.lower():
            missing.append("NVIDIA_NIMS_API_KEY (Set your NVIDIA NIM API Key in backend/.env)")
        return missing


# Global singleton instance
settings = Settings()


def verify_configuration_or_warn():
    """
    Called on application boot. If required credentials are missing, prints
    prominent configuration diagnostics without silent crash or fake mock disguise.
    """
    errors = settings.validate_runtime_credentials()
    if errors:
        print("\n" + "=" * 78, file=sys.stderr)
        print("[WARN] PULSE BRIDGE - CONFIGURATION NOTICE", file=sys.stderr)
        print("=" * 78, file=sys.stderr)
        print("The following mandatory environment variables are not yet configured:", file=sys.stderr)
        for err in errors:
            print(f"  - {err}", file=sys.stderr)
        print("\nPlease update backend/.env with your actual Supabase, Gemini, and NVIDIA credentials.", file=sys.stderr)
        print("=" * 78 + "\n", file=sys.stderr)
    else:
        print("[OK] PULSE BRIDGE - Environment credentials verified successfully.")
