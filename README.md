# نظام دليل التحويلات الهاتفية

نظام متكامل لإدارة دليل التحويلات الهاتفية لشركة شبه الجزيرة للمقاولات.

## المميزات

- إدارة التحويلات الهاتفية (إضافة، تعديل، حذف)
- إدارة الإدارات والأقسام
- نظام صلاحيات متكامل (مدير النظام، مستخدم عادي)
- البحث المتقدم
- تصدير واستيراد البيانات بصيغ مختلفة (CSV, JSON)
- تقارير وإحصائيات

## متطلبات التشغيل

- Python 3.10 أو أحدث
- Flask
- bcrypt
- pandas

## طريقة التشغيل

1. تثبيت المتطلبات: `pip install -r requirements.txt`
2. تشغيل التطبيق: `python app.py`
3. فتح المتصفح على العنوان: `http://localhost:5000`

## بيانات الدخول الافتراضية

- اسم المستخدم: `admin`
- كلمة المرور: `admin123`
