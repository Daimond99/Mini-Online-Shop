# ============================================================
#  config.py — ตั้งค่าการเชื่อมต่อ MySQL
#  ค่าจริง (รวมรหัสผ่าน) ให้ใส่ในไฟล์ config_local.py ซึ่งไม่ถูกอัปขึ้น GitHub
#  วิธีใช้: คัดลอก config_example.py เป็น config_local.py แล้วแก้ค่า
# ============================================================
DB_HOST = "localhost"
DB_USER = "root"
DB_PASSWORD = "CHANGE_ME"
DB_NAME = "project69"
DB_PORT = 3306

try:
    from config_local import *   # ถ้ามี config_local.py จะใช้ค่าในนั้นแทนค่าด้านบน
except ImportError:
    pass
