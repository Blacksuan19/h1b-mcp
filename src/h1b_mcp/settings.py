from dataclasses import dataclass, field
from pathlib import Path


def default_profile_dir() -> Path:
    return Path.home() / ".h1b-mcp" / "browser-profile"


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://h1bgrader.com/"
    timeout_ms: int = 30_000
    profile_dir: Path = field(default_factory=default_profile_dir)


settings = Settings()
