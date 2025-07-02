import sqlite3
import os
import bcrypt
from app import app

def setup_database():
    db_path = app.config['DATABASE']
    
    # Create database file if it doesn't exist
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        # Create tables
        cursor.executescript('''
        -- جدول المستخدمين
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            full_name TEXT NOT NULL,
            role TEXT NOT NULL,
            last_login TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- جدول الإدارات
        CREATE TABLE IF NOT EXISTS departments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- جدول الموظفين
        CREATE TABLE IF NOT EXISTS employees (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            extension TEXT UNIQUE NOT NULL,
            department_id INTEGER NOT NULL,
            job_title TEXT,
            email TEXT,
            notes TEXT,
            created_by INTEGER,
            updated_by INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (department_id) REFERENCES departments (id),
            FOREIGN KEY (created_by) REFERENCES users (id),
            FOREIGN KEY (updated_by) REFERENCES users (id)
        );
        
        -- جدول سجل النشاط
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            action_type TEXT NOT NULL,
            table_name TEXT NOT NULL,
            record_id INTEGER,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
        ''')
        
        # Create admin user
        try:
            username = 'admin'
            password = 'admin123'
            full_name = 'مدير النظام'
            role = 'admin'
            
            # تشفير كلمة المرور
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor.execute('''
                INSERT INTO users (username, password, full_name, role)
                VALUES (?, ?, ?, ?)
            ''', (username, hashed_password, full_name, role))
            conn.commit()
            print("تم إنشاء حساب المسؤول بنجاح")
            print(f"اسم المستخدم: {username}")
            print(f"كلمة المرور: {password}")
        except sqlite3.IntegrityError:
            print("حساب المسؤول موجود بالفعل")
        except Exception as e:
            print(f"حدث خطأ أثناء إنشاء حساب المسؤول: {e}")

if __name__ == "__main__":
    setup_database()