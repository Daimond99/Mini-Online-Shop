# Mini Online Shop — Term Project (โจทย์ 4)

เว็บร้านค้าออนไลน์ (อุปกรณ์คอมพิวเตอร์) · Flask + MySQL (local)

## โครงสร้างโฟลเดอร์

```
Dataminishop/
├── shop_system/              ← ตัวเว็บทั้งหมด
│   ├── app.py                  หลังบ้าน: กำหนด URL (/api/...) แล้วเรียก db.py
│   ├── db.py                   หลังบ้าน: SQL ทั้งหมด (CRUD + รายงาน + กฎตรวจก่อนบันทึก)
│   ├── config.py               ตั้งค่าเชื่อม MySQL (ค่าตัวอย่าง) · ค่าจริงอยู่ใน config_local.py (ไม่อัปขึ้น git)
│   ├── config_example.py       ต้นแบบของ config_local.py
│   ├── requirements.txt        ไลบรารี (Flask, mysql-connector-python)
│   ├── templates/              หน้าบ้าน: index.html (CRUD), report.html (รายงาน)
│   └── static/                 หน้าบ้าน: app.js, report.js, style.css
├── database/
│   ├── schema.sql              สร้างตาราง + sample data (รันใน DBeaver)
│   └── er-diagram.png         ER diagram
├── docs/                     เอกสารประกอบ (แผนงาน, เกณฑ์คะแนน)
```

โฟลเดอร์ `General/` และ `.metadata/` เป็นของ DBeaver (workspace) ห้ามลบ

## การทำงาน (ใช้อธิบายตอน present)

```
เบราว์เซอร์ (templates + static/app.js)
      │  fetch /api/customers, /api/orders, /api/reports/...
      ▼
app.py  ── route รับคำขอ ──►  db.py  ── SQL (%s) ──►  MySQL :3306  (DB: project69)
                                                          ▲
                                                       DBeaver (เปิดดู/แก้ DB ตัวเดียวกัน)
```

- เว็บเปิดที่ port **5000** (Flask) · MySQL อยู่ที่ port **3306**
- `app.py` ไม่มี SQL · SQL ทั้งหมดอยู่ใน `db.py`
- ทุก query ใช้ `%s` (parameter) กัน SQL injection

## ฐานข้อมูล (6 ตาราง)

```
customer 1──M shop_order 1──M order_line M──1 product
customer 1──M review     M──1 product              (review = M:N customer × product)
shop_order 1──1 payment                            (order_line = M:N order × product)
```

## สิ่งที่ `db.py` ทำ

| กลุ่ม | ฟังก์ชัน |
|---|---|
| customer / product | `search_`, `get_`, `create_`, `update_`, `delete_` |
| order | เหมือนข้างบน + `search_orders` JOIN customer และคำนวณ `total` จาก `order_line` |
| กฎธุรกิจ | `check_can_ship` — จัดส่งได้เฉพาะออเดอร์ที่จ่ายแล้ว · ห้ามลบออเดอร์ที่จ่ายแล้ว |
| รายงาน | สินค้าขายดี (JOIN+GROUP BY) · ลูกค้ายอดเกินค่าเฉลี่ย (subquery+AVG) · รีวิว ≥ 4 (HAVING) |

## วิธีติดตั้งและรัน (สำหรับคนที่ clone ไป)

**สิ่งที่ต้องมี:** Python 3.10+, MySQL 8 (เปิดอยู่ที่ port 3306), โปรแกรมจัดการ DB เช่น DBeaver (หรือใช้ `mysql` command line)

**1. Clone โปรเจกต์**

```bash
git clone https://github.com/Daimond99/Mini-Online-Shop.git
cd Mini-Online-Shop
```

**2. สร้างฐานข้อมูลและตาราง**

เปิด DBeaver (หรือ MySQL client) ต่อ MySQL ของเครื่อง แล้วรันตามลำดับ:

```sql
CREATE DATABASE project69 CHARACTER SET utf8mb4;
USE project69;
```

