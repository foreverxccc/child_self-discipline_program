from __future__ import annotations

from app.database import Database


class RewardService:
    """
    负责处理奖励系统（星星）和兑换商城的业务逻辑。
    包括：获取总星星数、完成任务发放星星、撤销任务回滚星星、管理兑换商品，以及处理孩子的兑换操作。
    """
    def __init__(self, database: Database) -> None:
        self.database = database

    def total_stars(self) -> int:
        """获取当前拥有的可用星星总数"""
        row = self.database.fetch_one("SELECT value FROM settings WHERE key = 'total_stars'")
        return int(row["value"]) if row is not None else 0

    def grant_for_plan_item(self, plan_item_id: int) -> int:
        """当一个任务完成时，根据任务模板里设置的奖励星星数，发放大红星并记录日志"""
        existing_reward = self.database.fetch_one(
            "SELECT id FROM reward_logs WHERE plan_item_id = ? LIMIT 1",
            (plan_item_id,),
        )
        if existing_reward is not None:
            return 0

        row = self.database.fetch_one(
            """
            SELECT tt.reward_stars, tt.title
            FROM daily_plan_items dpi
            JOIN task_templates tt ON tt.id = dpi.template_id
            WHERE dpi.id = ?
            """,
            (plan_item_id,),
        )
        if row is None:
            return 0

        stars = int(row["reward_stars"])
        self.database.execute(
            "INSERT INTO reward_logs(plan_item_id, stars, reason) VALUES(?, ?, ?)",
            (plan_item_id, stars, f"完成任务：{row['title']}"),
        )
        self.database.execute(
            """
            INSERT INTO settings(key, value)
            VALUES('total_stars', ?)
            ON CONFLICT(key) DO UPDATE SET value = CAST(CAST(value AS INTEGER) + ? AS TEXT)
            """,
            (str(stars), stars),
        )
        return stars

    def revoke_for_plan_item(self, plan_item_id: int) -> int:
        """当任务被取消完成状态时，扣除因该任务而获得的星星（防止误点或作弊）"""
        row = self.database.fetch_one(
            "SELECT id, stars FROM reward_logs WHERE plan_item_id = ?",
            (plan_item_id,),
        )
        if row is None:
            return 0
        
        stars = int(row["stars"])
        self.database.execute(
            "DELETE FROM reward_logs WHERE id = ?",
            (row["id"],),
        )
        self.database.execute(
            """
            UPDATE settings
            SET value = CAST(CAST(value AS INTEGER) - ? AS TEXT)
            WHERE key = 'total_stars'
            """,
            (stars,),
        )
        return stars

    def list_store_items(self) -> list[dict]:
        rows = self.database.fetch_all(
            """
            SELECT id, title, icon, cost_stars, sort_order, is_active
            FROM store_items
            WHERE is_active >= 0
            ORDER BY sort_order, id
            """
        )
        return [dict(row) for row in rows]

    def list_active_store_items(self) -> list[dict]:
        rows = self.database.fetch_all(
            """
            SELECT id, title, icon, cost_stars, sort_order, is_active
            FROM store_items
            WHERE is_active = 1
            ORDER BY sort_order, id
            """
        )
        return [dict(row) for row in rows]

    def create_store_item(self, title: str, icon: str, cost_stars: int) -> int:
        row = self.database.fetch_one("SELECT COALESCE(MAX(sort_order), 0) + 10 AS next_order FROM store_items")
        sort_order = int(row["next_order"]) if row is not None else 10
        return self.database.execute(
            """
            INSERT INTO store_items (title, icon, cost_stars, sort_order)
            VALUES (?, ?, ?, ?)
            """,
            (title, icon, cost_stars, sort_order),
        )

    def update_store_item(self, item_id: int, title: str, icon: str, cost_stars: int) -> None:
        self.database.execute(
            """
            UPDATE store_items
            SET title = ?, icon = ?, cost_stars = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, icon, cost_stars, item_id),
        )

    def set_store_item_active(self, item_id: int, is_active: bool) -> None:
        self.database.execute(
            "UPDATE store_items SET is_active = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (1 if is_active else 0, item_id),
        )

    def delete_store_item(self, item_id: int) -> None:
        self.database.execute(
            "UPDATE store_items SET is_active = -1, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (item_id,),
        )

    def move_store_item(self, item_id: int, direction: int) -> None:
        items = self.list_store_items()
        index = next((i for i, item in enumerate(items) if item["id"] == item_id), None)
        if index is None:
            return

        target_index = index + direction
        if target_index < 0 or target_index >= len(items):
            return

        items[index], items[target_index] = items[target_index], items[index]
        for idx, item in enumerate(items):
            sort_order = (idx + 1) * 10
            self.database.execute(
                "UPDATE store_items SET sort_order = ? WHERE id = ?",
                (sort_order, item["id"]),
            )

    def redeem_item(self, item_id: int) -> bool:
        """处理孩子兑换商城商品的操作。如果星星不够返回 False，如果足够则扣除对应的星星并记录兑换日志"""
        item = self.database.fetch_one(
            "SELECT title, cost_stars FROM store_items WHERE id = ? AND is_active = 1",
            (item_id,),
        )
        if not item:
            return False

        cost = int(item["cost_stars"])
        current_stars = self.total_stars()
        
        if current_stars < cost:
            return False
            
        with self.database.session():
            self.database.execute(
                "INSERT INTO reward_logs(plan_item_id, stars, reason) VALUES(NULL, ?, ?)",
                (-cost, f"兑换奖励：{item['title']}"),
            )
            self.database.execute(
                """
                UPDATE settings
                SET value = CAST(CAST(value AS INTEGER) - ? AS TEXT)
                WHERE key = 'total_stars'
                """,
                (cost,),
            )
        return True
