# Create admin user script
import sqlite3
import bcrypt
import os

def create_admin_user():
    # Check if database exists
    db_path = 'phone_directory.db'
    if os.path.exists(db_path):
        os.remove(db_path)  # Remove existing database
    
    # Create new database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create users table
    cursor.executescript('''
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
    ''')
    
    # Create admin user
    username = 'admin'
    password = 'admin123'
    full_name = 'مدير النظام'
    role = 'admin'
    
    # Hash password properly
    salt = bcrypt.gensalt()
    hashed_password = bcrypt.hashpw(password.encode('utf-8'), salt)
    
    try:
        cursor.execute('''
            INSERT INTO users (username, password, full_name, role)
            VALUES (?, ?, ?, ?)
        ''', (username, hashed_password, full_name, role))
        conn.commit()
        print("تم إنشاء حساب المسؤول بنجاح")
        print(f"اسم المستخدم: {username}")
        print(f"كلمة المرور: {password}")
    except Exception as e:
        print(f"حدث خطأ: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    create_admin_user()