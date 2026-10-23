from unittest.mock import Mock

import pytest

from tests.db_safety import assert_test_database, test_database_url as build_test_url


def write_config(tmp_path, **overrides):
    values = dict(DB_HOST="localhost", DB_PORT="5432", DB_NAME="orderflow_test_db",
                  DB_USER="test_user", DB_PASSWORD="test-placeholder")
    values.update(overrides)
    path = tmp_path / ".env.test"
    path.write_text("\n".join(f"{key}={value}" for key, value in values.items()
                              if value is not None), encoding="utf-8")
    return path


def test_missing_file_rejected(tmp_path):
    with pytest.raises(RuntimeError, match="complete"):
        build_test_url(tmp_path / "missing")


@pytest.mark.parametrize("name", ["orderflow_db", "postgres", "orderflow_test", ""])
def test_other_database_names_rejected(tmp_path, name):
    with pytest.raises(RuntimeError):
        build_test_url(write_config(tmp_path, DB_NAME=name))


@pytest.mark.parametrize("key", ["DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD"])
def test_missing_setting_never_inherits_shell(tmp_path, monkeypatch, key):
    monkeypatch.setenv(key, "inherited-value")
    with pytest.raises(RuntimeError):
        build_test_url(write_config(tmp_path, **{key: None}))


@pytest.mark.parametrize("port", ["bad", "0", "65536"])
def test_invalid_port_rejected(tmp_path, port):
    with pytest.raises(RuntimeError, match="port"):
        build_test_url(write_config(tmp_path, DB_PORT=port))


def test_valid_explicit_configuration(tmp_path):
    assert build_test_url(write_config(tmp_path)).database == "orderflow_test_db"


def test_server_identity_checked_before_ddl():
    connection = Mock()
    connection.execute.return_value.scalar_one.return_value = "orderflow_db"
    with pytest.raises(RuntimeError, match="refusing DDL"):
        assert_test_database(connection)
    assert connection.execute.call_count == 1
