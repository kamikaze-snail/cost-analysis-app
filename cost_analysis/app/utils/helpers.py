from collections import defaultdict
import re
from categories import CATEGORIES

def parse_line_with_category(line):
    """Парсит строку формата: 'сумма(дата) категория'"""
    line = line.strip()
    if not line:
        return None, None
    
    match = re.search(r'(\d+)', line)
    if not match:
        return None, None
    
    amount = int(match.group(1))
    
    # Ищем категорию
    for key, value in CATEGORIES.items():
        if value.lower() in line.lower():
            return amount, key
    
    return amount, "misc"

def format_currency(amount):
    """Форматирование суммы"""
    return f"{amount:,.2f} руб."

def get_month_name(month):
    """Получение названия месяца"""
    months = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
              'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']
    return months[month - 1] if 1 <= month <= 12 else None

def allowed_file(filename, allowed_extensions):
    """Проверка разрешенного расширения файла"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def calculate_percentage(amount, total):
    """Расчет процента"""
    return (amount / total * 100) if total > 0 else 0
