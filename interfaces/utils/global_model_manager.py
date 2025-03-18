import json
from pathlib import Path
from typing import Dict, Optional

class GlobalModelManager:
    def __init__(self):
        self.models: Dict[str, str] = {
            "основная": None,
            "зрение": None
        }
        self._load_models()

    def _load_models(self):
        """Загрузка настроек моделей из файла"""
        path = Path("data/global_models.json")
        if path.exists():
            with open(path, "r") as f:
                data = json.load(f)
                self.models.update(data)

    def _save_models(self):
        """Сохранение настроек моделей в файл"""
        path = Path("data/global_models.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.models, f)

    def set_model(self, model_type: str, model_name: str):
        """Установка модели определенного типа"""
        if model_type in self.models:
            self.models[model_type] = model_name
            self._save_models()
            return True
        return False

    def get_model(self, model_type: str) -> Optional[str]:
        """Получение текущей модели определенного типа"""
        return self.models.get(model_type)

    def get_all_models(self) -> Dict[str, str]:
        """Получение всех текущих моделей"""
        return self.models.copy() 