จากนั้นเปิดไฟล์ `database/schema.sql` แล้ว **รันทั้งไฟล์** (DBeaver: Execute Script / Alt+X) ไฟล์นี้จะลบตารางเก่าที่ชื่อซ้ำ สร้างตารางทั้ง 6 ตาราง และใส่ข้อมูลตัวอย่าง

ตรวจว่าสำเร็จ: `SELECT COUNT(*) FROM customer;` ต้องได้ 8

**3. ตั้งค่าการเชื่อมต่อ**

```bash
cd shop_system
copy config_example.py config_local.py      # Windows  (macOS/Linux: cp config_example.py config_local.py)
```

เปิด `config_local.py` แล้วแก้ `DB_USER`, `DB_PASSWORD` (และ `DB_NAME`, `DB_HOST`, `DB_PORT` ถ้าต่างจากค่าตัวอย่าง) ให้ตรงกับ MySQL ของเครื่องตัวเอง ไฟล์นี้ไม่ถูกอัปขึ้น GitHub

**4. ติดตั้งไลบรารีและรัน**

```bash
pip install -r requirements.txt
python app.py
```

**5. เปิดเว็บ**

- http://127.0.0.1:5000 — จัดการข้อมูล (แท็บ ลูกค้า / สินค้า / ออเดอร์: ค้นหา เพิ่ม แก้ไข ลบ)
- http://127.0.0.1:5000/report — รายงานและการ์ดสรุป

## ลองใช้งานดู (ตัวอย่างสิ่งที่ควรเห็น)

| ทำอะไร | ผลที่ควรได้ |
|---|---|
| หน้า `/report` | สินค้าขายดีอันดับ 1 = Logitech G502 HERO (15 ชิ้น), ลูกค้ายอดเกินค่าเฉลี่ย 4 คน, สินค้ารีวิวเฉลี่ย ≥ 4 มี 3 รายการ |
| แท็บ ออเดอร์ → แก้ออเดอร์ #9 (ยังไม่จ่าย) เป็น `shipped` | ขึ้นข้อความ "ออเดอร์นี้ยังไม่ได้ชำระเงิน จัดส่งไม่ได้" |
| ลบออเดอร์ #1 (จ่ายแล้ว) | ขึ้นข้อความ "ออเดอร์นี้ชำระเงินแล้ว ลบไม่ได้" |
| ลบลูกค้า #1 (มีออเดอร์) | ขึ้นข้อความ "ลูกค้ารายนี้มีออเดอร์หรือรีวิวอยู่ ลบไม่ได้" |
| เพิ่มลูกค้า 2 คนโดยไม่กรอกอีเมล | บันทึกได้ทั้งคู่ (อีเมลที่ว่างเก็บเป็น NULL) |

## แก้ปัญหาที่พบบ่อย

| อาการ | สาเหตุ / วิธีแก้ |
|---|---|
| `Access denied for user` | `DB_USER` / `DB_PASSWORD` ใน `config_local.py` ไม่ตรงกับ MySQL ของเครื่อง |
| `Unknown database 'project69'` | ยังไม่ได้รัน `CREATE DATABASE project69` (ขั้นที่ 2) หรือตั้ง `DB_NAME` ไม่ตรง |
| `Can't connect to MySQL server` | MySQL ยังไม่เปิด หรือ port ไม่ใช่ 3306 |
| `Table ... doesn't exist` | ยังไม่ได้รัน `database/schema.sql` |
| `No module named 'flask'` | ยังไม่ได้ `pip install -r requirements.txt` หรือติดตั้งลง Python คนละตัวกับที่ใช้รัน (ลอง `python -m pip install -r requirements.txt`) |
| ภาษาไทยเป็น `???` | สร้าง DB โดยไม่ใส่ `CHARACTER SET utf8mb4` |
| ค้นหาแล้วไม่ขึ้นข้อมูล | กดปุ่ม "🔍 ค้นหา" ก่อน (หน้าเว็บไม่โหลดข้อมูลอัตโนมัติ) |
