import json
from collections.abc import Callable
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from pathlib import Path
from typing import Any, Generic, TypeVar
from urllib.parse import urlparse

from pydantic import ValidationError

from h1b_mcp.constants import PROFILE_CACHE_SCHEMA_VERSION
from h1b_mcp.models import CachedProfile
from h1b_mcp.utils import normalize_company_name

INDEX_FILENAME = "index.json"
TProfile = TypeVar("TProfile", bound=CachedProfile[Any])


class ProfileCache(Generic[TProfile]):
    """Disk cache for any H1BGrader profile keyed by normalized aliases."""

    def __init__(
        self,
        *,
        cache_dir: Path,
        ttl_seconds: int,
        model_type: type[TProfile],
        aliases: Callable[[TProfile], set[str]],
    ) -> None:
        self._cache_dir = cache_dir
        self._ttl = timedelta(seconds=ttl_seconds)
        self._model_type = model_type
        self._aliases = aliases

    def get(self, query: str) -> TProfile | None:
        key = cache_key(query)
        if not key:
            return None

        index = self._load_index()
        filename = index.get(key, profile_filename(key))
        profile = self._read_profile(filename)
        if not profile or self._is_stale(profile) or self._has_stale_schema(profile):
            return None
        return profile

    def set(self, profile: TProfile) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        aliases = self._aliases(profile)
        canonical_key = first_alias(aliases)
        if not canonical_key:
            return

        filename = profile_filename(canonical_key)
        profile_path = self._cache_dir / filename
        profile_path.write_text(profile.model_dump_json(indent=2), encoding="utf-8")

        index = self._load_index()
        for alias in aliases:
            index[alias] = filename
        self._write_index(index)

    def _read_profile(self, filename: str) -> TProfile | None:
        path = self._cache_dir / filename
        if not path.exists():
            return None
        try:
            return self._model_type.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError, ValueError):
            return None

    def _is_stale(self, profile: TProfile) -> bool:
        fetched_at = profile.fetched_at
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return datetime.now(UTC) - fetched_at > self._ttl

    @staticmethod
    def _has_stale_schema(profile: TProfile) -> bool:
        return profile.cache_schema_version < PROFILE_CACHE_SCHEMA_VERSION

    def _load_index(self) -> dict[str, str]:
        path = self._cache_dir / INDEX_FILENAME
        if not path.exists():
            return {}
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        return {str(key): str(value) for key, value in data.items()}

    def _write_index(self, index: dict[str, str]) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        path = self._cache_dir / INDEX_FILENAME
        path.write_text(json.dumps(index, indent=2, sort_keys=True), encoding="utf-8")


def profile_aliases(profile: CachedProfile[Any]) -> set[str]:
    """Return stable lookup keys that should point at the same cached profile."""
    aliases = {
        cache_key(profile.query),
        cache_key(profile.matched_name or ""),
        cache_key(url_slug(profile.url)),
    }
    return {alias for alias in aliases if alias}


def first_alias(aliases: set[str]) -> str:
    """Choose a deterministic filename owner from a set of equivalent cache aliases."""
    return sorted(aliases)[0] if aliases else ""


def cache_key(value: str) -> str:
    """Use the same normalization for cache lookup as H1BGrader typeahead lookup."""
    return normalize_company_name(value)


def profile_filename(key: str) -> str:
    """Keep cache filenames short and filesystem-safe without exposing raw queries."""
    digest = sha256(key.encode("utf-8")).hexdigest()[:20]
    return f"{digest}.json"


def url_slug(url: str) -> str:
    """Extract H1BGrader's profile slug so URL-derived aliases survive query changes."""
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""
