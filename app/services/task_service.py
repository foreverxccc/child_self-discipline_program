from __future__ import annotations

from app.database import Database


class TaskService:
    def __init__(self, database: Database) -> None:
        self.database = database

    def list_templates(self) -> list[dict]:
        rows = self.database.fetch_all(
            """
            SELECT id, title, icon, category, suggested_minutes, reward_stars, sort_order, is_active
            FROM task_templates
            WHERE is_active >= 0
            ORDER BY sort_order, id
            """
        )
        return [dict(row) for row in rows]

    def list_active_templates(self) -> list[dict]:
        rows = self.database.fetch_all(
            """
            SELECT id, title, icon, category, suggested_minutes, reward_stars, sort_order, is_active
            FROM task_templates
            WHERE is_active = 1
            ORDER BY sort_order, id
            """
        )
        return [dict(row) for row in rows]

    def create_template(
        self,
        title: str,
        icon: str,
        category: str,
        suggested_minutes: int,
        reward_stars: int,
    ) -> int:
        row = self.database.fetch_one("SELECT COALESCE(MAX(sort_order), 0) + 10 AS next_order FROM task_templates")
        sort_order = int(row["next_order"]) if row is not None else 10
        return self.database.execute(
            """
            INSERT INTO task_templates
                (title, icon, category, suggested_minutes, reward_stars, sort_order)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (title, icon, category, suggested_minutes, reward_stars, sort_order),
        )

    def update_template(
        self,
        template_id: int,
        title: str,
        icon: str,
        category: str,
        suggested_minutes: int,
        reward_stars: int,
    ) -> None:
        self.database.execute(
            """
            UPDATE task_templates
            SET
                title = ?,
                icon = ?,
                category = ?,
                suggested_minutes = ?,
                reward_stars = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, icon, category, suggested_minutes, reward_stars, template_id),
        )

    def set_template_active(self, template_id: int, is_active: bool) -> None:
        self.database.execute(
            """
            UPDATE task_templates
            SET is_active = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (1 if is_active else 0, template_id),
        )

    def delete_template(self, template_id: int) -> None:
        self.database.execute(
            "UPDATE task_templates SET is_active = -1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (template_id,),
        )

    def move_template(self, template_id: int, direction: int) -> None:
        templates = self.list_templates()
        index = next((i for i, template in enumerate(templates) if template["id"] == template_id), None)
        if index is None:
            return

        target_index = index + direction
        if target_index < 0 or target_index >= len(templates):
            return

        templates[index], templates[target_index] = templates[target_index], templates[index]
        for sort_order, template in enumerate(templates, start=1):
            self.database.execute(
                "UPDATE task_templates SET sort_order = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (sort_order * 10, template["id"]),
            )
