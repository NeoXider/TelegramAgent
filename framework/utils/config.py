import os
import json
from typing import Dict, Any
from dotenv import load_dotenv

def load_config() -> Dict[str, Any]:
    """Загрузка конфигурации из файла или создание конфигурации по умолчанию"""
    config = {
        'bot': {
            'name': 'MultiAgentBot',
            'username': 'multi_agent_bot'
        },
        'queue': {
            'max_queue_size': 5,
            'task_timeout': 300,  # 5 минут
            'max_retries': 3
        },
        'agents': {
            'models': {
                'think': 'gemma3:12b',
                'image': 'llava',
                'default': 'gemma3:12b'
            },
            'memory': {
                'max_messages': 10,
                'max_context_length': 2000
            }
        },
        'logging': {
            'level': 'INFO',
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    }
    
    try:
        # Пытаемся загрузить конфигурацию из файла
        if os.path.exists('config/bot_config.json'):
            with open('config/bot_config.json', 'r', encoding='utf-8') as f:
                file_config = json.load(f)
                # Обновляем конфигурацию по умолчанию значениями из файла
                config.update(file_config)
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Получаем токены
        if os.getenv('BOT_TOKEN'):
            config['bot']['token'] = os.getenv('BOT_TOKEN')
        
        return config
        
    except Exception as e:
        print(f"Предупреждение: Ошибка при загрузке конфигурации из файла: {str(e)}")
        print("Используется конфигурация по умолчанию")
        return config 