import sqlite3
import os
import bcrypt

# Database path
DB_PATH = 'phone_directory.db'

def setup_database():
    print(f"Setting up database at: {DB_PATH}")
    
    # Create database and tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    print("Creating tables...")
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
    
    # Check if admin user already exists
    cursor.execute('SELECT id FROM users WHERE username = ?', ('admin',))
    admin_exists = cursor.fetchone()
    
    if not admin_exists:
        print("Creating admin user...")
        # Create admin user
        username = 'admin'
        password = 'admin123'
        full_name = 'مدير النظام'
        role = 'admin'
        
        # Hash the password
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # Insert admin user
        cursor.execute(
            'INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)',
            (username, hashed_password, full_name, role)
        )
        conn.commit()
        print(f"Admin user created successfully:")
        print(f"  Username: {username}")
        print(f"  Password: {password}")
    else:
        print("Admin user already exists.")
    
    # Verify tables were created
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("\nCreated tables:")
    for table in tables:
        print(f"  - {table[0]}")
    
    conn.close()
    print("\nDatabase setup complete!")

if __name__ == "__main__":
    setup_database()