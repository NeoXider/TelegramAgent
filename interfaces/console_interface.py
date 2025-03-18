from agent_base import AIAgent

def main():
    agent = AIAgent("ConsoleAgent")
    print("AI Agent Framework Console")
    print("Доступные команды:")
    print(" - Просто отправьте запрос для анализа (агент сам подберет инструмент).")
    print(" - /setmodel <model_name> для установки основной модели Ollama.")
    print(" - /setvision <model_name> для установки модели для анализа изображений.")
    print(" - /recall_memory для вывода накопленной памяти.")
    print(" - exit для выхода")
    
    while True:
        try:
            command = input(">>> ")
        except EOFError:
            break
        if not command.strip():
            continue
        if command.lower() == "exit":
            break
        if command.startswith("/setmodel"):
            parts = command.split()
            if len(parts) >= 2:
                agent.model_name = parts[1]
                print(f"Основная модель установлена: {parts[1]}")
            else:
                print("Использование: /setmodel <model_name>")
            continue
        if command.startswith("/setvision"):
            parts = command.split()
            if len(parts) >= 2:
                agent.vision_model_name = parts[1]
                print(f"Модель для анализа изображений установлена: {parts[1]}")
            else:
                print("Использование: /setvision <model_name>")
            continue
        result = agent.process_request(command)
        print(result)

if __name__ == "__main__":
    main()