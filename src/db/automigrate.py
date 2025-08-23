src/db/automigrate.py
import subprocess
from ..utils.settings import settings

def run_migrations():
    if str(settings.auto_migrate) != "1":
        return
    subprocess.check_call(["alembic", "upgrade", "head"])