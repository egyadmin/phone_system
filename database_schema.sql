-- قاعدة بيانات نظام دليل التحويلات الهاتفية

-- إنشاء جدول المستخدمين
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

-- إنشاء جدول الإدارات
CREATE TABLE IF NOT EXISTS departments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- إنشاء جدول الموظفين
CREATE TABLE IF NOT EXISTS employees (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    extension TEXT UNIQUE NOT NULL,
    department_id INTEGER NOT NULL,
    job_title TEXT,
    email TEXT,
    notes TEXT,
    created_by INTEGER NOT NULL,
    updated_by INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (department_id) REFERENCES departments (id),
    FOREIGN KEY (created_by) REFERENCES users (id),
    FOREIGN KEY (updated_by) REFERENCES users (id)
);

-- إنشاء جدول سجل النشاطات
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

-- إنشاء مستخدم افتراضي للنظام (admin/admin)
INSERT INTO users (username, password, full_name, role) VALUES 
('admin', '$2b$12$1234567890123456789012uQGbTmwzZRBWzOZ3pPUPwbPQRTSnq4S', 'مدير النظام', 'admin');

-- إنشاء الإدارات الأساسية
INSERT INTO departments (name, description) VALUES 
('الإدارة المالية بفرع الرياض', 'الإدارة المالية بفرع الرياض'),
('إدارة الموارد البشرية', 'إدارة الموارد البشرية والشؤون الإدارية'),
('إدارة تقنية المعلومات', 'إدارة تقنية المعلومات والدعم الفني'),
('الإدارة التنفيذية', 'الإدارة التنفيذية العليا');

-- إدخال بيانات الموظفين المستخرجة
INSERT INTO employees (name, extension, department_id, job_title) VALUES 
('أ / جميعه العتيبي', '273', 1, ''),
('أ / خالد عبدالمجيد اسماعيل', '301', 1, ''),
('أ / راضي باصهيول', '232', 1, ''),
('أ / عبد القادر محمد إبراهيم', '226', 1, 'مدير إدارة الحسابات'),
('أ / شمس سراج', '228', 1, 'مدخل بيانات'),
('أ / سلطان الحارثي (أبو متعب)', '266', 1, 'مدير شؤون الموظفين'),
('أ / مبارك العتيبي', '143', 1, ''),
('أ / علي رمضان', '227', 1, 'أمين الصندوق'),
('أ / علي أحمد وداعه', '863', 1, 'فرع الرياض (التنفيذية)'),
('أ / محمد الدوسري', '280', 1, ''),
('أ / محمد الدعجاني', '283', 1, 'الصادر والوارد'),
('أ / محمد الحسينان', '263', 1, ''),
('أ / محمد بياسر', '234', 1, ''),
('أ / محمد عبدالعال حسني', '285', 1, ''),
('أ / محمد العتيبي', '852', 1, ''),
('أ / أسماء المطيري', '276', 1, ''),
('أ / عبدالوكيل', '275', 1, ''),
('أ / أحلام الشهري', '329', 1, ''),
('أ / إيمان الشهراني', '281', 1, ''),
('أ / أشرف علي', '231', 1, ''),
('أ / أحمد عبدالفتاح', '845', 1, 'محاسب الإنتاج'),
('أ / تهاني العتيبي', '218', 1, ''),
('أ / تهاني العتيبي', '350', 1, ''),
('أ / بدور الحارثي', '230', 1, '');

-- إنشاء فهارس لتحسين الأداء
CREATE INDEX idx_employees_department ON employees(department_id);
CREATE INDEX idx_employees_extension ON employees(extension);
CREATE INDEX idx_activity_log_user ON activity_log(user_id);
CREATE INDEX idx_activity_log_action ON activity_log(action_type);
