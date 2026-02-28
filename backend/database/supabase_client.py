"""
Supabase Client Singleton
=========================
Provides a single Supabase client instance for the entire application.
Uses the SERVICE_KEY (service role) to bypass RLS for backend operations.
Falls back to in-memory storage if Supabase is not configured.
"""
import logging
from typing import Optional

from config import get_settings

logger = logging.getLogger("deepshield.db")

_client = None
_use_mock = False


class MockSupabaseClient:
    """
    In-memory mock client for development without Supabase.
    Stores data in dictionaries — data is lost on restart.
    """

    def __init__(self):
        self._tables: dict[str, list[dict]] = {}
        logger.info("📦 Using in-memory mock database (no Supabase configured)")

    def table(self, name: str):
        if name not in self._tables:
            self._tables[name] = []
        return MockTable(self._tables, name)

    @property
    def storage(self):
        return MockStorage()


class MockTable:
    """Mock table for CRUD operations."""

    def __init__(self, tables: dict, name: str):
        self._tables = tables
        self._name = name
        self._filters = []
        self._order_col = None
        self._order_desc = False
        self._limit_val = None

    def select(self, columns: str = "*"):
        self._filters = []
        self._order_col = None
        self._limit_val = None
        return self

    def insert(self, data: dict | list):
        import uuid
        if isinstance(data, list):
            for item in data:
                if "id" not in item:
                    item["id"] = str(uuid.uuid4())
                self._tables[self._name].append(item)
        else:
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            self._tables[self._name].append(data)
        return self

    def update(self, data: dict):
        self._update_data = data
        return self

    def delete(self):
        return self

    def eq(self, column: str, value):
        self._filters.append((column, "eq", value))
        return self

    def neq(self, column: str, value):
        self._filters.append((column, "neq", value))
        return self

    def gte(self, column: str, value):
        self._filters.append((column, "gte", value))
        return self

    def lte(self, column: str, value):
        self._filters.append((column, "lte", value))
        return self

    def in_(self, column: str, values: list):
        self._filters.append((column, "in", values))
        return self

    def order(self, column: str, desc: bool = False):
        self._order_col = column
        self._order_desc = desc
        return self

    def limit(self, count: int):
        self._limit_val = count
        return self

    def _apply_filters(self, data: list[dict]) -> list[dict]:
        result = data
        for col, op, val in self._filters:
            if op == "eq":
                result = [r for r in result if r.get(col) == val]
            elif op == "neq":
                result = [r for r in result if r.get(col) != val]
            elif op == "gte":
                result = [r for r in result if r.get(col, 0) >= val]
            elif op == "lte":
                result = [r for r in result if r.get(col, 0) <= val]
            elif op == "in":
                result = [r for r in result if r.get(col) in val]
        return result

    def execute(self):
        data = self._tables.get(self._name, [])

        if self._filters:
            data = self._apply_filters(data)

        if hasattr(self, "_update_data") and self._filters:
            for item in self._tables[self._name]:
                match = True
                for col, op, val in self._filters:
                    if op == "eq" and item.get(col) != val:
                        match = False
                if match:
                    item.update(self._update_data)
            data = self._apply_filters(self._tables[self._name])

        if self._order_col:
            data = sorted(data, key=lambda x: x.get(self._order_col, ""),
                          reverse=self._order_desc)
        if self._limit_val:
            data = data[: self._limit_val]

        return MockResponse(data)

    def upsert(self, data: dict):
        # Find existing by id or insert
        existing = [i for i, r in enumerate(self._tables[self._name])
                    if r.get("id") == data.get("id") or r.get("name") == data.get("name")]
        if existing:
            self._tables[self._name][existing[0]].update(data)
        else:
            import uuid
            if "id" not in data:
                data["id"] = str(uuid.uuid4())
            self._tables[self._name].append(data)
        return self

    def single(self):
        return self


class MockResponse:
    def __init__(self, data):
        self.data = data


class MockStorage:
    def from_(self, bucket: str):
        return self

    def upload(self, path: str, file_data, file_options=None):
        return {"path": path}

    def download(self, path: str):
        return b""

    def get_public_url(self, path: str):
        return f"/mock-storage/{path}"


def get_client():
    """
    Get or create the Supabase client singleton.
    Falls back to MockSupabaseClient if Supabase is not configured.
    """
    global _client, _use_mock

    if _client is not None:
        return _client

    settings = get_settings()

    # Check if real Supabase credentials are provided
    if (settings.SUPABASE_URL == "https://your-project.supabase.co"
            or settings.SUPABASE_SERVICE_KEY == "your-service-role-key"):
        logger.warning("⚠️  Supabase not configured — using in-memory mock database")
        _client = MockSupabaseClient()
        _use_mock = True
        return _client

    try:
        from supabase import create_client
        _client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        logger.info("✅ Connected to Supabase")
        return _client
    except Exception as e:
        logger.error(f"❌ Supabase connection failed: {e}")
        logger.info("   Falling back to in-memory mock database")
        _client = MockSupabaseClient()
        _use_mock = True
        return _client


def is_mock() -> bool:
    """Check if we're using the mock database."""
    return _use_mock
