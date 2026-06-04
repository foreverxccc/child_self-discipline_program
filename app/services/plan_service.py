from __future__ import annotations

from datetime import date

from app.database import Database


class PlanService:
    """
    负责管理每天的计划任务（Daily Plan Items）。
    主要功能包括：获取今日任务列表、添加/删除/移动今日任务、更改任务状态（如完成、失败、待办），以及确认今日计划。
    """
    def __init__(self, database: Database) -> None:
        self.database = database

    def list_today_items(self, today: date | None = None) -> list[dict]:
        """获取当天的所有计划任务，按设定的顺序(sort_order)排列返回"""
        plan_date = today or date.today()
        rows = self.database.fetch_all(
            """
            SELECT
                dpi.id,
                dpi.plan_date,
                dpi.template_id,
                tt.title,
                tt.icon,
                tt.suggested_minutes,
                tt.reward_stars,
                dpi.sort_order,
                dpi.status,
                dpi.completed_at
            FROM daily_plan_items dpi
            JOIN task_templates tt ON tt.id = dpi.template_id
            WHERE dpi.plan_date = ?
            ORDER BY dpi.sort_order, dpi.id
            """,
            (plan_date.isoformat(),),
        )
        return [dict(row) for row in rows]

    def add_template_to_today(self, template_id: int, today: date | None = None) -> int:
        """根据任务模板ID，将该任务添加到今日计划中"""
        plan_date = today or date.today()
        row = self.database.fetch_one(
            "SELECT COALESCE(MAX(sort_order), 0) + 10 AS next_order FROM daily_plan_items WHERE plan_date = ?",
            (plan_date.isoformat(),),
        )
        sort_order = int(row["next_order"]) if row is not None else 10
        return self.database.execute(
            """
            INSERT INTO daily_plan_items(plan_date, template_id, sort_order)
            VALUES (?, ?, ?)
            """,
            (plan_date.isoformat(), template_id, sort_order),
        )

    def mark_completed(self, plan_item_id: int) -> None:
        """将指定的任务标记为“已完成”，并记录完成时间"""
        self.database.execute(
            """
            UPDATE daily_plan_items
            SET status = 'completed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (plan_item_id,),
        )

    def mark_failed(self, plan_item_id: int) -> None:
        self.database.execute(
            """
            UPDATE daily_plan_items
            SET status = 'failed', completed_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (plan_item_id,),
        )

    def mark_pending(self, plan_item_id: int) -> None:
        """将指定的任务重置为“待办”状态（支持孩子或家长回滚任务状态）"""
        self.database.execute(
            """
            UPDATE daily_plan_items
            SET status = 'pending', completed_at = NULL
            WHERE id = ?
            """,
            (plan_item_id,),
        )

    def remove_item(self, plan_item_id: int) -> None:
        self.database.execute(
            "DELETE FROM reward_logs WHERE plan_item_id = ?",
            (plan_item_id,),
        )
        self.database.execute(
            "DELETE FROM daily_plan_items WHERE id = ?",
            (plan_item_id,),
        )

    def clear_today_items(self, today: date | None = None) -> None:
        plan_date = today or date.today()
        self.database.execute(
            """
            DELETE FROM reward_logs 
            WHERE plan_item_id IN (
                SELECT id FROM daily_plan_items WHERE plan_date = ?
            )
            """,
            (plan_date.isoformat(),),
        )
        self.database.execute(
            "DELETE FROM daily_plan_items WHERE plan_date = ?",
            (plan_date.isoformat(),),
        )

    def copy_yesterday_items(self, today: date | None = None) -> None:
        """一键复制昨天的计划任务到今天"""
        from datetime import timedelta
        plan_date = today or date.today()
        yesterday = plan_date - timedelta(days=1)
        
        # Get yesterday's items ordered by sort_order
        rows = self.database.fetch_all(
            """
            SELECT template_id, sort_order
            FROM daily_plan_items
            WHERE plan_date = ?
            ORDER BY sort_order, id
            """,
            (yesterday.isoformat(),),
        )
        
        if not rows:
            return
            
        # Get max sort_order for today to append correctly
        max_order_row = self.database.fetch_one(
            "SELECT COALESCE(MAX(sort_order), 0) AS max_order FROM daily_plan_items WHERE plan_date = ?",
            (plan_date.isoformat(),),
        )
        current_max_order = int(max_order_row["max_order"]) if max_order_row is not None else 0
        
        # Insert them for today
        for row in rows:
            current_max_order += 10
            self.database.execute(
                """
                INSERT INTO daily_plan_items(plan_date, template_id, sort_order)
                VALUES (?, ?, ?)
                """,
                (plan_date.isoformat(), row["template_id"], current_max_order),
            )

    def move_item(self, plan_item_id: int, direction: int, today: date | None = None) -> None:
        plan_date = today or date.today()
        items = self.list_today_items(plan_date)
        index = next((i for i, item in enumerate(items) if item["id"] == plan_item_id), None)
        if index is None:
            return

        target_index = index + direction
        if target_index < 0 or target_index >= len(items):
            return

        items[index], items[target_index] = items[target_index], items[index]
        for sort_order, item in enumerate(items, start=1):
            self.database.execute(
                "UPDATE daily_plan_items SET sort_order = ? WHERE id = ?",
                (sort_order * 10, item["id"]),
            )

    def is_plan_confirmed(self, today: date | None = None) -> bool:
        """检查今天的计划是否已被家长确认，确认后的计划通常不允许轻易删除或大幅修改"""
        plan_date = today or date.today()
        key = f"plan_confirmed_{plan_date.isoformat()}"
        row = self.database.fetch_one("SELECT value FROM settings WHERE key = ?", (key,))
        if row and row["value"] == "1":
            return True
        return False

    def set_plan_confirmed(self, confirmed: bool, today: date | None = None) -> None:
        plan_date = today or date.today()
        key = f"plan_confirmed_{plan_date.isoformat()}"
        value = "1" if confirmed else "0"
        self.database.execute(
            """
            INSERT INTO settings (key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )
