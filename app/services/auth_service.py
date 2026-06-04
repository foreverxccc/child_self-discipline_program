from __future__ import annotations

import hashlib

from app.database import Database


class AuthService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def verify_parent_password(self, password: str) -> bool:
        row = self.database.fetch_one(
            "SELECT value FROM settings WHERE key = 'parent_password_hash'",
        )
        if row is None:
            return False
        return self._hash_password(password) == row["value"]

    def change_parent_password(self, new_password: str) -> None:
        password_hash = self._hash_password(new_password)
        self.database.execute(
            """
            INSERT INTO settings(key, value)
            VALUES('parent_password_hash', ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (password_hash,),
        )

    @staticmethod
    def _hash_password(password: str) -> str:
        return hashlib.sha256(password.encode("utf-8")).hexdigest()

