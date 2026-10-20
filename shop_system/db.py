# db.py — คำสั่ง SQL ทั้งหมดของระบบ
#
# สารบัญ: 1.เชื่อมฐานข้อมูล  2.ลูกค้า  3.สินค้า  4.ออเดอร์  5.รายงาน  6.รายการรายงาน
#
# กติกาที่ใช้ทั้งไฟล์
# - ค่าจากผู้ใช้ส่งผ่าน %s เสมอ ไม่ต่อสตริงเอง (กัน SQL injection)
# - raise ValueError("ข้อความ") = ไม่บันทึก และแสดงข้อความนั้นบนหน้าเว็บ

import mysql.connector
import config


# ============================================================
# 1. เชื่อมฐานข้อมูล
# ============================================================

def get_connection():
    """เปิดการเชื่อมต่อ MySQL ตามค่าใน config.py"""
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT,
    )


def run_query(sql, params=()):
    """รัน SELECT แล้วคืนผลเป็น list ของ dict เช่น [{"name": "สมชาย"}, ...]"""
    with get_connection() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(sql, params)
            return cur.fetchall()


def run_command(sql, params=()):
    """รัน INSERT / UPDATE / DELETE แล้วบันทึก (commit)"""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            conn.commit()
            return {"new_id": cur.lastrowid, "affected": cur.rowcount}


def blank_to_none(value):
    """ช่องที่เว้นว่างไว้ -> None (บันทึกเป็น NULL)"""
    if value in ("", None):
        return None
    return value


# ============================================================
# 2. ลูกค้า (customer)
# ============================================================

def search_customers(filters):
    """ค้นหาลูกค้า กรองเฉพาะช่องที่ผู้ใช้กรอก"""
    sql = "SELECT * FROM customer WHERE 1=1"     # 1=1 ทำให้ต่อ AND ได้เสมอ
    params = []

    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append("%" + filters["name"] + "%")

    if filters.get("email"):
        sql += " AND email LIKE %s"
        params.append("%" + filters["email"] + "%")

    if filters.get("tier"):
        sql += " AND tier = %s"
        params.append(filters["tier"])

    sql += " ORDER BY cust_id"
    return run_query(sql, params)


def get_customer(cust_id):
    """ดึงลูกค้า 1 คน (ใช้เติมฟอร์มแก้ไข)"""
    rows = run_query("SELECT * FROM customer WHERE cust_id = %s", (cust_id,))
    if rows:
        return rows[0]
    return None


def check_email_not_used(email, cust_id=0):
    """อีเมลห้ามซ้ำกับลูกค้าคนอื่น (cust_id = คนที่กำลังแก้ ไม่นับตัวเอง)"""
    if not email:
        return
    sql = "SELECT 1 FROM customer WHERE email = %s AND cust_id <> %s"
    if run_query(sql, (email, cust_id)):
        raise ValueError(f"อีเมล {email} ถูกใช้แล้ว")


def create_customer(data):
    """เพิ่มลูกค้าใหม่"""
    email = blank_to_none(data.get("email"))
    address = blank_to_none(data.get("address"))
    check_email_not_used(email)

    sql = """INSERT INTO customer (name, email, address, tier)
             VALUES (%s, %s, %s, %s)"""
    return run_command(sql, (data["name"], email, address, data["tier"]))


def update_customer(cust_id, data):
    """แก้ไขข้อมูลลูกค้า"""
    email = blank_to_none(data.get("email"))
    address = blank_to_none(data.get("address"))
    check_email_not_used(email, cust_id)

    sql = """UPDATE customer
             SET name = %s, email = %s, address = %s, tier = %s
             WHERE cust_id = %s"""
    return run_command(sql, (data["name"], email, address, data["tier"], cust_id))


