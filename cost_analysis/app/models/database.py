import sqlite3
import pandas as pd
from contextlib import contextmanager
import os

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.init_db()
    
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с БД"""
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()
    
    def init_db(self):
        """Создание таблиц при первом запуске"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        with self.get_connection() as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS expenses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    datetime TEXT NOT NULL,
                    category TEXT NOT NULL,
                    value REAL NOT NULL,
                    description TEXT
                )
            ''')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_datetime ON expenses(datetime)')
            conn.execute('CREATE INDEX IF NOT EXISTS idx_category ON expenses(category)')
            conn.commit()
    
    def clear_all(self):
        """Очистка всех данных"""
        with self.get_connection() as conn:
            conn.execute('DELETE FROM expenses')
            conn.commit()
    
    def get_stats(self):
        """Получение статистики"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM expenses')
            total_records = cursor.fetchone()[0]
            
            if total_records == 0:
                return {
                    'data_exists': False,
                    'total_records': 0,
                    'total_amount': 0,
                    'total_categories': 0,
                    'min_date': None,
                    'max_date': None
                }
            
            cursor.execute('SELECT SUM(value) FROM expenses')
            total_amount = cursor.fetchone()[0] or 0
            
            cursor.execute('SELECT COUNT(DISTINCT category) FROM expenses')
            total_categories = cursor.fetchone()[0]
            
            cursor.execute('SELECT MIN(datetime), MAX(datetime) FROM expenses')
            min_date, max_date = cursor.fetchone()
            
            return {
                'data_exists': True,
                'total_records': total_records,
                'total_amount': round(total_amount, 2),
                'total_categories': total_categories,
                'min_date': min_date,
                'max_date': max_date
            }
    
    def import_from_excel(self, file_path):
        """Импорт из Excel"""
        try:
            df = pd.read_excel(file_path, sheet_name='Report')
            df = df.dropna(subset=['Category', 'Value'])
            df['Value'] = pd.to_numeric(df['Value'], errors='coerce')
            df = df.dropna(subset=['Value'])
            df['DateTime'] = pd.to_datetime(df['DateTime'], errors='coerce')
            df = df.dropna(subset=['DateTime'])
            
            if df.empty:
                return False, "Файл не содержит корректных данных"
            
            with self.get_connection() as conn:
                conn.execute('DELETE FROM expenses')
                
                for _, row in df.iterrows():
                    conn.execute('''
                        INSERT INTO expenses (datetime, category, value, description)
                        VALUES (?, ?, ?, ?)
                    ''', (
                        row['DateTime'].strftime('%Y-%m-%d %H:%M:%S'),
                        row['Category'],
                        row['Value'],
                        row['Description'] if pd.notna(row['Description']) else ''
                    ))
                conn.commit()
            
            return True, f"Загружено {len(df)} записей"
            
        except Exception as e:
            return False, f"Ошибка: {str(e)}"
    
    def get_expenses(self, year=None, month=None):
        """Получение расходов с фильтрацией"""
        query = 'SELECT category, SUM(value) as amount FROM expenses WHERE 1=1'
        params = []
        
        if year:
            query += ' AND strftime("%Y", datetime) = ?'
            params.append(str(year))
        
        if month:
            query += ' AND strftime("%m", datetime) = ?'
            params.append(f"{month:02d}")
        
        query += ' GROUP BY category ORDER BY amount DESC'
        
        with self.get_connection() as conn:
            df = pd.read_sql_query(query, conn, params=params)
            
            if df.empty:
                return None, 0
            
            total = df['amount'].sum()
            return df, total
    
    def export_to_excel(self):
        """Экспорт в Excel"""
        with self.get_connection() as conn:
            df = pd.read_sql_query('SELECT datetime, category, value, description FROM expenses ORDER BY datetime', conn)
            
            if df.empty:
                return None
            
            return df