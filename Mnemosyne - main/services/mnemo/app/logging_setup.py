"""
Logging configuration for MnemosyneOS.
Prefers YAML-based dictConfig; falls back to programmatic RotatingFileHandler.
Respects APP_ENV and LOG_LEVEL, and writes to LOG_FILE (default under LOG_DIR).
"""
import os
import stat
import logging
import logging.config
from logging.handlers import RotatingFileHandler
from pathlib import Path
import yaml

from app.config import settings

LOGGER_NAME = "mnemosyneos"
DEFAULT_LOG_FILE = os.path.join(settings.LOG_DIR, "app.log")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5

def _env_log_level():
    # APP_ENV: production|development|test ; LOG_LEVEL overrides all
    env = (os.getenv("APP_ENV") or "production").lower()
    level = (os.getenv("LOG_LEVEL") or "").upper()
    if level in {"DEBUG","INFO","WARNING","ERROR","CRITICAL"}:
        return getattr(logging, level)
    return logging.DEBUG if env == "development" else logging.INFO

def _ensure_dir_permissions(path: str):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    try:
        # 0640 for file, 0750 for directory (best-effort)
        os.chmod(Path(path).parent, 0o750)
    except Exception:
        pass

def _try_load_yaml_config():
    """
    Load logging.yaml if present, injecting LOG_FILE and LOG_LEVEL from env/defaults.
    Returns True if applied.
    """
    candidates = [
        Path(__file__).resolve().parents[2] / "config" / "logging.yaml",  # mnemosyneos/config/logging.yaml
        Path("mnemosyneos/config/logging.yaml")
    ]
    for p in candidates:
        if p.exists():
            with p.open("r") as f:
                cfg = yaml.safe_load(f)
            # Inject values
            log_file = os.getenv("LOG_FILE", DEFAULT_LOG_FILE)
            lvl_name = logging.getLevelName(_env_log_level())
            # Walk handlers and set filename/level where applicable
            for hname, hcfg in (cfg.get("handlers") or {}).items():
                if hcfg.get("class","").endswith("RotatingFileHandler"):
                    hcfg["filename"] = log_file
                if "level" in hcfg:
                    hcfg["level"] = lvl_name
            # Root and named loggers
            for k in ["root", "loggers"]:
                node = cfg.get(k)
                if isinstance(node, dict):
                    if k == "root":
                        node["level"] = lvl_name
                    else:
                        for _, lc in node.items():
                            lc["level"] = lvl_name
            _ensure_dir_permissions(log_file)
            logging.config.dictConfig(cfg)
            return True
    return False

def setup_logger():
    """Set up logger via YAML if possible; otherwise programmatically."""
    if _try_load_yaml_config():
        return logging.getLogger(LOGGER_NAME)

    # Fallback: programmatic rotating file + console
    logger = logging.getLogger(LOGGER_NAME)
    logger.setLevel(_env_log_level())
    formatter = logging.Formatter(LOG_FORMAT)

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    logger.addHandler(console)

    try:
        log_file = os.getenv("LOG_FILE", DEFAULT_LOG_FILE)
        _ensure_dir_permissions(log_file)
        file_handler = RotatingFileHandler(log_file, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        # Restrict file perms (0640)
        try:
            os.chmod(log_file, 0o640)
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error setting up file logging: {e}. Falling back to console only.")

    return logger

def get_logger():
    """Get or create the logger instance"""
    logger = logging.getLogger(LOGGER_NAME)
    if not logger.handlers:
        logger = setup_logger()
    return logger