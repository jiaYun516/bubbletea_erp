"""
一鍵重建資料庫：  python reset_db.py
會【刪除】舊的 db.sqlite3 與 erp/migrations/，重新 makemigrations → migrate → seed。
"""
import os
import shutil
from pathlib import Path

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django  # noqa: E402

django.setup()

from django.core.management import call_command  # noqa: E402

BASE = Path(__file__).resolve().parent

(BASE / "db.sqlite3").unlink(missing_ok=True)
shutil.rmtree(BASE / "erp" / "migrations", ignore_errors=True)

call_command("makemigrations", "erp")
call_command("migrate")
call_command("seed")
