"""Application configuration loaded from environment variables."""

import os
from dataclasses import dataclass, field
from pathlib import Path
from dotenv import load_dotenv


_ROOT_PATH = Path(__file__).resolve().parent.parent
load_dotenv(_ROOT_PATH / ".env", override=True)


@dataclass
class DatabaseSettings:
    """Typed container for PostgreSQL connection settings."""

    dbname: str = field(default_factory=lambda: os.getenv("DB_NAME", ""))
    user: str = field(default_factory=lambda: os.getenv("DB_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("DB_PASSWORD", ""))
    host: str = field(default_factory=lambda: os.getenv("DB_HOST", "localhost"))
    port: int = field(default_factory=lambda: int(os.getenv("DB_PORT", 5432)))

    def to_dict(self) -> dict[str, str | int]:
        """
        Convert settings to a psycopg-compatible keyword argument dictionary.

        Args:
            None.

        Returns:
            dict[str, str | int]: Mapping passed as connection kwargs to the psycopg pool.
        """
        return {
            "dbname": self.dbname,
            "user": self.user,
            "password": self.password,
            "host": self.host,
            "port": self.port,
        }