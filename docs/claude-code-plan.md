# Plan สำหรับ Claude Code — Mini Online Shop (โจทย์ 4)

Flask + MySQL (local) · โฟลเดอร์งาน: `D:\Dataminishop`
เอกสารอ้างอิง: PDF โจทย์, `schema.sql` (ของผู้ใช้), `mini-shop-db-project-plan.md`

---

## 0. ข้อตกลงการทำงาน (อ่านก่อนเริ่ม)

- **Schema และ SQL ใน `db.py` เป็นงานออกแบบของผู้ใช้เอง** (เกณฑ์ให้คะแนนอยู่ที่ความเข้าใจ schema + SQL และมีถามรายบุคคล ตอบไม่ได้ = โดนหักคะแนน)
- บทบาทของ Claude Code: ทำงาน setup/เชื่อมต่อ, อธิบาย, ให้คำใบ้, รีวิว SQL, ทดสอบ — **ให้ผู้ใช้เขียนตรรกะ SQL เอง** เว้นแต่ผู้ใช้สั่งชัดเจนให้เขียนฟังก์ชันใดฟังก์ชันหนึ่ง
- ทุกครั้งที่ช่วยเขียน SQL ให้อธิบายทีละบรรทัดว่าทำงานอย่างไร ทำไมต้อง JOIN ตรงนี้
- ห้าม commit/push Git, ห้ามลบไฟล์ หรือแก้ไฟล์นอกขอบเขต เว้นแต่ผู้ใช้สั่ง
- ถ้าเจอปัญหาอื่นที่ไม่เกี่ยวกับงานที่ขอ ให้รายงานแต่ไม่ต้องแก้

## 1. บริบท

- Template อาจารย์: `https://github.com/prymania/DB69_projectTemplate` โฟลเดอร์ `4-shop_system` (frontend + API เสร็จแล้ว, `db.py` เป็น TODO)
- คู่มือตัวอย่าง (ระบบห้องสมุด): `https://prymania.github.io/dbprojectLibraryTutorialNewTemplate/index.html` ใช้เป็นแบบอย่างแพทเทิร์น CRUD/รายงาน
- ไฟล์ที่ต้องแก้มีแค่ `config.py`, `db.py` (+ `schema.sql` ของตัวเอง) ส่วน `app.py`, `templates/`, `static/` ปกติไม่แตะ ยกเว้นข้อ 4 ด้านล่าง
- DB: MySQL local, ใช้ DBeaver (ย้ายจาก DataGrip) ตอนนี้ **สร้างตาราง 6 ตาราง + sample data เสร็จแล้ว** (`order_line` = 19 แถว)
- วันที่อ้างอิง: 7 ต.ค. 2026 (ตรวจกับผู้ใช้ว่ากลุ่มจองรอบ 2 วันไหน) · รอบ 2 ส่งวันที่ 7 หรือ 14 ต.ค. (ต้องเชื่อม DB จริง, CRUD ≥ 2 ตาราง, JOIN ≥ 1 query) · รอบ 3 วันที่ 24 ต.ค.

## 2. Schema (ยืนยันแล้วว่าตรงกับโจทย์และ ER)

```
customer   (cust_id PK, name, email UNIQUE, address, tier)
product    (product_id PK, name, category, price, stock)
shop_order (order_id PK, cust_id FK, order_date, status)
order_line (order_id FK, product_id FK, qty, unit_price)  PK(order_id, product_id)  -- M:N #1
review     (cust_id FK, product_id FK, rating CHECK 1-5, comment, review_date)  PK(cust_id, product_id)  -- M:N #2
payment    (payment_id PK, order_id FK UNIQUE, method, amount, paid_date)  -- weak entity, 1:1
```

ค่าที่ schema ของผู้ใช้ใช้: `tier` = regular/silver/gold · `status` = pending/paid/shipped/completed/cancelled · `method` = cash/credit_card/transfer/promptpay
**ชื่อตาราง/คอลัมน์ต้องตรงกับ `db.py` เป๊ะ**

## 3. ขั้นตอน

### Step 1 — Clone และเตรียมสภาพแวดล้อม
1. `git clone https://github.com/prymania/DB69_projectTemplate.git` ลงใน `D:\Dataminishop` แล้วทำงานในโฟลเดอร์ `4-shop_system`
2. ถามผู้ใช้ก่อนว่าจะจัดโครงสร้างใหม่ (เช่น ย้าย `4-shop_system` ออกมา/สร้าง repo ของตัวเอง) หรือไม่ — **อย่าทำเองและอย่าลบ `.git` เดิม**
3. สร้าง virtual env และ `pip install -r requirements.txt` (Flask 3.0.3, mysql-connector-python 9.0.0) ตรวจเวอร์ชัน Python ที่ใช้งานได้จริงก่อน อย่าเดา

