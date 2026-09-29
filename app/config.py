"""Configuration settings for Meeting Prep Agent."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file if present
BASE_DIR = Path(__file__).resolve().parent.parent
env_path = BASE_DIR / ".env"
load_dotenv(dotenv_path=env_path)


class Settings:
    """Application settings and API credentials."""

    def __init__(self):
        self.groq_api_key: str = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model: str = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        
        self.hindsight_api_key: str = os.getenv("HINDSIGHT_API_KEY", "").strip()
        self.hindsight_bank_id: str = os.getenv("HINDSIGHT_BANK_ID", "meeting-prep-agent").strip()
        self.hindsight_api_url: str = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io").strip()
        
        # SQLite database path
        default_db = str(BASE_DIR / "data" / "meeting_prep.db")
        self.sqlite_db_path: str = os.getenv("SQLITE_DB_PATH", default_db).strip()

    @property
    def has_groq_key(self) -> bool:
        """Check if Groq API key is present and not a placeholder."""
        return bool(self.groq_api_key and "your_" not in self.groq_api_key.lower())

    @property
    def has_hindsight_key(self) -> bool:
        """Check if Hindsight API key is present and not a placeholder."""
        return bool(self.hindsight_api_key and "your_" not in self.hindsight_api_key.lower())

    def reload(self):
        """Reload configuration from environment."""
        load_dotenv(dotenv_path=env_path, override=True)
        self.groq_api_key = os.getenv("GROQ_API_KEY", "").strip()
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
        self.hindsight_api_key = os.getenv("HINDSIGHT_API_KEY", "").strip()
        self.hindsight_bank_id = os.getenv("HINDSIGHT_BANK_ID", "meeting-prep-agent").strip()
        self.hindsight_api_url = os.getenv("HINDSIGHT_API_URL", "https://api.hindsight.vectorize.io").strip()
        default_db = str(BASE_DIR / "data" / "meeting_prep.db")
        self.sqlite_db_path = os.getenv("SQLITE_DB_PATH", default_db).strip()


# Global singleton settings instance
settings = Settings()


def get_settings() -> Settings:
    """Return the global settings instance."""
    return settings
