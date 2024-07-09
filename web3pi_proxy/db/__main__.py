import importlib
import os
from peewee import SqliteDatabase
from peewee_migrate import Router
from pathlib import Path

from web3pi_proxy.config import Config

if not os.path.exists(Config.STATE_STORAGE_FILE):
    os.makedirs(os.path.dirname(Config.STATE_STORAGE_FILE), exist_ok=True)

db = SqliteDatabase(Config.STATE_STORAGE_FILE)

migrations_dir = Path(__file__).parent / "migrations"
migration_router = Router(db, migrations_dir)
migration_router.run()


def create_migrations():
    from .models.__main__ import BaseModel
    models = set()
    models_dir = Path(__file__).parent / "models"
    for module_file in models_dir.rglob("*.py"):
        module_path = str(
            module_file.relative_to(models_dir.parent.parent.parent)
        )[:-3].replace("/", ".").removesuffix(".__init__")
        module = importlib.import_module(module_path)
        for v in (getattr(module, varname) for varname in dir(module)):
            if isinstance(v, type) and issubclass(v, BaseModel) and v is not BaseModel:
                models.add(v)

    migration_router.create(auto=list(models))
