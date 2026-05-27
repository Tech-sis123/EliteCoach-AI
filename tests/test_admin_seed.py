import importlib
from contextlib import AbstractAsyncContextManager

import pytest
from sqlalchemy import text

from app.models.users import User, UserRole, UserRoleEnum


create_admin_script = importlib.import_module("scripts.create_admin")


class _SessionContext(AbstractAsyncContextManager):
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def _bind_script_session(monkeypatch, session):
    monkeypatch.setattr(create_admin_script, "AsyncSessionLocal", lambda: _SessionContext(session))


@pytest.mark.asyncio
async def test_create_admin_script_creates_user_and_role(db, monkeypatch, capsys):
    _bind_script_session(monkeypatch, db)

    email = "admin@example.com"
    full_name = "Platform Admin"
    password = "StrongPass123!"

    await create_admin_script.create_admin(email, full_name, password)

    captured = capsys.readouterr()
    assert "Platform admin created successfully" in captured.out

    user = (await db.execute(
        User.__table__.select().where(User.__table__.c.email == email)
    )).mappings().one()
    assert user["email"] == email
    assert user["full_name"] == full_name
    assert user["is_active"] is True
    assert user["is_deleted"] is False
    assert user["email_verified_at"] is not None

    # Use text() with stringified UUID for SQLite compatibility in tests
    user_id_str = str(user["id"])
    role_result = await db.execute(
        text("SELECT * FROM user_roles WHERE user_id = :user_id"),
        {"user_id": user_id_str}
    )
    role = role_result.mappings().one()
    assert role["role"] == "platform_admin"


@pytest.mark.asyncio
async def test_create_admin_script_rejects_duplicate_email(db, monkeypatch, capsys):
    _bind_script_session(monkeypatch, db)

    email = "duplicate@example.com"

    await create_admin_script.create_admin(email, "First Admin", "StrongPass123!")

    with pytest.raises(SystemExit) as excinfo:
        await create_admin_script.create_admin(email, "Second Admin", "StrongPass123!")

    assert excinfo.value.code == 1

    captured = capsys.readouterr()
    assert f"ERROR: A user with email '{email}' already exists." in captured.out

    count = (await db.execute(
        User.__table__.select().where(User.email == email)
    )).mappings().all()
    assert len(count) == 1