def delete_customer(cust_id):
    """ลบลูกค้า (ลบไม่ได้ถ้ามีออเดอร์หรือรีวิวอยู่)"""
    sql = """SELECT (SELECT COUNT(*) FROM shop_order WHERE cust_id = %s)
                  + (SELECT COUNT(*) FROM review     WHERE cust_id = %s) AS used"""
    if run_query(sql, (cust_id, cust_id))[0]["used"] > 0:
        raise ValueError("ลูกค้ารายนี้มีออเดอร์หรือรีวิวอยู่ ลบไม่ได้")

    return run_command("DELETE FROM customer WHERE cust_id = %s", (cust_id,))


# ============================================================
# 3. สินค้า (product)
# ============================================================

def search_products(filters):
    """ค้นหาสินค้าตามชื่อ / หมวดหมู่"""
    sql = "SELECT * FROM product WHERE 1=1"
    params = []

    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append("%" + filters["name"] + "%")

    if filters.get("category"):
        sql += " AND category LIKE %s"
        params.append("%" + filters["category"] + "%")

    sql += " ORDER BY product_id"
    return run_query(sql, params)


def get_product(product_id):
    """ดึงสินค้า 1 รายการ"""
    rows = run_query("SELECT * FROM product WHERE product_id = %s", (product_id,))
    if rows:
        return rows[0]
    return None


def check_product_name_not_used(name, product_id=0):
    """ชื่อสินค้าห้ามซ้ำ (product_id = ตัวที่กำลังแก้ ไม่นับตัวเอง)"""
    sql = "SELECT 1 FROM product WHERE name = %s AND product_id <> %s"
    if run_query(sql, (name, product_id)):
        raise ValueError(f"มีสินค้าชื่อ {name} อยู่แล้ว")


def check_price_and_stock(price, stock):
    """ราคาต้อง >= 0 และสต็อกต้องเป็นจำนวนเต็ม >= 0"""
    try:
        price = float(price)
        stock = float(stock)
    except (TypeError, ValueError):
        raise ValueError("ราคาและสต็อกต้องเป็นตัวเลข")

    if price < 0:
        raise ValueError("ราคาต้องเป็น 0 หรือมากกว่า")
    if stock < 0 or not stock.is_integer():
        raise ValueError("สต็อกต้องเป็นจำนวนเต็ม 0 หรือมากกว่า")


def create_product(data):
    """เพิ่มสินค้าใหม่"""
    name = data["name"].strip()
    category = blank_to_none(data.get("category"))
    check_product_name_not_used(name)
    check_price_and_stock(data["price"], data["stock"])

    sql = """INSERT INTO product (name, category, price, stock)
             VALUES (%s, %s, %s, %s)"""
    return run_command(sql, (name, category, data["price"], data["stock"]))


def update_product(product_id, data):
    """แก้ไขข้อมูลสินค้า"""
    name = data["name"].strip()
    category = blank_to_none(data.get("category"))
    check_product_name_not_used(name, product_id)
    check_price_and_stock(data["price"], data["stock"])

    sql = """UPDATE product
             SET name = %s, category = %s, price = %s, stock = %s
             WHERE product_id = %s"""
    return run_command(sql, (name, category, data["price"], data["stock"], product_id))


def delete_product(product_id):
    """ลบสินค้า (ลบไม่ได้ถ้าอยู่ในออเดอร์หรือมีรีวิว)"""
    sql = """SELECT (SELECT COUNT(*) FROM order_line WHERE product_id = %s)
                  + (SELECT COUNT(*) FROM review     WHERE product_id = %s) AS used"""
    if run_query(sql, (product_id, product_id))[0]["used"] > 0:
        raise ValueError("สินค้านี้มีในออเดอร์หรือรีวิวแล้ว ลบไม่ได้")

    return run_command("DELETE FROM product WHERE product_id = %s", (product_id,))


# ============================================================
# 4. ออเดอร์ (shop_order)
# ============================================================

ORDER_STATUSES = ("pending", "paid", "shipped", "completed", "cancelled")


