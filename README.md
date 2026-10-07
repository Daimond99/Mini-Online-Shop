# Mini Online Shop

เว็บร้านค้าออนไลน์ขนาดเล็ก (Flask + MySQL) — Term Project วิชาฐานข้อมูล โจทย์ที่ 4

**ทำอะไรได้**
- จัดการลูกค้า สินค้า และออเดอร์ (ค้นหา เพิ่ม แก้ไข ลบ)
- จัดส่งได้เฉพาะออเดอร์ที่จ่ายเงินแล้ว
- หน้ารายงาน: สินค้าขายดี, ลูกค้าที่ซื้อเกินค่าเฉลี่ย, สินค้าคะแนนรีวิว ≥ 4

## โครงสร้างโปรเจกต์

```
shop_system/    เว็บ: app.py (URL), db.py (SQL ทั้งหมด), config.py, templates/, static/
database/       schema.sql (ตาราง + ข้อมูลตัวอย่าง), er-diagram.png
docs/           เอกสารประกอบ
```

## วิธีติดตั้ง

ต้องมี Python 3.10+ และ MySQL 8

**1. Clone**

```bash
git clone https://github.com/Daimond99/Mini-Online-Shop.git
cd Mini-Online-Shop
```

**2. สร้างฐานข้อมูล** — รันใน DBeaver หรือ MySQL client

```sql
CREATE DATABASE project69 CHARACTER SET utf8mb4;
USE project69;
```

แล้วรันไฟล์ `database/schema.sql` ทั้งไฟล์ (สร้างตารางและใส่ข้อมูลตัวอย่าง)

**3. ตั้งค่าการเชื่อมต่อ**

```bash
cd shop_system
copy config_example.py config_local.py
```

(macOS/Linux ใช้ `cp` แทน `copy`) แล้วเปิด `config_local.py` แก้ `DB_USER` และ `DB_PASSWORD` ให้ตรงกับ MySQL ของเครื่อง

**4. รัน**

```bash
pip install -r requirements.txt
python app.py
```

เปิด http://127.0.0.1:5000 (หน้ารายงานอยู่ที่ `/report`) กดปุ่ม "ค้นหา" เพื่อแสดงข้อมูล
