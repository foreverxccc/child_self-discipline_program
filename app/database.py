from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from contextlib import contextmanager
from pathlib import Path
from typing import Any


# 定义应用所需的 SQLite 表结构
SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS task_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'star',
    category TEXT NOT NULL DEFAULT 'custom',
    suggested_minutes INTEGER NOT NULL DEFAULT 10,
    reward_stars INTEGER NOT NULL DEFAULT 1,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS daily_plan_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_date TEXT NOT NULL,
    template_id INTEGER NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'pending',
    completed_at TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (template_id) REFERENCES task_templates(id)
);

CREATE TABLE IF NOT EXISTS timer_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    selected_minutes INTEGER NOT NULL,
    actual_seconds INTEGER NOT NULL DEFAULT 0,
    started_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TEXT,
    status TEXT NOT NULL DEFAULT 'running',
    linked_plan_item_id INTEGER,
    FOREIGN KEY (linked_plan_item_id) REFERENCES daily_plan_items(id)
);

CREATE TABLE IF NOT EXISTS reward_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    plan_item_id INTEGER,
    stars INTEGER NOT NULL,
    reason TEXT NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (plan_item_id) REFERENCES daily_plan_items(id)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS store_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    icon TEXT NOT NULL DEFAULT 'star',
    cost_stars INTEGER NOT NULL DEFAULT 10,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_active INTEGER NOT NULL DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);
"""


DEFAULT_TASKS = [
    ("阅读20分钟", "book", "study", 20, 2, 10),
    ("练字30分钟", "pen", "study", 30, 2, 20),
    ("口算10分钟", "calculator", "study", 10, 1, 30),
    ("背古诗", "scroll", "study", 15, 2, 40),
    ("整理书包", "bag", "life", 10, 1, 50),
    ("整理房间", "home", "life", 15, 2, 60),
    ("刷牙洗脸", "smile", "life", 8, 1, 70),
    ("跳绳30下", "activity", "sport", 10, 1, 80),
    ("拉伸5分钟", "person-standing", "sport", 5, 1, 90),
    ("喝水休息", "cup", "rest", 5, 1, 100),
]


class Database:
    """
    轻量级的 SQLite 数据库访问层，
    封装了连接池/上下文管理器，并提供基础的 SQL 执行和查询方法。
    """
    def __init__(self, path: Path) -> None:
        self.path = path

    def connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @contextmanager
    def session(self):
        connection = self.connect()
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def initialize(self) -> None:
        """运行 SCHEMA_SQL 创建所有的表"""
        with self.session() as connection:
            connection.executescript(SCHEMA_SQL)

    def seed_defaults(self) -> None:
        with self.session() as connection:
            task_count = connection.execute("SELECT COUNT(*) FROM task_templates").fetchone()[0]
            if task_count == 0:
                connection.executemany(
                    """
                    INSERT INTO task_templates
                        (title, icon, category, suggested_minutes, reward_stars, sort_order)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    DEFAULT_TASKS,
                )

            connection.execute(
                "INSERT OR IGNORE INTO settings(key, value) VALUES('parent_password_hash', ?)",
                ("03ac674216f3e15c761ee1a5e255f067953623c8b388b4459e13f978d7c846f4",),
            )
            connection.execute("INSERT OR IGNORE INTO settings(key, value) VALUES('total_stars', '0')")

    def fetch_all(self, sql: str, parameters: Iterable[Any] = ()) -> list[sqlite3.Row]:
        """执行 SQL 并返回所有的结果行"""
        with self.session() as connection:
            return list(connection.execute(sql, tuple(parameters)).fetchall())

    def fetch_one(self, sql: str, parameters: Iterable[Any] = ()) -> sqlite3.Row | None:
        with self.session() as connection:
            return connection.execute(sql, tuple(parameters)).fetchone()

    def execute(self, sql: str, parameters: Iterable[Any] = ()) -> int:
        """执行 SQL (如 INSERT/UPDATE) 并返回最后插入的行的 ID"""
        with self.session() as connection:
            cursor = connection.execute(sql, tuple(parameters))
            return int(cursor.lastrowid)