def search_orders(filters):
    """ค้นหาออเดอร์ พร้อมชื่อลูกค้าและยอดรวม"""
    # INNER JOIN customer  = เอาชื่อลูกค้ามาแสดง
    # LEFT JOIN order_line = ออเดอร์ที่ยังไม่มีสินค้าก็ยังแสดง (ยอดรวม = 0)
    sql = """SELECT o.order_id,
                    o.cust_id,
                    c.name AS customer_name,
                    CAST(o.order_date AS CHAR) AS order_date,
                    o.status,
                    IFNULL(t.total, 0) AS total
             FROM shop_order o
             INNER JOIN customer c ON o.cust_id = c.cust_id
             LEFT JOIN (SELECT order_id, SUM(qty * unit_price) AS total
                        FROM order_line
                        GROUP BY order_id) t ON o.order_id = t.order_id
             WHERE 1=1"""
    params = []

    if filters.get("cust_id"):
        sql += " AND o.cust_id = %s"
        params.append(filters["cust_id"])

    if filters.get("status"):
        sql += " AND o.status = %s"
        params.append(filters["status"])

    sql += " ORDER BY o.order_id"
    return run_query(sql, params)


def get_order(order_id):
    """ดึงออเดอร์ 1 รายการ"""
    sql = """SELECT order_id, cust_id, CAST(order_date AS CHAR) AS order_date, status
             FROM shop_order
             WHERE order_id = %s"""
    rows = run_query(sql, (order_id,))
    if rows:
        return rows[0]
    return None


def check_status(status):
    """สถานะต้องเป็นหนึ่งใน ORDER_STATUSES"""
    if status not in ORDER_STATUSES:
        raise ValueError(f"สถานะ {status} ไม่ถูกต้อง")


def is_paid(order_id):
    """ออเดอร์นี้จ่ายเงินแล้วหรือยัง (จ่ายแล้ว = มีแถวในตาราง payment)"""
    sql = "SELECT 1 FROM payment WHERE order_id = %s"
    return len(run_query(sql, (order_id,))) > 0


def create_order(data):
    """เพิ่มออเดอร์ใหม่ (ห้ามตั้งเป็น shipped เพราะยังไม่ได้จ่ายเงิน)"""
    check_status(data["status"])
    if data["status"] == "shipped":
        raise ValueError("ออเดอร์ใหม่ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")

    sql = """INSERT INTO shop_order (cust_id, order_date, status)
             VALUES (%s, %s, %s)"""
    return run_command(sql, (data["cust_id"], data["order_date"], data["status"]))


def update_order(order_id, data):
    """แก้ไขออเดอร์ (จะเปลี่ยนเป็น shipped ได้ต้องจ่ายเงินแล้ว)"""
    check_status(data["status"])
    if data["status"] == "shipped" and not is_paid(order_id):
        raise ValueError("ออเดอร์นี้ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")

    sql = """UPDATE shop_order
             SET cust_id = %s, order_date = %s, status = %s
             WHERE order_id = %s"""
    return run_command(sql, (data["cust_id"], data["order_date"], data["status"], order_id))


def delete_order(order_id):
    """ลบออเดอร์พร้อมรายการสินค้า (ลบไม่ได้ถ้าจ่ายเงินแล้ว)"""
    if is_paid(order_id):
        raise ValueError("ออเดอร์นี้ชำระเงินแล้ว ลบไม่ได้")

    # ลบตารางลูก (order_line) ก่อนตารางแม่ (shop_order) ไม่งั้นติด FOREIGN KEY
    run_command("DELETE FROM order_line WHERE order_id = %s", (order_id,))
    return run_command("DELETE FROM shop_order WHERE order_id = %s", (order_id,))


# ============================================================
# 5. รายงาน (ชื่อหลัง AS = หัวตารางบนหน้าเว็บ)
# ============================================================

