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

def process_calculation(data, category_filter="all"):
    """Обрабатывает данные и возвращает суммы по категориям"""
    rint(f"=== process_calculation called with data: '{data}' ===")
    items = []
    category_totals = defaultdict(lambda: {"sum": 0, "count": 0})
    
    lines = data.strip().split('\n')
    for line in lines:
        amount, category = parse_line_with_category(line)
        if amount is not None:
            items.append({"amount": amount, "category": category})
            category_totals[category]["sum"] += amount
            category_totals[category]["count"] += 1
    
    if category_filter != "all":
        filtered_sum = sum(item["amount"] for item in items if item["category"] == category_filter)
        filtered_count = sum(1 for item in items if item["category"] == category_filter)
    else:
        filtered_sum = sum(item["amount"] for item in items)
        filtered_count = len(items)
    
    return {
        "total_sum": filtered_sum,
        "total_count": filtered_count,
        "category_totals": dict(category_totals),
        "all_items": items
    }

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

def parse_line_with_category(line):
    """Парсит строку формата: 'сумма(дата) категория'"""
    line = line.strip()
    if not line:
        return None, None
    
    match = re.search(r'(\d+)', line)
    if not match:
        return None, None
    
    amount = int(match.group(1))
    
    # Отладка: выводим строку для проверки
    print(f"DEBUG: line = '{line}', amount = {amount}")
    
    # Ищем категорию
    for key, value in CATEGORIES.items():
        if value.lower() in line.lower():
            print(f"DEBUG: found category '{value}' -> key '{key}'")
            return amount, key
    
    print(f"DEBUG: no category found, defaulting to 'misc'")
    return amount, "misc"
