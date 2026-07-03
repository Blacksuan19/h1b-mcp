from dataclasses import dataclass, field
from pathlib import Path


def default_profile_dir() -> Path:
    return Path.home() / ".h1b-mcp" / "browser-profile"


def default_cache_dir() -> Path:
    return Path.home() / ".h1b-mcp" / "cache" / "company-profiles"


@dataclass(frozen=True)
class Settings:
    base_url: str = "https://h1bgrader.com/"
    timeout_ms: int = 30_000
    profile_dir: Path = field(default_factory=default_profile_dir)
    cache_dir: Path = field(default_factory=default_cache_dir)
    cache_ttl_seconds: int = 60 * 60 * 24 * 7


settings = Settings()
