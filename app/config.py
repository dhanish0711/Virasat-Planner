import os
import sys
from pathlib import Path
from cryptography.fernet import Fernet

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
STORAGE_DIR = BASE_DIR / "storage"
VAULT_DIR = STORAGE_DIR / "encrypted_vault"

# Load local .env file if present
_env_file = BASE_DIR / ".env"
if _env_file.exists():
    try:
        with open(_env_file, "r", encoding="utf-8") as _f:
            for _line in _f:
                _line = _line.strip()
                if _line and not _line.startswith("#") and "=" in _line:
                    _k, _v = _line.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip().strip('"').strip("'"))
    except Exception:
        pass

DATA_DIR.mkdir(parents=True, exist_ok=True)
STORAGE_DIR.mkdir(parents=True, exist_ok=True)
VAULT_DIR.mkdir(parents=True, exist_ok=True)

ENVIRONMENT = os.getenv("ENVIRONMENT", "development").lower()

DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR / 'virasat.db'}")

# Secrets configuration
DEFAULT_DEV_SECRET = "virasat-planner-dev-session-secret-change-in-prod-2026"
SECRET_KEY = os.getenv("SECRET_KEY", DEFAULT_DEV_SECRET)

env_key = os.getenv("VAULT_SECRET_KEY")
KEY_FILE = DATA_DIR / "vault.key"

if ENVIRONMENT == "production":
    if not env_key:
        raise RuntimeError("CRITICAL CONFIGURATION ERROR: VAULT_SECRET_KEY must be set in production via environment variable.")
    if SECRET_KEY == DEFAULT_DEV_SECRET or len(SECRET_KEY) < 32:
        raise RuntimeError("CRITICAL CONFIGURATION ERROR: Insecure or default SECRET_KEY specified in production environment.")
    VAULT_ENCRYPTION_KEY = env_key.encode() if isinstance(env_key, str) else env_key
else:
    # Development / Testing fallback
    if env_key:
        VAULT_ENCRYPTION_KEY = env_key.encode() if isinstance(env_key, str) else env_key
    elif KEY_FILE.exists():
        VAULT_ENCRYPTION_KEY = KEY_FILE.read_bytes().strip()
    else:
        VAULT_ENCRYPTION_KEY = Fernet.generate_key()
        try:
            KEY_FILE.write_bytes(VAULT_ENCRYPTION_KEY)
        except Exception:
            pass

AUTH_TOKEN_EXPIRE_HOURS = int(os.getenv("AUTH_TOKEN_EXPIRE_HOURS", "24"))
VAULT_MAX_UPLOAD_BYTES = int(os.getenv("VAULT_MAX_UPLOAD_BYTES", 15 * 1024 * 1024))  # 15 MB
ALLOWED_VAULT_EXTENSIONS = {".pdf", ".jpg", ".jpeg", ".png", ".tiff", ".txt", ".doc", ".docx"}

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

APP_NAME = "वारिस (Waaris) - VirasatPlanner"
APP_VERSION = "2.1.0"
