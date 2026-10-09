# คู่มือเปิด-ปิดระบบ และเชื่อม DBeaver

## ภาพรวม

```
DBeaver ──┐
          ├──> MySQL (localhost:3306, DB: project69)
เว็บ ─────┘
```

- **MySQL** ต้องเปิดอยู่เสมอ (ทั้งเว็บและ DBeaver ใช้)
- **เว็บ** (port 5000) เปิดด้วย `python app.py`
- **DBeaver** เป็นแค่เครื่องมือดู/แก้ข้อมูล ปิดหรือเปิดไม่กระทบเว็บ

## เปิดเว็บ

```bash
cd D:\Dataminishop\shop_system
python app.py
```

เห็น `Running on http://127.0.0.1:5000` = เปิดแล้ว แล้วเปิดเบราว์เซอร์ไปที่ http://127.0.0.1:5000
(หน้ารายงาน: http://127.0.0.1:5000/report) กดปุ่ม "ค้นหา" เพื่อแสดงข้อมูล

**ห้ามปิดหน้าต่าง terminal** ที่รันอยู่ เพราะ server ทำงานอยู่ในนั้น

## ปิดเว็บ

กด `Ctrl + C` ใน terminal ที่รันอยู่ (หรือปิดหน้าต่าง terminal) ข้อมูลไม่หาย เพราะเก็บอยู่ใน MySQL

## เชื่อม DBeaver

**ตั้งค่าครั้งแรก**
1. Database → New Database Connection → MySQL
2. Server Host `localhost`, Port `3306`, Username `root`, ใส่ Password → Test Connection → Finish
3. สร้าง DB แล้วรันตาราง:
   ```sql
   CREATE DATABASE project69 CHARACTER SET utf8mb4;
   ```
   จากนั้นเปิด `database/sql/schema.sql` แล้วรันทั้งไฟล์ (`Alt+X`)

**ใช้งานทั่วไป**
- ดูข้อมูล: ขยาย `project69` → Tables → ดับเบิลคลิกตาราง → แท็บ Data
- ดู ER diagram: คลิกขวาที่ `project69` → View Diagram (หรือเปิด `database/diagram/er-diagram.png`)
- เช็คว่าเว็บกับ DBeaver เห็น DB ตัวเดียวกัน: เพิ่มข้อมูลในเว็บ แล้วกด `F5` ที่ตารางใน DBeaver ต้องเห็นแถวใหม่

## ตรวจว่าเว็บต่อ DB ถูกตัว

รันใน DBeaver:

```sql
SELECT @@hostname, @@port, DATABASE();
```

ได้ `localhost` / `3306` / `project69` = ตรงกับที่ตั้งใน `shop_system/config.py`

## ปัญหาที่พบบ่อย

| อาการ | วิธีแก้ |
|---|---|
| `No module named 'flask'` | `python -m pip install -r requirements.txt` (ใช้ Python ตัวเดียวกับที่รัน) |
| `Address already in use` | มี server เก่าเปิดค้างที่ port 5000 ปิดตัวเก่าก่อน |
| `Can't connect to MySQL server` | MySQL ยังไม่เปิด |
| `Access denied for user` | รหัสผ่านใน `config.py` ไม่ตรงกับ MySQL |
| `Unknown database 'project69'` | ยังไม่ได้สร้าง DB (ดูขั้นตอนเชื่อม DBeaver ข้อ 3) |
| แก้ `.js` / `.css` แล้วไม่เปลี่ยน | refresh เบราว์เซอร์ด้วย `Ctrl + F5` (แก้ `.py` ไม่ต้อง server โหลดใหม่เอง) |
| แก้ข้อมูลใน DBeaver แล้วเว็บไม่เห็น | กด Save / Commit ใน DBeaver |

ถ้าเปลี่ยนรหัสผ่าน MySQL ต้องแก้ทั้งใน DBeaver (Edit Connection) และ `shop_system/config.py`
