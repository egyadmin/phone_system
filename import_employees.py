import json
import sqlite3
import os

# قاعدة البيانات
DB_PATH = 'phone_directory.db'

def import_directory_data(json_file_path):
    print(f"بدء استيراد البيانات من: {json_file_path}")
    
    # التأكد من وجود قاعدة البيانات
    if not os.path.exists(DB_PATH):
        print("خطأ: قاعدة البيانات غير موجودة. يرجى تشغيل التطبيق أولاً لإنشاء قاعدة البيانات.")
        return
    
    try:
        # قراءة ملف JSON
        print("قراءة ملف البيانات...")
        with open(json_file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        # الاتصال بقاعدة البيانات
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # استخراج الإدارات الفريدة
        print("استخراج الإدارات الفريدة...")
        departments = set()
        for entry in data:
            dept = entry.get('department', '').strip()
            if dept:
                departments.add(dept)
        
        # إضافة الإدارات إلى قاعدة البيانات
        department_mapping = {}  # لتخزين معرف الإدارة
        print(f"إضافة {len(departments)} إدارة إلى قاعدة البيانات...")
        
        for dept in departments:
            # التحقق من وجود الإدارة
            cursor.execute("SELECT id FROM departments WHERE name = ?", (dept,))
            result = cursor.fetchone()
            
            if result:
                # الإدارة موجودة بالفعل
                department_id = result[0]
            else:
                # إضافة إدارة جديدة
                cursor.execute("INSERT INTO departments (name) VALUES (?)", (dept,))
                department_id = cursor.lastrowid
            
            department_mapping[dept] = department_id
        
        # إضافة الموظفين
        print("إضافة الموظفين...")
        success_count = 0
        error_count = 0
        
        for entry in data:
            try:
                name = entry.get('name', '').strip()
                extension = entry.get('extension', '').strip()
                department_name = entry.get('department', '').strip()
                
                if not name or not extension or not department_name:
                    error_count += 1
                    print(f"خطأ: بيانات غير مكتملة: {entry}")
                    continue
                
                department_id = department_mapping.get(department_name)
                if not department_id:
                    error_count += 1
                    print(f"خطأ: لم يتم العثور على الإدارة: {department_name}")
                    continue
                
                # التحقق من عدم تكرار رقم التحويلة
                cursor.execute("SELECT id FROM employees WHERE extension = ?", (extension,))
                if cursor.fetchone():
                    error_count += 1
                    print(f"خطأ: رقم التحويلة مكرر: {extension} للموظف: {name}")
                    continue
                
                # استخراج المسمى الوظيفي من الاسم إذا وجد
                job_title = ""
                if " - " in name:
                    parts = name.split(" - ", 1)
                    name = parts[0].strip()
                    job_title = parts[1].strip()
                
                # إضافة الموظف
                cursor.execute(
                    """
                    INSERT INTO employees 
                    (name, extension, department_id, job_title, created_by, updated_by) 
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (name, extension, department_id, job_title, 1, 1)  # نفترض أن معرف المستخدم هو 1 (المسؤول)
                )
                
                success_count += 1
                
            except Exception as e:
                error_count += 1
                print(f"خطأ أثناء إضافة الموظف: {e}, البيانات: {entry}")
        
        # حفظ التغييرات
        conn.commit()
        
        print(f"\nتم الانتهاء من الاستيراد:")
        print(f"تم إضافة {len(department_mapping)} إدارة بنجاح")
        print(f"تم إضافة {success_count} موظف بنجاح")
        print(f"فشل إضافة {error_count} موظف")
        
        conn.close()
        
    except Exception as e:
        print(f"حدث خطأ أثناء استيراد البيانات: {e}")

# تحديد مسار ملف البيانات
json_file_path = 'directory_data.json'

# إنشاء ملف JSON من البيانات المقدمة
def create_json_file(json_content, file_path):
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(json_content)
    print(f"تم إنشاء ملف JSON في: {file_path}")

# البيانات ستستخدم من ملف خارجي، لا حاجة لتعريفها هنا

if __name__ == "__main__":
    # حدد مسار الملف الذي سيتم إنشاؤه أو استخدامه
    json_file_path = 'directory_data.json'
    
    # تأكد من وجود قاعدة البيانات
    if not os.path.exists(DB_PATH):
        print("خطأ: قاعدة البيانات غير موجودة. يرجى تشغيل التطبيق أولاً لإنشاء قاعدة البيانات.")
    else:
        # استيراد البيانات إلى قاعدة البيانات
        import_directory_data(json_file_path)