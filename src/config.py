import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


_MODULE_PATH = Path(__file__).resolve().parent
load_dotenv(_MODULE_PATH / ".env", override=True)


@dataclass
class DatabaseSettings:
    dbname: str = field(default_factory=lambda: os.getenv("DB_NAME", ""))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", 5432)))

    def to_dict(self) -> dict:
        """Return connection params as a dictionary."""
        return {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": str(self.port)
        }