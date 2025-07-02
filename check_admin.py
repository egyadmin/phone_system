# create_admin.py
import sqlite3
import bcrypt

def create_admin():
    try:
        conn = sqlite3.connect('phone_directory.db')
        
        # Check if admin already exists
        cursor = conn.execute('SELECT id FROM users WHERE username = ?', ('admin',))
        if cursor.fetchone():
            print("Admin user already exists")
            conn.close()
            return
        
        # Create admin user
        username = 'admin'
        password = 'admin123'
        full_name = 'مدير النظام'
        role = 'admin'
        
        # Ensure proper password hashing
        hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        conn.execute(
            'INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)',
            (username, hashed_password, full_name, role)
        )
        conn.commit()
        
        print("Admin user created successfully")
        print(f"Username: {username}")
        print(f"Password: {password}")
        
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    create_admin()