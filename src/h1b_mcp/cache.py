import json
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from urllib.parse import urlparse

from pydantic import ValidationError

from h1b_mcp.models import CompanyProfile
from h1b_mcp.settings import Settings
from h1b_mcp.utils import normalize_company_name

INDEX_FILENAME = "index.json"


class CompanyProfileCache:
    def __init__(self, settings: Settings) -> None:
        self._cache_dir = settings.cache_dir
        self._ttl = timedelta(seconds=settings.cache_ttl_seconds)

    def get(self, company_name: str) -> CompanyProfile | None:
        key = cache_key(company_name)
        if not key:
            return None

        index = self._load_index()
        filename = index.get(key, profile_filename(key))
        profile = self._read_profile(filename)
        if not profile or self._is_stale(profile):
            return None
        return profile

    def set(self, profile: CompanyProfile) -> None:
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        aliases = profile_aliases(profile)
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

    def _read_profile(self, filename: str) -> CompanyProfile | None:
        path = self._cache_dir / filename
        if not path.exists():
            return None
        try:
            return CompanyProfile.model_validate_json(path.read_text(encoding="utf-8"))
        except (OSError, ValidationError, ValueError):
            return None

    def _is_stale(self, profile: CompanyProfile) -> bool:
        fetched_at = profile.fetched_at
        if fetched_at.tzinfo is None:
            fetched_at = fetched_at.replace(tzinfo=UTC)
        return datetime.now(UTC) - fetched_at > self._ttl

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


def profile_aliases(profile: CompanyProfile) -> set[str]:
    aliases = {
        cache_key(profile.company_query),
        cache_key(profile.matched_company or ""),
        cache_key(url_slug(profile.url)),
    }
    return {alias for alias in aliases if alias}


def first_alias(aliases: set[str]) -> str:
    return sorted(aliases)[0] if aliases else ""


def cache_key(value: str) -> str:
    return normalize_company_name(value)


def profile_filename(key: str) -> str:
    digest = sha256(key.encode("utf-8")).hexdigest()[:20]
    return f"{digest}.json"


def url_slug(url: str) -> str:
    path = urlparse(url).path.rstrip("/")
    return path.rsplit("/", 1)[-1] if path else ""
