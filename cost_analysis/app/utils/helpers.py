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