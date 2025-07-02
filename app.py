from flask import Flask, render_template, request, redirect, url_for, flash, session, g
import sqlite3
import os
import bcrypt
import pandas as pd
import json
from datetime import datetime
import csv
import io
from functools import wraps

# تهيئة التطبيق
app = Flask(__name__)
app.secret_key = 'sajco_phone_directory_secret_key'
app.config['DATABASE'] = 'phone_directory.db'

# إضافة دالة للحصول على التاريخ الحالي في قوالب Jinja
@app.context_processor
def utility_processor():
    return {'now': datetime.now()}

# إنشاء قاعدة البيانات وتهيئتها
def init_db():
    db_path = app.config['DATABASE']
    db_exists = os.path.exists(db_path)
    
    # استخدام مدير سياق لضمان إغلاق الاتصال في جميع الحالات
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()

        if not db_exists:
            try:
                # إنشاء الجداول يدوياً إذا لم يتم العثور على ملف المخطط
                schema_file = 'database_schema.sql'
                
                if os.path.exists(schema_file):
                    with open(schema_file, 'r', encoding='utf-8') as f:
                        cursor.executescript(f.read())
                else:
                    # إنشاء جداول قاعدة البيانات يدوياً
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
                print("تم إنشاء قاعدة البيانات بنجاح")

                # إنشاء المستخدم المسؤول إذا لم يكن موجود
                try:
                    username = 'admin'
                    password = 'admin123'
                    full_name = 'مدير النظام'
                    role = 'admin'

                    # تشفير كلمة المرور - ضمان تخزينها كـ bytes ثم تحويلها إلى string للتخزين
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
            except Exception as e:
                print(f"حدث خطأ أثناء إنشاء قاعدة البيانات: {e}")
        else:
            print("قاعدة البيانات موجودة بالفعل")

# دالة للاتصال بقاعدة البيانات
def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

# دالة لإغلاق اتصال قاعدة البيانات عند انتهاء الطلب
@app.teardown_appcontext
def close_db(error):
    if 'db' in g:
        g.db.close()

# تأكد من وجود قاعدة البيانات قبل كل طلب
@app.before_request
def ensure_db_exists():
    if not os.path.exists(app.config['DATABASE']):
        with app.app_context():
            init_db()

# تسجيل نشاط في السجل
def log_activity(user_id, action_type, table_name, record_id=None, details=None):
    try:
        conn = get_db()
        conn.execute(
            'INSERT INTO activity_log (user_id, action_type, table_name, record_id, details) VALUES (?, ?, ?, ?, ?)',
            (user_id, action_type, table_name, record_id, details)
        )
        conn.commit()
    except Exception as e:
        print(f"خطأ في تسجيل النشاط: {e}")
        conn.rollback()

