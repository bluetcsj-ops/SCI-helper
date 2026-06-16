import os
from dataclasses import dataclass

from dotenv import load_dotenv


load_dotenv()


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("APP_NAME", "Radiation Therapy SCI Workshop API")
    app_version: str = os.getenv("APP_VERSION", "0.1.0")
    app_env: str = os.getenv("APP_ENV", "development")
    database_url: str = os.getenv("DATABASE_URL", "sqlite:///./sci_workshop.db")
    llm_provider: str = os.getenv("LLM_PROVIDER", "deepseek")
    deepseek_api_key: str | None = os.getenv("DEEPSEEK_API_KEY")
    deepseek_base_url: str = os.getenv("DEEPSEEK_BASE_URL", "https://api.deepseek.com")
    deepseek_model: str = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-pro")
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o")
    mentor_evidence_provider: str = os.getenv("MENTOR_EVIDENCE_PROVIDER", "local")
    pubmed_base_url: str = os.getenv(
        "PUBMED_BASE_URL",
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils",
    )
    pubmed_api_key: str | None = os.getenv("PUBMED_API_KEY")
    pubmed_email: str | None = os.getenv("PUBMED_EMAIL")
    mentor_pubmed_retmax: int = int(os.getenv("MENTOR_PUBMED_RETMAX", "3"))
    mentor_evidence_timeout_seconds: float = float(
        os.getenv("MENTOR_EVIDENCE_TIMEOUT_SECONDS", "6"),
    )
    cors_origins: list[str] = None

    def __post_init__(self) -> None:
        origins = os.getenv(
            "CORS_ORIGINS",
            "http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173",
        )
        object.__setattr__(self, "cors_origins", _split_csv(origins))


settings = Settings()