### Step 2 — ต่อฐานข้อมูล (`config.py`)
- `DB_HOST="localhost"`, `DB_PORT=3306`, `DB_USER`, `DB_PASSWORD`, `DB_NAME` ให้ **ถามผู้ใช้** (ชื่อ DB จริงที่ใช้ใน DBeaver; ผู้ใช้ยังไม่ได้ยืนยัน)
- ห้ามนำรหัสผ่านไปใส่ในแชทหรือ commit
- ทดสอบ: รัน `python -c "import db; print(db.run_query('SELECT COUNT(*) AS n FROM customer'))"` ควรได้ 8
- นำ `schema.sql` ของผู้ใช้ (ในโปรเจกต์) มาไว้แทนไฟล์ `schema.sql` ใน template เมื่อผู้ใช้อนุญาต (ไฟล์มี `DROP TABLE IF EXISTS` + sample data ครบ)

### Step 3 — ปรับ `ENTITIES` ใน `static/app.js` (แก้เฉพาะ options ใน array)
ค่าใน template (`normal/vip`, `pending/shipped`) เป็นแค่ตัวอย่าง ต้องเปลี่ยนให้ตรง schema ของผู้ใช้ ไม่งั้น (1) ค้นหา tier ไม่เจอข้อมูล (2) เปิดฟอร์มแก้ไขแล้ว dropdown ตกเป็นค่าแรกเงียบๆ ทำให้ข้อมูลเปลี่ยนโดยไม่รู้ตัว
- customers: `tier` ทั้ง `search` (มี `""` นำหน้า) และ `form` → regular, silver, gold
- orders: `status` ทั้ง `search` (มี `""`) และ `form` → pending, paid, shipped, completed, cancelled
- ไม่แก้ logic อื่นใน `app.js`

### Step 4 — เขียน `db.py` (ผู้ใช้เขียนเอง · Claude Code อธิบาย/รีวิว)
ลำดับ: customer → product → order → report
ทุก SQL ใช้ `%s` เท่านั้น **ห้ามต่อสตริง/f-string/.format()** กับค่าที่มาจาก user

**แพทเทิร์น (จากคู่มือห้องสมุด)**
- `search_*`: `WHERE 1=1` + ต่อ `AND` เฉพาะ filter ที่มีค่า · ข้อความอิสระ (name, email, category) ใช้ `LIKE %s` ครอบ `%` · ค่าจาก dropdown/ตัวเลข (tier, status, cust_id) ใช้ `= %s` · ปิดด้วย `ORDER BY`
- `get_*`: `rows[0] if rows else None`
- `create/update`: จำนวน `%s` = จำนวนค่าใน tuple และเรียงตรงกัน · `UPDATE/DELETE` ต้องมี `WHERE`
- เพิ่มฟังก์ชันช่วย `blank_to_none(v)` (template ร้านค้าไม่มี) ใช้กับ `email` (UNIQUE, ถ้าส่ง `""` ลูกค้าคนที่ 2 จะ error `Duplicate entry ''`) และช่องวันที่/ช่องว่างได้
- **วันที่:** `jsonify` ส่ง `date` เป็น `"Sat, 01 Aug 2026 00:00:00 GMT"` (ทดสอบแล้ว) ทำให้ `<input type="date">` ในฟอร์มแก้ไขแสดงค่าไม่ได้ → ใน `SELECT` ของ order ใช้ `DATE_FORMAT(order_date, '%Y-%m-%d') AS order_date` (ทั้ง `search_orders` และ `get_order`)
- `delete_*` ที่ติด FK จะขึ้น error 1451 ถือว่าปกติ (FK ทำงาน) ตอนเดโมให้เพิ่มรายการใหม่ก่อนแล้วลบตัวนั้น

**ฟังก์ชันและ key ที่หน้าเว็บส่งมา**

| กลุ่ม | ฟังก์ชัน | key |
|---|---|---|
| customer | `search_customers(filters)` | name, email (LIKE) · tier (=) |
| | `create/update_customer(data)` | name, email, address, tier |
| product | `search_products(filters)` | name, category (LIKE) |
| | `create/update_product(data)` | name, category, price, stock |
| order | `search_orders(filters)` | cust_id, status (=) |
| | `create/update_order(data)` | cust_id, order_date, status |
| ทุกกลุ่ม | `get_*(id)`, `delete_*(id)` | id ตาม PK |

