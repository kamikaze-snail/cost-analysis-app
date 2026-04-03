import os
from flask import Flask, render_template, request, redirect, url_for, flash, send_file
from werkzeug.utils import secure_filename

from flask import render_template  # вместо render_template_string
from categories import CATEGORIES  # импортируйте категории

from config import config
from models.database import Database
from utils.helpers import get_month_name, allowed_file, calculate_percentage

from utils.helpers import get_month_name, allowed_file, calculate_percentage, process_calculation, parse_line_with_category

# Создаем приложение
app = Flask(__name__)
app.config.from_object(config['development'])

# Инициализация базы данных
db = Database(app.config['DATABASE'])

# Создаем папку для загрузок
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Названия месяцев
MONTH_NAMES = ['Январь', 'Февраль', 'Март', 'Апрель', 'Май', 'Июнь',
               'Июль', 'Август', 'Сентябрь', 'Октябрь', 'Ноябрь', 'Декабрь']

# --- Маршруты ---
@app.route('/', methods=['GET', 'POST'])
def index():
    result = None
    count = None
    totals_by_category = None
    selected_category = "all"
    error = None
    
    if request.method == 'POST':
        data = request.form.get('data', '')
        selected_category = request.form.get('category_filter', 'all')
        
        try:
            calculation = process_calculation(data, selected_category)
            result = calculation["total_sum"]
            count = calculation["total_count"]
            totals_by_category = calculation["category_totals"]
        except Exception as e:
            error = str(e)
    
    return render_template(
        'index.html',
        result=result,
        count=count,
        categories=CATEGORIES,
        selected_category=selected_category,
        totals_by_category=totals_by_category,
        error=error
    )

@app.route('/upload')
def upload_page():
    """Страница загрузки"""
    return render_template('upload.html', month_names=MONTH_NAMES)

@app.route('/upload', methods=['POST'])
def upload_file():
    """Обработка загрузки файла"""
    if 'file' not in request.files:
        flash('Файл не выбран', 'error')
        return redirect(url_for('upload_page'))
    
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран', 'error')
        return redirect(url_for('upload_page'))
    
    if not allowed_file(file.filename, app.config['ALLOWED_EXTENSIONS']):
        flash('Неподдерживаемый формат. Используйте .xls или .xlsx', 'error')
        return redirect(url_for('upload_page'))
    
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    
    success, message = db.import_from_excel(filepath)
    os.remove(filepath)
    
    if success:
        flash(message, 'success')
    else:
        flash(message, 'error')
    
    return redirect(url_for('index'))

@app.route('/filter')
def filter_expenses():
    """Фильтрация расходов"""
    year = request.args.get('year', type=int)
    month = request.args.get('month', type=int)
    
    if month and (month < 1 or month > 12):
        flash('Месяц должен быть от 1 до 12', 'error')
        return redirect(url_for('index'))
    
    df, total = db.get_expenses(year, month)
    
    table_data = []
    if df is not None:
        for _, row in df.iterrows():
            table_data.append({
                'category': row['category'],
                'amount': row['amount'],
                'percentage': calculate_percentage(row['amount'], total)
            })
    
    stats = db.get_stats()
    
    # Формируем заголовок
    title = "Все расходы"
    if year and month:
        title = f"Расходы за {MONTH_NAMES[month-1]} {year} г."
    elif year:
        title = f"Расходы за {year} г."
    
    return render_template('index.html',
                         stats=stats,
                         table_data=table_data,
                         total_filtered=total,
                         month_names=MONTH_NAMES,
                         title=title)

@app.route('/stats')
def stats():
    """Страница статистики"""
    from models.database import Database
    import pandas as pd
    
    conn_db = Database(app.config['DATABASE'])
    
    with conn_db.get_connection() as conn:
        # Статистика по месяцам
        query_monthly = '''
            SELECT 
                strftime('%Y-%m', datetime) as month,
                SUM(value) as total
            FROM expenses
            GROUP BY strftime('%Y-%m', datetime)
            ORDER BY month DESC
            LIMIT 12
        '''
        monthly_stats = pd.read_sql_query(query_monthly, conn)
        
        # Топ категорий
        query_categories = '''
            SELECT category, SUM(value) as total
            FROM expenses
            GROUP BY category
            ORDER BY total DESC
            LIMIT 10
        '''
        top_categories = pd.read_sql_query(query_categories, conn)
    
    return render_template('stats.html',
                         monthly_stats=monthly_stats,
                         top_categories=top_categories,
                         month_names=MONTH_NAMES)

@app.route('/export')
def export():
    """Экспорт данных в Excel"""
    import tempfile
    from datetime import datetime
    
    df = db.export_to_excel()
    
    if df is None or df.empty:
        flash('Нет данных для экспорта', 'error')
        return redirect(url_for('index'))
    
    # Создаем временный файл
    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx')
    df.to_excel(temp_file.name, index=False, sheet_name='Expenses')
    
    return send_file(
        temp_file.name,
        as_attachment=True,
        download_name=f'expenses_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@app.errorhandler(404)
def not_found(error):
    """Страница 404"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Страница 500"""
    flash('Внутренняя ошибка сервера', 'error')
    return redirect(url_for('index'))
	
# --- Запуск ---
if __name__ == '__main__':
    print("=" * 50)
    print("🚀 Запуск приложения для анализа расходов")
    print("=" * 50)
    print(f"📁 База данных: {app.config['DATABASE']}")
    print(f"📁 Папка загрузок: {app.config['UPLOAD_FOLDER']}")
    print("=" * 50)
    print("🌐 Откройте в браузере: http://127.0.0.1:5000")
    print("=" * 50)
    
    app.run(debug=True, host='0.0.0.0', port=5000)
