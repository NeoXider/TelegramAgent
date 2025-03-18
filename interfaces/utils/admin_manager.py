import json
from pathlib import Path
from typing import Dict, Optional

class AdminManager:
    def __init__(self, admin_password: str):
        self.admin_password = admin_password
        self.attempts: Dict[int, int] = {}  # user_id -> attempts count
        self.admin_ids: set = set()
        self.max_attempts = 3
        self._load_admin_data()

    def _load_admin_data(self):
        """Загрузка данных об администраторах из файла"""
        path = Path("data/admin_data.json")
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                self.admin_ids = set(data.get("admin_ids", []))
                self.attempts = {int(k): v for k, v in data.get("attempts", {}).items()}

    def _save_admin_data(self):
        """Сохранение данных об администраторах в файл"""
        path = Path("data/admin_data.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump({
                "admin_ids": list(self.admin_ids),
                "attempts": self.attempts
            }, f)

    def check_password(self, user_id: int, password: str) -> bool:
        """Проверка пароля с учетом количества попыток"""
        if user_id in self.admin_ids:
            return True

        if user_id not in self.attempts:
            self.attempts[user_id] = 0

        if self.attempts[user_id] >= self.max_attempts:
            return False

        if password == self.admin_password:
            self.admin_ids.add(user_id)
            self.attempts.pop(user_id, None)
            self._save_admin_data()
            return True
        else:
            self.attempts[user_id] += 1
            self._save_admin_data()
            return False

    def is_admin(self, user_id: int) -> bool:
        """Проверка, является ли пользователь администратором"""
        return user_id in self.admin_ids

    def get_remaining_attempts(self, user_id: int) -> Optional[int]:
        """Получение оставшихся попыток ввода пароля"""
        if user_id in self.admin_ids:
            return None
        attempts = self.attempts.get(user_id, 0)
        return max(0, self.max_attempts - attempts) 