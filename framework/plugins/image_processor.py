try:
    from PIL import Image
    import pytesseract
except ImportError:
    # Если библиотеки не установлены, возвращаем сообщение об ошибке
    def extract_text_from_image(image_path: str) -> str:
        return "Ошибка: Pillow или pytesseract не установлены."
else:
    def extract_text_from_image(image_path: str) -> str:
        try:
            img = Image.open(image_path)
            text = pytesseract.image_to_string(img)
            return text
        except Exception as e:
            return f"Ошибка при обработке изображения: {e}"