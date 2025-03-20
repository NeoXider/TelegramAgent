#!/usr/bin/env python3
import asyncio
import logging
import os
import sys
import psutil
from run_bot import main

def check_instance():
    """Проверка, не запущен ли уже экземпляр бота"""
    pid_file = "bot.pid"
    
    # Проверяем существование PID файла
    if os.path.exists(pid_file):
        try:
            with open(pid_file, 'r') as f:
                old_pid = int(f.read().strip())
                
            # На Windows используем psutil для проверки процесса
            if psutil.pid_exists(old_pid):
                print(f"Бот уже запущен (PID: {old_pid})")
                return False
                
        except (ValueError, IOError) as e:
            print(f"Ошибка при чтении PID файла: {e}")
        
        try:
            os.remove(pid_file)
        except PermissionError:
            print("Не удалось удалить старый PID файл. Возможно, он используется другим процессом.")
            return False
        except OSError as e:
            print(f"Ошибка при удалении PID файла: {e}")
            return False
    
    # Записываем текущий PID
    try:
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
        return True
    except IOError as e:
        print(f"Не удалось создать PID файл: {e}")
        return False

def cleanup():
    """Очистка при завершении работы"""
    pid_file = "bot.pid"
    try:
        if os.path.exists(pid_file):
            os.remove(pid_file)
    except (PermissionError, OSError) as e:
        print(f"Ошибка при удалении PID файла: {e}")

if __name__ == '__main__':
    # Настраиваем базовое логирование
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Проверяем, не запущен ли уже бот
    if not check_instance():
        sys.exit(1)
    
    try:
        # Запускаем бота
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nБот остановлен пользователем")
    except Exception as e:
        print(f"Критическая ошибка: {e}")
        raise
    finally:
        cleanup() 