# التحقق من تسجيل الدخول
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            flash('يرجى تسجيل الدخول للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# التحقق من صلاحيات المدير
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_role' not in session or session['user_role'] != 'admin':
            flash('ليس لديك صلاحية للوصول إلى هذه الصفحة', 'error')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

# الصفحة الرئيسية
@app.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    
    try:
        conn = get_db()
        employees = conn.execute('''
            SELECT e.id, e.name, e.extension, e.job_title, d.name as department_name
            FROM employees e
            JOIN departments d ON e.department_id = d.id
            ORDER BY e.name
        ''').fetchall()
        
        departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
        
        return render_template('index.html', employees=employees, departments=departments)
    except Exception as e:
        flash(f'حدث خطأ: {e}', 'error')
        return render_template('index.html', employees=[], departments=[])

# صفحة تسجيل الدخول
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db()
            user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
            
            if user:
                # معالجة متناسقة لكلمة المرور المخزنة
                stored_password = user['password']
                
                # تأكد من أن كلمة المرور المخزنة هي bytes أو قم بترميزها
                if isinstance(stored_password, str):
                    stored_password = stored_password.encode('utf-8')
                
                # التحقق من كلمة المرور
                if bcrypt.checkpw(password.encode('utf-8'), stored_password):
                    session['user_id'] = user['id']
                    session['username'] = user['username']
                    session['user_role'] = user['role']
                    session['full_name'] = user['full_name']
                    
                    conn.execute('UPDATE users SET last_login = CURRENT_TIMESTAMP WHERE id = ?', (user['id'],))
                    conn.commit()
                    
                    log_activity(user['id'], 'login', 'users', user['id'], f'تسجيل دخول المستخدم {username}')
                    
                    flash('تم تسجيل الدخول بنجاح', 'success')
                    return redirect(url_for('index'))
                else:
                    flash('كلمة المرور غير صحيحة', 'error')
            else:
                flash('اسم المستخدم غير موجود', 'error')
        except Exception as e:
            flash(f'خطأ في عملية تسجيل الدخول: {e}', 'error')
    
    return render_template('login.html')

# تسجيل الخروج
@app.route('/logout')
def logout():
    if 'user_id' in session:
        log_activity(session['user_id'], 'logout', 'users', session['user_id'], f'تسجيل خروج المستخدم {session["username"]}')
        session.clear()
    return redirect(url_for('login'))

# إضافة موظف جديد
@app.route('/employees/add', methods=['GET', 'POST'])
@login_required
def add_employee():
    if request.method == 'POST':
        name = request.form['name']
        extension = request.form['extension']
        department_id = request.form['department_id']
        job_title = request.form['job_title']
        email = request.form.get('email', '')
        notes = request.form.get('notes', '')
        
        try:
            conn = get_db()
            
            # التحقق من عدم تكرار رقم التحويلة
            existing = conn.execute('SELECT id FROM employees WHERE extension = ?', (extension,)).fetchone()
            if existing:
                flash('رقم التحويلة موجود بالفعل', 'error')
                departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
                return render_template('add_employee.html', departments=departments)
            
            cursor = conn.execute(
                '''INSERT INTO employees 
                   (name, extension, department_id, job_title, email, notes, created_by, updated_by) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                (name, extension, department_id, job_title, email, notes, session['user_id'], session['user_id'])
            )
            employee_id = cursor.lastrowid
            conn.commit()
            
            # تسجيل النشاط
            log_activity(
                session['user_id'], 
                'add', 
                'employees', 
                employee_id, 
                f'إضافة موظف جديد: {name} - التحويلة: {extension}'
            )
            
            flash('تمت إضافة الموظف بنجاح', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            conn.rollback()
            flash(f'حدث خطأ أثناء إضافة الموظف: {e}', 'error')
    
    try:
        conn = get_db()
        departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
        return render_template('add_employee.html', departments=departments)
    except Exception as e:
        flash(f'حدث خطأ: {e}', 'error')
        return redirect(url_for('index'))

# تعديل بيانات موظف
@app.route('/employees/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_employee(id):
    conn = get_db()
    
    if request.method == 'POST':
        name = request.form['name']
        extension = request.form['extension']
        department_id = request.form['department_id']
        job_title = request.form['job_title']
        email = request.form.get('email', '')
        notes = request.form.get('notes', '')
        
        try:
            # التحقق من عدم تكرار رقم التحويلة (باستثناء الموظف الحالي)
            existing = conn.execute('SELECT id FROM employees WHERE extension = ? AND id != ?', (extension, id)).fetchone()
            if existing:
                flash('رقم التحويلة موجود بالفعل', 'error')
                employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
                departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
                return render_template('edit_employee.html', employee=employee, departments=departments)
            
            conn.execute(
                '''UPDATE employees 
                   SET name = ?, extension = ?, department_id = ?, job_title = ?, 
                       email = ?, notes = ?, updated_at = CURRENT_TIMESTAMP, updated_by = ? 
                   WHERE id = ?''',
                (name, extension, department_id, job_title, email, notes, session['user_id'], id)
            )
            conn.commit()
            
            # تسجيل النشاط
            log_activity(
                session['user_id'], 
                'edit', 
                'employees', 
                id, 
                f'تعديل بيانات الموظف: {name} - التحويلة: {extension}'
            )
            
            flash('تم تحديث بيانات الموظف بنجاح', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            conn.rollback()
            flash(f'حدث خطأ أثناء تحديث بيانات الموظف: {e}', 'error')
            return redirect(url_for('index'))
    
    try:
        employee = conn.execute('SELECT * FROM employees WHERE id = ?', (id,)).fetchone()
        if not employee:
            flash('الموظف غير موجود', 'error')
            return redirect(url_for('index'))
        
        departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
        return render_template('edit_employee.html', employee=employee, departments=departments)
    except Exception as e:
        flash(f'حدث خطأ: {e}', 'error')
        return redirect(url_for('index'))

# حذف موظف
@app.route('/employees/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_employee(id):
    try:
        conn = get_db()
        employee = conn.execute('SELECT name, extension FROM employees WHERE id = ?', (id,)).fetchone()
        
        if not employee:
            flash('الموظف غير موجود', 'error')
            return redirect(url_for('index'))
        
        conn.execute('DELETE FROM employees WHERE id = ?', (id,))
        conn.commit()
        
        # تسجيل النشاط
        log_activity(
            session['user_id'], 
            'delete', 
            'employees', 
            id, 
            f'حذف الموظف: {employee["name"]} - التحويلة: {employee["extension"]}'
        )
        
        flash('تم حذف الموظف بنجاح', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'حدث خطأ أثناء حذف الموظف: {e}', 'error')
    
    return redirect(url_for('index'))

# إدارة الإدارات
@app.route('/departments', methods=['GET'])
@login_required
@admin_required
def departments():
    try:
        conn = get_db()
        departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
        
        # حساب عدد الموظفين في كل إدارة
        department_list = []
        for dept in departments:
            count = conn.execute('SELECT COUNT(*) as count FROM employees WHERE department_id = ?', (dept['id'],)).fetchone()
            
            # Create a new dictionary with the department data and employee count
            dept_dict = dict(dept)  # Convert sqlite3.Row to a dictionary
            dept_dict['employee_count'] = count['count']
            department_list.append(dept_dict)
        
        return render_template('departments.html', departments=department_list)
    except Exception as e:
        flash(f'حدث خطأ: {e}', 'error')
        return redirect(url_for('index'))

# إضافة إدارة جديدة
@app.route('/departments/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_department():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form.get('description', '')
        
        try:
            conn = get_db()
            
            # التحقق من عدم تكرار اسم الإدارة
            existing = conn.execute('SELECT id FROM departments WHERE name = ?', (name,)).fetchone()
            if existing:
                flash('اسم الإدارة موجود بالفعل', 'error')
                return render_template('add_department.html')
            
            cursor = conn.execute(
                'INSERT INTO departments (name, description) VALUES (?, ?)',
                (name, description)
            )
            department_id = cursor.lastrowid
            conn.commit()
            
            # تسجيل النشاط
            log_activity(
                session['user_id'], 
                'add', 
                'departments', 
                department_id, 
                f'إضافة إدارة جديدة: {name}'
            )
            
            flash('تمت إضافة الإدارة بنجاح', 'success')
            return redirect(url_for('departments'))
        except Exception as e:
            conn.rollback()
            flash(f'حدث خطأ أثناء إضافة الإدارة: {e}', 'error')
    
    return render_template('add_department.html')

# تعديل إدارة
@app.route('/departments/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_department(id):
    try:
        conn = get_db()
        department = conn.execute('SELECT * FROM departments WHERE id = ?', (id,)).fetchone()

        if department is None:
            flash('القسم غير موجود', 'error')
            return redirect(url_for('departments'))

        if request.method == 'POST':
            name = request.form['name']
            description = request.form['description']

            # Check for duplicate department name (excluding the current department)
            existing_department = conn.execute('SELECT id FROM departments WHERE name = ? AND id != ?', (name, id)).fetchone()
            if existing_department:
                flash('اسم القسم موجود بالفعل', 'error')
                return render_template('edit_department.html', department=department)

            conn.execute('UPDATE departments SET name = ?, description = ? WHERE id = ?', (name, description, id))
            conn.commit()
            flash('تم تحديث القسم بنجاح', 'success')
            return redirect(url_for('departments'))

        return render_template('edit_department.html', department=department)

    except Exception as e:
        conn.rollback()
        flash(f'حدث خطأ: {e}', 'error')
        return redirect(url_for('departments'))

# حذف إدارة
@app.route('/departments/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_department(id):
    try:
        conn = get_db()
        
        # التحقق من عدم وجود موظفين في الإدارة
        employee_count = conn.execute('SELECT COUNT(*) as count FROM employees WHERE department_id = ?', (id,)).fetchone()
        if employee_count['count'] > 0:
            flash('لا يمكن حذف الإدارة لأنها تحتوي على موظفين', 'error')
            return redirect(url_for('departments'))
        
        department = conn.execute('SELECT name FROM departments WHERE id = ?', (id,)).fetchone()
        if not department:
            flash('الإدارة غير موجودة', 'error')
            return redirect(url_for('departments'))
        
        conn.execute('DELETE FROM departments WHERE id = ?', (id,))
        conn.commit()
        
        # تسجيل النشاط
        log_activity(
            session['user_id'], 
            'delete', 
            'departments', 
            id, 
            f'حذف الإدارة: {department["name"]}'
        )
        
        flash('تم حذف الإدارة بنجاح', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'حدث خطأ أثناء حذف الإدارة: {e}', 'error')
    
    return redirect(url_for('departments'))

# إدارة المستخدمين
@app.route('/users', methods=['GET'])
@login_required
@admin_required
def users():
    try:
        conn = get_db()
        users = conn.execute('SELECT * FROM users ORDER BY username').fetchall()
        return render_template('users.html', users=users)
    except Exception as e:
        flash(f'حدث خطأ: {e}', 'error')
        return redirect(url_for('index'))

# إضافة مستخدم جديد
@app.route('/users/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_user():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        full_name = request.form['full_name']
        role = request.form['role']
        
        try:
            conn = get_db()
            
            # التحقق من عدم تكرار اسم المستخدم
            existing = conn.execute('SELECT id FROM users WHERE username = ?', (username,)).fetchone()
            if existing:
                flash('اسم المستخدم موجود بالفعل', 'error')
                return render_template('add_user.html')
            
            # تشفير كلمة المرور وتخزينها كـ string
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            
            cursor = conn.execute(
                'INSERT INTO users (username, password, full_name, role) VALUES (?, ?, ?, ?)',
                (username, hashed_password, full_name, role)
            )
            user_id = cursor.lastrowid
            conn.commit()
            
            # تسجيل النشاط
            log_activity(
                session['user_id'], 
                'add', 
                'users', 
                user_id, 
                f'إضافة مستخدم جديد: {username} - الدور: {role}'
            )
            
            flash('تمت إضافة المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            conn.rollback()
            flash(f'حدث خطأ أثناء إضافة المستخدم: {e}', 'error')
    
    return render_template('add_user.html')

# تعديل مستخدم
@app.route('/users/edit/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    # لا يمكن تعديل المستخدم الحالي
    if id == session['user_id']:
        flash('لا يمكنك تعديل حسابك الحالي من هنا', 'error')
        return redirect(url_for('users'))
    
    conn = get_db()
    
    if request.method == 'POST':
        username = request.form['username']
        full_name = request.form['full_name']
        role = request.form['role']
        password = request.form.get('password', '')
        
        try:
            # التحقق من عدم تكرار اسم المستخدم (باستثناء المستخدم الحالي)
            existing = conn.execute('SELECT id FROM users WHERE username = ? AND id != ?', (username, id)).fetchone()
            if existing:
                flash('اسم المستخدم موجود بالفعل', 'error')
                user = conn.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
                return render_template('edit_user.html', user=user)
            
            if password:
                # تشفير كلمة المرور الجديدة وتخزينها كـ string
                hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
                conn.execute(
                    'UPDATE users SET username = ?, password = ?, full_name = ?, role = ? WHERE id = ?',
                    (username, hashed_password, full_name, role, id)
                )
            else:
                conn.execute(
                    'UPDATE users SET username = ?, full_name = ?, role = ? WHERE id = ?',
                    (username, full_name, role, id)
                )
            
            conn.commit()
            
            # تسجيل النشاط
            log_activity(
                session['user_id'], 
                'edit', 
                'users', 
                id, 
                f'تعديل المستخدم: {username} - الدور: {role}'
            )
            
            flash('تم تحديث المستخدم بنجاح', 'success')
            return redirect(url_for('users'))
        except Exception as e:
            conn.rollback()
            flash(f'حدث خطأ أثناء تحديث المستخدم: {e}', 'error')
    
    try:
        user = conn.execute('SELECT * FROM users WHERE id = ?', (id,)).fetchone()
        if not user:
            flash('المستخدم غير موجود', 'error')
            return redirect(url_for('users'))
        
        return render_template('edit_user.html', user=user)
    except Exception as e:
        flash(f'حدث خطأ: {e}', 'error')
        return redirect(url_for('users'))

# حذف مستخدم
@app.route('/users/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_user(id):
    # لا يمكن حذف المستخدم الحالي
    if id == session['user_id']:
        flash('لا يمكنك حذف حسابك الحالي', 'error')
        return redirect(url_for('users'))
    
    try:
        conn = get_db()
        user = conn.execute('SELECT username FROM users WHERE id = ?', (id,)).fetchone()
        
        if not user:
            flash('المستخدم غير موجود', 'error')
            return redirect(url_for('users'))
        
        conn.execute('DELETE FROM users WHERE id = ?', (id,))
        conn.commit()
        
        # تسجيل النشاط
        log_activity(
            session['user_id'], 
            'delete', 
            'users', 
            id, 
            f'حذف المستخدم: {user["username"]}'
        )
        
        flash('تم حذف المستخدم بنجاح', 'success')
    except Exception as e:
        conn.rollback()
        flash(f'حدث خطأ أثناء حذف المستخدم: {e}', 'error')
    
    return redirect(url_for('users'))

# البحث المتقدم
@app.route('/search', methods=['GET', 'POST'])
@login_required
def search():
    if request.method == 'POST':
        search_term = request.form.get('search_term', '')
        department_id = request.form.get('department_id', '')
        
        try:
            conn = get_db()
            query = '''
                SELECT e.id, e.name, e.extension, e.job_title, d.name as department_name
                FROM employees e
                JOIN departments d ON e.department_id = d.id
                WHERE 1=1
            '''
            params = []
            
            if search_term:
                query += ' AND (e.name LIKE ? OR e.extension LIKE ? OR e.job_title LIKE ?)'
                params += [f'%{search_term}%', f'%{search_term}%', f'%{search_term}%']
            
            if department_id and department_id != 'all':
                query += ' AND e.department_id = ?'
                params.append(department_id)
            
            employees = conn.execute(query, params).fetchall()
            departments = conn.execute('SELECT * FROM departments ORDER BY name').fetchall()
            
            return render_template('index.html', employees=employees, departments=departments, search_term=search_term, selected_department=department_id)
        except Exception as e:
            flash(f'حدث خطأ أثناء البحث: {e}', 'error')
            return redirect(url_for('index'))
    
    return redirect(url_for('index'))

# استيراد البيانات
@app.route('/import_data', methods=['GET', 'POST'])
@login_required
@admin_required
def import_data():
    if request.method == 'POST':
        file = request.files['file']
        file_type = request.form.get('file_type', '')
        
        if not file or file.filename == '':
            flash('يرجى اختيار ملف', 'error')
            return redirect(url_for('import_data'))
        
        try:
            conn = get_db()
            
            if file_type == 'employees':
                # معالجة ملف الموظفين
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                reader = csv.DictReader(stream)
                
                for row in reader:
                    # التحقق من وجود الحقول الأساسية
                    if 'name' not in row or 'extension' not in row or 'department_id' not in row:
                        flash('الملف يحتوي على بيانات غير صحيحة', 'error')
                        return redirect(url_for('import_data'))
                    
                    name = row['name']
                    extension = row['extension']
                    department_id = row['department_id']
                    job_title = row.get('job_title', '')
                    email = row.get('email', '')
                    notes = row.get('notes', '')
                    
                    # التحقق من عدم تكرار رقم التحويلة
                    existing = conn.execute('SELECT id FROM employees WHERE extension = ?', (extension,)).fetchone()
                    if existing:
                        continue  # تجاهل هذا الصف إذا كان رقم التحويلة موجود بالفعل
                    
                    # إضافة الموظف
                    conn.execute(
                        '''INSERT INTO employees 
                           (name, extension, department_id, job_title, email, notes, created_by, updated_by) 
                           VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                        (name, extension, department_id, job_title, email, notes, session['user_id'], session['user_id'])
                    )
                
                conn.commit()
                flash('تم استيراد بيانات الموظفين بنجاح', 'success')
            elif file_type == 'departments':
                # معالجة ملف الإدارات
                stream = io.StringIO(file.stream.read().decode("UTF8"), newline=None)
                reader = csv.DictReader(stream)
                
                for row in reader:
                    # التحقق من وجود الحقول الأساسية
                    if 'name' not in row:
                        flash('الملف يحتوي على بيانات غير صحيحة', 'error')
                        return redirect(url_for('import_data'))
                    
                    name = row['name']
                    description = row.get('description', '')
                    
                    # التحقق من عدم تكرار اسم الإدارة
                    existing = conn.execute('SELECT id FROM departments WHERE name = ?', (name,)).fetchone()
                    if existing:
                        continue  # تجاهل هذا الصف إذا كان اسم الإدارة موجود بالفعل
                    
                    # إضافة الإدارة
                    conn.execute(
                        'INSERT INTO departments (name, description) VALUES (?, ?)',
                        (name, description)
                    )
                
                conn.commit()
                flash('تم استيراد بيانات الإدارات بنجاح', 'success')
            else:
                flash('نوع الملف غير مدعوم', 'error')
                return redirect(url_for('import_data'))
        except Exception as e:
            conn.rollback()
            flash(f'حدث خطأ أثناء استيراد البيانات: {e}', 'error')
            return redirect(url_for('import_data'))
    
    return render_template('import_data.html')

# التقارير
@app.route('/reports', methods=['GET'])
@login_required
@admin_required
def reports():
    return render_template('reports.html')

if __name__ == '__main__':
    app.run(debug=True)
# filepath: f:\Desktop\phone_system\app.py