ข้อเสนอเพิ่มคะแนน JOIN รอบ 2: ให้ `search_orders` JOIN `customer` เพื่อแสดงชื่อลูกค้า (ไม่บังคับ — เป็นการตัดสินใจของผู้ใช้)

**รายงาน (explicit `INNER JOIN ... ON` เสมอ ห้าม comma join)**
- `report_summary()` → dict ต้องมีคีย์ `customers, products, orders, reviews` (หน้ารายงานมีการ์ด "รีวิว" ด้วย; แผนเดิมเขียนแค่ 3 คีย์)
- `report_best_selling()` → `order_line ⋈ product`, `GROUP BY`, `SUM(qty)`, `ORDER BY ... DESC LIMIT 5`
- `report_customers_above_avg()` → `customer ⋈ shop_order ⋈ order_line` (3 ตาราง), `GROUP BY` ลูกค้า, `HAVING SUM(qty*unit_price) >` subquery ที่หา `AVG` ของยอดรวมต่อคน (ต้องหายอดรวมต่อคนก่อน แล้วค่อยเฉลี่ย ไม่ใช่เฉลี่ย `unit_price`)
- `report_high_rated()` → `review ⋈ product`, `GROUP BY`, `HAVING AVG(rating) >= 4`

**ตรวจผลด้วยมือจาก sample data** (ผู้ใช้ควรคำนวณเอง): สินค้า id=8 (Logitech G502) ขายดีสุด 15 ชิ้น · รีวิวเฉลี่ย ≥ 4 ควรได้ สินค้า 8, 10 (และ 7 ที่เท่ากับ 4.0 พอดี) · การ์ดจอ (id 1) ควรไม่ติด

### Step 5 — ทดสอบ
1. `python app.py` → `http://127.0.0.1:5000`
2. หน้า `/`: ค้นหา/เพิ่ม/แก้/ลบ ใช้งานได้ทั้ง customer, product, orders (ไม่ขึ้น 🚧 TODO)
3. หน้า `/report`: การ์ดตัวเลข 4 ใบ + ตาราง 3 ตารางขึ้นค่าถูกต้อง
4. Security: grep `db.py` หา `f"`, `.format(`, `" +` ที่ต่อ SQL — ต้องไม่มี
5. ทดสอบ edge: เพิ่มลูกค้าที่ไม่กรอกอีเมล 2 คนติดกัน, เปิดฟอร์มแก้ออเดอร์แล้ววันที่ต้องขึ้นถูก, แก้ลูกค้า gold แล้วบันทึก tier ต้องไม่เปลี่ยน

## 4. ผูกกับเกณฑ์ให้คะแนน (รอบ 2 = 30 คะแนน)

| เกณฑ์ | ทำได้เมื่อ |
|---|---|
| เชื่อม MySQL (5) | Step 2 ผ่าน + โครงสร้างตรง ER รอบ 1 |
| CRUD ≥ 2 ตาราง (10) | customer + product (หรือ order) ครบ 5 ฟังก์ชันใช้งานจริงบนเว็บ |
| JOIN ≥ 1 (5) | `report_best_selling` หรือ `search_orders` ที่ JOIN customer |
| ตาม feedback รอบ 1 (5) | **ผู้ใช้ยังไม่ได้บอกว่าอาจารย์ให้ feedback อะไร — ถามผู้ใช้** |
| ความเข้าใจ (5) | ผู้ใช้อธิบายทุกบรรทัดที่เขียนได้ |

## 5. ค้างรอ (ไม่ใช่ข้อผิดพลาด)

- self-reference: PDF ข้อ 1.5.3 ระบุให้ "ตามที่ระบุในแต่ละโจทย์" แต่โจทย์ 4 และ `schema.sql` ของ template ไม่มี → **ถามอาจารย์**
- ฟีเจอร์พิเศษของกลุ่ม: ยังไม่ทราบ ถ้าทราบแล้วต้องแก้ ER + schema + `db.py`
- ประเด็นที่ควรเตรียมตอบอาจารย์: ทำไม `payment` เป็น 1:1 (`UNIQUE order_id`), ทำไมเก็บ `payment.amount` ซ้ำกับผลรวม `order_line`, ทำไมเก็บ `unit_price` ใน `order_line` (ราคา ณ ตอนสั่ง), `tier/status/method` เป็น VARCHAR แทน ENUM, ไม่มี `CHECK` ที่ `qty/price/stock`
