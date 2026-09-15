from dataclasses import dataclass, field
import os
from pathlib import Path
import secrets

BASE_DIR = Path(__file__).resolve().parents[1]


def load_environment():
    path = BASE_DIR / ".env"
    if path.is_file():
        for line in path.read_text(encoding="utf-8").splitlines():
            key, separator, value = line.partition("=")
            if separator and key.strip() and not key.lstrip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


@dataclass
class Settings:
    database_url: str = f"sqlite:///{(BASE_DIR / 'database' / 'codyssey_v2.db').as_posix()}"
    operator_password: str = ""
    allowed_origins: tuple = ("http://127.0.0.1:5173", "http://localhost:5173", "http://127.0.0.1:8000", "http://localhost:8000")
    match_radius_m: float = 25
    heartbeat_timeout: int = 30
    password_file: Path = field(default_factory=lambda: BASE_DIR / "database" / "operator-password.txt")

    @classmethod
    def from_environment(cls):
        load_environment()
        settings = cls()
        settings.database_url = os.environ.get("CODYSSEY_DATABASE_URL", settings.database_url)
        settings.operator_password = os.environ.get("CODYSSEY_OPERATOR_PASSWORD", "")
        settings.allowed_origins = tuple(value.strip() for value in os.environ.get("CODYSSEY_ALLOWED_ORIGINS", ",".join(settings.allowed_origins)).split(",") if value.strip())
        return settings

    def ensure_operator_password(self):
        if self.operator_password:
            return
        self.password_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.password_file.exists():
            try:
                with self.password_file.open("x", encoding="utf-8") as output:
                    output.write(secrets.token_urlsafe(24))
            except FileExistsError:
                pass
        self.operator_password = self.password_file.read_text(encoding="utf-8").strip()
        if not self.operator_password:
            raise RuntimeError(f"Operator password file is empty: {self.password_file}")
        print(f"Operator sign-in password is stored in: {self.password_file}")
