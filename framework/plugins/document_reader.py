def read_document(document_path: str) -> str:
    try:
        with open(document_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Ошибка при чтении документа: {e}"