def report_summary():
    """การ์ดตัวเลขสรุปด้านบน (1 คอลัมน์ = 1 การ์ด)"""
    sql = """SELECT
               (SELECT COUNT(*) FROM customer)   AS 'ลูกค้า',
               (SELECT COUNT(*) FROM product)    AS 'สินค้า',
               (SELECT COUNT(*) FROM shop_order) AS 'ออเดอร์',
               (SELECT COUNT(*) FROM review)     AS 'รีวิว',
               (SELECT IFNULL(SUM(amount), 0) FROM payment) AS 'รายได้รวม (บาท)',
               (SELECT COUNT(*) FROM shop_order WHERE status = 'pending') AS 'ออเดอร์รอดำเนินการ'"""
    return run_query(sql)[0]


def report_best_selling():
    """รายงานที่ 1: สินค้าขายดี 5 อันดับ — JOIN 3 ตาราง + GROUP BY + SUM"""
    sql = """SELECT p.name     AS 'สินค้า',
                    p.category AS 'หมวดหมู่',
                    SUM(ol.qty) AS 'จำนวนที่ขายได้'
             FROM order_line ol
             INNER JOIN product p    ON ol.product_id = p.product_id
             INNER JOIN shop_order o ON ol.order_id = o.order_id
             WHERE o.status <> 'cancelled'
             GROUP BY p.product_id, p.name, p.category
             ORDER BY SUM(ol.qty) DESC, p.name
             LIMIT 5"""
    return run_query(sql)


def report_customers_above_avg():
    """รายงานที่ 2: ลูกค้าที่ยอดซื้อมากกว่าค่าเฉลี่ย — JOIN 3 ตาราง + HAVING + subquery AVG"""
    # subquery ด้านใน: หายอดรวมของลูกค้าแต่ละคน แล้วเอามาเฉลี่ย
    sql = """SELECT c.name AS 'ลูกค้า',
                    c.tier AS 'ระดับ',
                    SUM(ol.qty * ol.unit_price) AS 'ยอดซื้อรวม'
             FROM customer c
             INNER JOIN shop_order o  ON c.cust_id = o.cust_id
             INNER JOIN order_line ol ON o.order_id = ol.order_id
             WHERE o.status <> 'cancelled'
             GROUP BY c.cust_id, c.name, c.tier
             HAVING SUM(ol.qty * ol.unit_price) > (
                 SELECT AVG(per_cust.total)
                 FROM (SELECT SUM(ol2.qty * ol2.unit_price) AS total
                       FROM shop_order o2
                       INNER JOIN order_line ol2 ON o2.order_id = ol2.order_id
                       WHERE o2.status <> 'cancelled'
                       GROUP BY o2.cust_id) per_cust
             )
             ORDER BY SUM(ol.qty * ol.unit_price) DESC"""
    return run_query(sql)


def report_high_rated():
    """รายงานที่ 3: สินค้าคะแนนรีวิวเฉลี่ย >= 4 — JOIN 3 ตาราง + GROUP BY + AVG + HAVING"""
    sql = """SELECT p.name AS 'สินค้า',
                    ROUND(AVG(r.rating), 2) AS 'คะแนนเฉลี่ย',
                    COUNT(DISTINCT c.cust_id) AS 'จำนวนผู้รีวิว'
             FROM review r
             INNER JOIN product p  ON r.product_id = p.product_id
             INNER JOIN customer c ON r.cust_id = c.cust_id
             GROUP BY p.product_id, p.name
             HAVING AVG(r.rating) >= 4
             ORDER BY AVG(r.rating) DESC"""
    return run_query(sql)


# ============================================================
# 6. รายการรายงานบนหน้า /report (ต้องอยู่ท้ายไฟล์)
#    (key ใน URL, ชื่อที่แสดง, ฟังก์ชันที่รัน)
# ============================================================

REPORTS = [
    ("best-selling",  "สินค้าขายดี 5 อันดับ",              report_best_selling),
    ("top-customers", "ลูกค้าที่ยอดซื้อมากกว่าค่าเฉลี่ย",     report_customers_above_avg),
    ("high-rated",    "สินค้าที่คะแนนรีวิวเฉลี่ย 4 ขึ้นไป",     report_high_rated),
]
