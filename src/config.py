import os
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv


_MODULE_PATH = Path(__file__).resolve().parent
load_dotenv(_MODULE_PATH / ".env", override=True)


@dataclass
class DatabaseSettings:
    dbname: str
    user: str
    password: str
    host: str = "localhost"
    port: int = 5432

    def to_dict(self) -> dict:
        """Return connection params as a dictionary."""
        return {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": str(self.port)
        }

def load_db_settings() -> DatabaseSettings:
    """Loads environment variables for database settings."""
    return DatabaseSettings(
        dbname=os.getenv("DB_NAME", ""),
        user=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        host=os.getenv("DB_HOST", ""),
        port=int(os.getenv("DB_PORT", 5432)
                 )