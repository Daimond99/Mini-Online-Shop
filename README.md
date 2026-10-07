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

## วิธีรัน

1. เปิด MySQL แล้วรัน `database/schema.sql` ใน DBeaver (สร้างตาราง + ข้อมูล)
2. คัดลอก `shop_system/config_example.py` เป็น `shop_system/config_local.py` แล้วใส่ user/password ของ MySQL ตัวเอง
   (`config_local.py` ไม่ถูกอัปขึ้น GitHub เพื่อไม่ให้รหัสผ่านหลุด)
3. ติดตั้งและรัน:

```bash
cd shop_system
pip install -r requirements.txt
python app.py
```

4. เปิด http://127.0.0.1:5000 (หน้ารายงานที่ `/report`)

## ความคืบหน้า (อัปเดต 7 ต.ค. 2026)

### สำเร็จแล้ว
- [x] ER diagram + `database/schema.sql` (6 ตาราง, PK/FK/CHECK/UNIQUE, sample data ทุกตาราง ≥ 8 แถว, มีออเดอร์ที่ยกเลิก 1 ใบไว้ทดสอบรายงาน)
- [x] เชื่อม MySQL local ได้ (ตรวจแล้วว่า DBeaver กับเว็บใช้ DB `project69` ตัวเดียวกัน)
- [x] CRUD ครบ 3 ตารางหลัก: customer, product, shop_order (ค้นหา/ดู/เพิ่ม/แก้/ลบ)
- [x] กฎธุรกิจ: จัดส่งได้เฉพาะออเดอร์ที่จ่ายแล้ว · ห้ามลบออเดอร์ที่จ่ายแล้ว · ลบลูกค้า/สินค้าที่มีออเดอร์หรือรีวิวไม่ได้ · อีเมลซ้ำแจ้งเตือน
- [x] รายงานบังคับ 3 ตัว (ทุกตัว JOIN ≥ 3 ตาราง) + การ์ดสรุป 6 ใบ
- [x] ป้องกัน SQL injection (ใช้ `%s` ทุก query) และทดสอบแล้ว
- [x] ทดสอบระบบแบบผู้ใช้ ~30 กรณี ผ่านทั้งหมด
- [x] ตรวจเทียบกับ PDF โจทย์ทุกข้อในขอบเขต

### ยังเหลือ
- [ ] **ฟีเจอร์พิเศษเฉพาะกลุ่ม** (หน้า 9 ของโจทย์) — ยังไม่ทราบว่ากลุ่มได้อะไร ต้องเช็คในไฟล์คะแนนของอาจารย์
- [ ] ปรับตาม feedback รอบ 1 — ยังไม่ทราบ feedback
- [ ] ยืนยันกับอาจารย์ว่าโจทย์ 4 ไม่ต้องมี self-reference
- [ ] ทำความเข้าใจระบบให้ตอบรายบุคคลได้ (SQL ทุกฟังก์ชัน, ทำไม JOIN/FK ตรงนั้น, `WHERE` vs `HAVING`, ทำไมเก็บ `unit_price`, ทำไม `payment` เป็น 1:1)
- [ ] ปรับปรุงเพิ่มเติม (optimize) ถ้ามีเวลา เช่น index, transaction
