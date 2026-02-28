import json
from pathlib import Path
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Конфигурация
TOKEN = 'укажите токен'
FILES_DIR = Path('')  # Путь к директории с файлами

# Находим все JSON файлы
files = {}
for file in FILES_DIR.glob('*.json'):
    files[file.stem] = file

print(f"Найдено файлов: {len(files)}")

async def send_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    command = update.message.text[1:]  # Получаем команду (имя файла)
    
    if command not in files:
        await update.message.reply_text(f"Файл {command}.json не найден")
        return
    
    try:
        with open(files[command], 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Проверяем, пустые ли данные
        if is_data_empty(data):
            await update.message.reply_text("В данный момент предложений нет в категории")
            return
        
        # Форматируем JSON в нужный вид
        formatted_text = format_json_data(data)
        
        # Если текст слишком длинный, разбиваем на части
        if len(formatted_text) > 4000:
            parts = split_text(formatted_text, 4000)
            for i, part in enumerate(parts, 1):
                if i == 1:
                    await update.message.reply_text(part)
                else:
                    await update.message.reply_text(f"(продолжение {i}/{len(parts)})\n\n{part}")
        else:
            await update.message.reply_text(formatted_text)
            
    except json.JSONDecodeError:
        # Проверяем, пустой ли файл
        file_path = files[command]
        if is_file_empty(file_path):
            await update.message.reply_text("В данный момент предложений нет в категории")
        else:
            await update.message.reply_text("Ошибка: файл содержит некорректный JSON")
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

def is_file_empty(file_path):
    """Проверяет, пустой ли файл"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        return len(content) == 0
    except:
        return False

def is_data_empty(data):
    """Проверяет, пустые ли данные"""
    if data is None:
        return True
    elif isinstance(data, list):
        # Проверяем пустой список
        if len(data) == 0:
            return True
        # Проверяем список с пустыми элементами
        if all(is_item_empty(item) for item in data):
            return True
        return False
    elif isinstance(data, dict):
        # Проверяем пустой словарь
        if len(data) == 0:
            return True
        # Проверяем словарь с пустыми значениями
        if all(value is None or value == '' for value in data.values()):
            return True
        return False
    else:
        return str(data).strip() == ""

def is_item_empty(item):
    """Проверяет, пустой ли элемент (для списков)"""
    if isinstance(item, dict):
        # Проверяем словарь
        if len(item) == 0:
            return True
        # Проверяем, все ли значения пустые или None
        for key, value in item.items():
            if value is not None and str(value).strip() != '':
                return False
        return True
    else:
        return item is None or str(item).strip() == ""

def format_json_data(data):
    """
    Форматирует JSON данные в указанный формат с выравниванием.
    Пример:
    1. Символ Новолуния Бодрость Кач-во мат. 3:    992.54
    2. Символ Новолуния Сияние Кач-во мат. 3:      190.55
    3. Символ Новолуния Вознесение Кач-во мат. 3:  103.23
    """
    result = []
    
    # Проверяем, является ли data списком
    if isinstance(data, list):
        for i, item in enumerate(data, 1):
            if isinstance(item, dict):
                # Получаем значения по ключам name и profit
                name = item.get('name', 'Не указано')
                profit = item.get('profit', 'Не указано')
                
                # Проверяем, что значения не пустые
                if name != 'Не указано' and profit != 'Не указано':
                    # Добавляем табуляцию (4 пробела) между названием и цифрой
                    result.append(f"{i}. {name}:    {profit}")
            else:
                # Для не-словарей выводим как есть
                item_str = str(item).strip()
                if item_str:
                    result.append(f"{i}. {item_str}")
    elif isinstance(data, dict):
        # Если это словарь, выводим ключ: значение
        for key, value in data.items():
            value_str = str(value).strip()
            if value_str:
                result.append(f"{key}:    {value_str}")
    else:
        # Если это не список и не словарь, просто выводим как есть
        data_str = str(data).strip()
        if data_str:
            result.append(data_str)
    
    return "\n".join(result) if result else ""

def split_text(text, max_length):
    """Разбивает текст на части указанной максимальной длины"""
    parts = []
    current_part = ""
    
    for line in text.split('\n'):
        if len(current_part) + len(line) + 1 <= max_length:
            if current_part:
                current_part += '\n' + line
            else:
                current_part = line
        else:
            if current_part:
                parts.append(current_part)
                current_part = line
            else:
                # Если одна строка длиннее max_length, разбиваем ее
                parts.append(line[:max_length])
                current_part = line[max_length:]
    
    if current_part:
        parts.append(current_part)
    
    return parts

async def help_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    commands = "\n".join([f"/{name}" for name in files.keys()])
    await update.message.reply_text(f"Доступные команды:\n{commands}")

async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"Привет, {update.effective_user.first_name}!\n\n"
        f"Я бот для отображения данных из JSON файлов.\n"
        f"Используйте /help чтобы увидеть все доступные команды."
    )

def main():
    app = Application.builder().token(TOKEN).build()
    
    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("help", help_cmd))
    
    # Регистрируем команды для каждого файла
    for name in files.keys():
        app.add_handler(CommandHandler(name, send_file))
    
    print("=" * 50)
    print("Бот запущен!")
    print(f"Загружено команд: {len(files)}")
    if files:
        print("Доступные команды:", ", ".join([f"/{name}" for name in files.keys()]))
    print("=" * 50)
    print("Нажмите Ctrl+C для остановки")
    
    app.run_polling()

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\nБот остановлен")
    except Exception as e:
        print(f"Ошибка при запуске: {e}")
