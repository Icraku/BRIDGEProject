"""
tests/test_database_utils.py
============================
Tests for the SurrealDB helper layer.
"""

from pathlib import Path

from database_utils import db_utils


class FakeDB:
    def __init__(self):
        self.select_result: object = None
        self.create_result: object = {"status": "ok"}
        self.use_calls = []
        self.signin_calls = []
        self.create_calls = []
        self.select_calls = []

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb):
        return None

    def use(self, namespace, database):
        self.use_calls.append((namespace, database))

    def signin(self, credentials):
        self.signin_calls.append(credentials)

    def create(self, target, data):
        self.create_calls.append((target, data))
        return self.create_result

    def select(self, target):
        self.select_calls.append(target)
        return self.select_result


def _patch_db(monkeypatch):
    fake_db = FakeDB()
    monkeypatch.setattr(db_utils, "Surreal", lambda url: fake_db)
    monkeypatch.setattr(db_utils, "RecordID", lambda table, record_id: f"{table}:{record_id}")
    monkeypatch.setattr(db_utils, "_DB_USER", "demo-user")
    monkeypatch.setattr(db_utils, "_DB_PASSWORD", "demo-pass")
    return fake_db


def test_save_record_uses_explicit_record_id(monkeypatch):
    fake_db = _patch_db(monkeypatch)
    payload = {"image": "img.png", "accuracy": 0.95}

    result = db_utils.save_record(payload, "extractions", record_id="test_001")

    assert result == {"status": "ok"}
    assert fake_db.use_calls == [("BRIDGE", "Results")]
    assert fake_db.signin_calls == [{"username": "demo-user", "password": "demo-pass"}]
    assert fake_db.create_calls == [("extractions:test_001", payload)]


def test_fetch_record_returns_record(monkeypatch):
    fake_db = _patch_db(monkeypatch)
    fake_db.select_result = {"id": "extractions:test_001", "image": "img.png"}

    result = db_utils.fetch_record("extractions", "test_001")

    assert result == {"id": "extractions:test_001", "image": "img.png"}
    assert fake_db.select_calls == ["extractions:test_001"]


def test_fetch_records_returns_empty_list(monkeypatch):
    fake_db = _patch_db(monkeypatch)
    fake_db.select_result = None

    result = db_utils.fetch_records("extractions")

    assert result == []
    assert fake_db.select_calls == ["extractions"]


def test_safe_save_reraises_write_errors(monkeypatch):
    def raise_error(*args, **kwargs):
        raise RuntimeError("db unavailable")

    monkeypatch.setattr(db_utils, "save_record", raise_error)

    try:
        db_utils.safe_save({"field": "value"}, "structured", "test_001")
    except RuntimeError as exc:
        assert str(exc) == "db unavailable"
    else:
        assert False, "safe_save should raise when save_record fails"


def test_export_each_record_md_writes_files(monkeypatch, tmp_path: Path):
    monkeypatch.setattr(
        db_utils,
        "fetch_records",
        lambda table_name: [
            {"id": "extractions:test_001", "extracted_text": "# Sample one"},
            {"id": "extractions:test_002", "extracted_text": "# Sample two"},
        ],
    )

    db_utils.export_each_record_md("extractions", folder=str(tmp_path))

    assert (tmp_path / "extractions_test_001.md").read_text(encoding="utf-8") == "# Sample one"
    assert (tmp_path / "extractions_test_002.md").read_text(encoding="utf-8") == "# Sample two"
