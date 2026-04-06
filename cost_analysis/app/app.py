from flask import Flask, render_template, request, send_file, session, redirect, url_for
import pandas as pd
import io
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-in-production'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max

# Создаём папку для загрузок, если её нет
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Русские названия месяцев
MONTHS_RU = ['Янв', 'Фев', 'Мар', 'Апр', 'Май', 'Июн', 'Июл', 'Авг', 'Сен', 'Окт', 'Ноя', 'Дек']


def load_and_prepare_data(filepath):
    """Загружает и подготавливает данные из Excel файла"""
    df = pd.read_excel(filepath, sheet_name='Report')
    
    # Оставляем только нужные колонки
    df = df[['DateTime', 'Category', 'Value', 'Description']].copy()
    
    # Преобразуем дату
    df['DateTime'] = pd.to_datetime(df['DateTime'])
    df = df.sort_values('DateTime')
    
    # Очищаем значения
    df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
    df = df.dropna(subset=['Value'])
    
    # Создаём дополнительные колонки
    df['Year'] = df['DateTime'].dt.year
    df['Month'] = df['DateTime'].dt.month
    df['YearMonth'] = df['DateTime'].dt.to_period('M')
    df['MonthName'] = df['DateTime'].dt.month.map(lambda x: MONTHS_RU[x-1])
    df['Day'] = df['DateTime'].dt.day
    
    return df


def get_summary_stats(df):
    """Получает общую статистику по расходам"""
    total = df['Value'].sum()
    avg_monthly = df.groupby('YearMonth')['Value'].sum().mean()
    
    # Расходы по годам
    by_year = df.groupby('Year')['Value'].sum().to_dict()
    
    # Топ категорий
    top_categories = df.groupby('Category')['Value'].sum().sort_values(ascending=False).head(10).to_dict()
    
    # Расходы по месяцам (средние за всё время)
    by_month = df.groupby('Month')['Value'].sum() / df['Year'].nunique()
    by_month = {MONTHS_RU[i-1]: val for i, val in by_month.items()}
    
    # Статистика по дням недели
    df['Weekday'] = df['DateTime'].dt.dayofweek
    weekdays = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
    by_weekday = df.groupby('Weekday')['Value'].sum().to_dict()
    by_weekday = {weekdays[k]: v for k, v in by_weekday.items()}
    
    return {
        'total': total,
        'avg_monthly': avg_monthly,
        'by_year': by_year,
        'top_categories': top_categories,
        'by_month': by_month,
        'by_weekday': by_weekday,
        'record_count': len(df)
    }


def filter_data(df, category=None, year=None, month=None, start_date=None, end_date=None):
    """Фильтрует данные по заданным параметрам"""
    filtered = df.copy()
    
    if category:
        filtered = filtered[filtered['Category'] == category]
    if year:
        filtered = filtered[filtered['Year'] == int(year)]
    if month:
        filtered = filtered[filtered['Month'] == int(month)]
    if start_date:
        filtered = filtered[filtered['DateTime'] >= pd.to_datetime(start_date)]
    if end_date:
        filtered = filtered[filtered['DateTime'] <= pd.to_datetime(end_date)]
    
    return filtered


@app.route('/')
def index():
    """Главная страница с загрузкой файла"""
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_file():
    """Загружает файл и показывает отчёт"""
    if 'file' not in request.files:
        return redirect(url_for('index'))
    
    file = request.files['file']
    if file.filename == '':
        return redirect(url_for('index'))
    
    if file and (file.filename.endswith('.xls') or file.filename.endswith('.xlsx')):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # Загружаем и подготавливаем данные
        df = load_and_prepare_data(filepath)
        
        # Сохраняем данные в сессии для последующей фильтрации
        session['data'] = df.to_json(date_format='iso', orient='split')
        
        # Получаем статистику
        stats = get_summary_stats(df)
        
        # Список категорий для фильтра
        categories = sorted(df['Category'].unique())
        years = sorted(df['Year'].unique(), reverse=True)
        
        # Таблица с детальными расходами
        table_data = df[['DateTime', 'Category', 'Value', 'Description']].copy()
        table_data['DateTime'] = table_data['DateTime'].dt.strftime('%d.%m.%Y %H:%M')
        table_data = table_data.sort_values('DateTime', ascending=False).head(50)
        
        return render_template('report.html', 
                               stats=stats,
                               categories=categories,
                               years=years,
                               table_data=table_data.to_dict('records'))
    
    return redirect(url_for('index'))


@app.route('/filter', methods=['POST'])
def filter_report():
    """Фильтрует данные и показывает обновлённый отчёт"""
    data_json = session.get('data')
    if not data_json:
        return redirect(url_for('index'))
    
    df = pd.read_json(data_json, orient='split')
    
    # Получаем параметры фильтрации
    category = request.form.get('category')
    year = request.form.get('year')
    month = request.form.get('month')
    start_date = request.form.get('start_date')
    end_date = request.form.get('end_date')
    
    # Применяем фильтры
    filtered_df = filter_data(df, category, year, month, start_date, end_date)
    
    if len(filtered_df) == 0:
        return render_template('report.html', 
                               error="Нет данных для выбранных фильтров",
                               categories=sorted(df['Category'].unique()),
                               years=sorted(df['Year'].unique(), reverse=True))
    
    # Получаем статистику для отфильтрованных данных
    stats = get_summary_stats(filtered_df)
    
    # Таблица с детальными расходами
    table_data = filtered_df[['DateTime', 'Category', 'Value', 'Description']].copy()
    table_data['DateTime'] = table_data['DateTime'].dt.strftime('%d.%m.%Y %H:%M')
    table_data = table_data.sort_values('DateTime', ascending=False).head(50)
    
    categories = sorted(df['Category'].unique())
    years = sorted(df['Year'].unique(), reverse=True)
    
    return render_template('report.html',
                           stats=stats,
                           categories=categories,
                           years=years,
                           table_data=table_data.to_dict('records'))


@app.route('/download')
def download_data():
    """Скачивает данные в Excel"""
    data_json = session.get('data')
    if not data_json:
        return redirect(url_for('index'))
    
    df = pd.read_json(data_json, orient='split')
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Расходы', index=False)
    
    output.seek(0)
    return send_file(output, download_name='expenses_analysis.xlsx', as_attachment=True)


if __name__ == '__main__':
    app.run(debug=True)