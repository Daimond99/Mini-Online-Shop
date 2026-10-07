# ============================================================
#  db.py — ชั้นติดต่อฐานข้อมูล
#  ใช้ %s เป็น placeholder เสมอ (กัน SQL injection)
# ============================================================
import mysql.connector
import config


def get_connection():
    return mysql.connector.connect(
        host=config.DB_HOST, user=config.DB_USER, password=config.DB_PASSWORD,
        database=config.DB_NAME, port=config.DB_PORT)


def run_query(sql, params=None):
    """รัน SELECT คืนผลเป็น list ของ dict"""
    conn = get_connection(); cur = conn.cursor(dictionary=True)
    cur.execute(sql, params or ()); rows = cur.fetchall()
    cur.close(); conn.close(); return rows


def run_command(sql, params=None):
    """รัน INSERT / UPDATE / DELETE แล้ว commit"""
    conn = get_connection(); cur = conn.cursor()
    cur.execute(sql, params or ()); conn.commit()
    out = {"new_id": cur.lastrowid, "affected": cur.rowcount}
    cur.close(); conn.close(); return out


def blank_to_none(value):
    """ช่องที่ไม่ได้กรอกในฟอร์มจะส่งมาเป็น "" — แปลงเป็น None (= NULL ใน SQL)
    ใช้กับคอลัมน์ที่ว่างได้ เช่น email (UNIQUE) เพราะ '' ซ้ำกันไม่ได้"""
    return None if value in ("", None) else value


# ---------- ลูกค้า (customer) ----------
def search_customers(filters):
    sql = "SELECT * FROM customer WHERE 1=1"
    params = []
    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append(f"%{filters['name']}%")
    if filters.get("email"):
        sql += " AND email LIKE %s"
        params.append(f"%{filters['email']}%")
    if filters.get("tier"):
        sql += " AND tier = %s"
        params.append(filters["tier"])
    sql += " ORDER BY cust_id"
    return run_query(sql, params)


def get_customer(cust_id):
    rows = run_query("SELECT * FROM customer WHERE cust_id = %s", (cust_id,))
    return rows[0] if rows else None


def _check_email_unique(email, cust_id=0):
    """email เป็น UNIQUE — แจ้งข้อความอ่านง่ายแทน error ดิบของ MySQL (cust_id = คนที่กำลังแก้ ไม่นับตัวเอง)"""
    if email and run_query("SELECT 1 FROM customer WHERE email = %s AND cust_id <> %s", (email, cust_id)):
        raise ValueError(f"อีเมล {email} ถูกใช้แล้ว")


def create_customer(data):
    email = blank_to_none(data.get("email"))
    _check_email_unique(email)
    sql = """INSERT INTO customer (name, email, address, tier)
             VALUES (%s, %s, %s, %s)"""
    return run_command(sql, (data["name"], email, blank_to_none(data.get("address")), data["tier"]))


def update_customer(cust_id, data):
    email = blank_to_none(data.get("email"))
    _check_email_unique(email, cust_id)
    sql = """UPDATE customer SET name = %s, email = %s, address = %s, tier = %s
             WHERE cust_id = %s"""
    return run_command(sql, (data["name"], email, blank_to_none(data.get("address")),
                             data["tier"], cust_id))


def delete_customer(cust_id):
    sql = """SELECT (SELECT COUNT(*) FROM shop_order WHERE cust_id = %s)
                  + (SELECT COUNT(*) FROM review WHERE cust_id = %s) AS n"""
    if run_query(sql, (cust_id, cust_id))[0]["n"]:
        raise ValueError("ลูกค้ารายนี้มีออเดอร์หรือรีวิวอยู่ ลบไม่ได้")
    return run_command("DELETE FROM customer WHERE cust_id = %s", (cust_id,))


# ---------- สินค้า (product) ----------
def search_products(filters):
    sql = "SELECT * FROM product WHERE 1=1"
    params = []
    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append(f"%{filters['name']}%")
    if filters.get("category"):
        sql += " AND category LIKE %s"
        params.append(f"%{filters['category']}%")
    sql += " ORDER BY product_id"
    return run_query(sql, params)


def get_product(product_id):
    rows = run_query("SELECT * FROM product WHERE product_id = %s", (product_id,))
    return rows[0] if rows else None


def create_product(data):
    sql = """INSERT INTO product (name, category, price, stock)
             VALUES (%s, %s, %s, %s)"""
    return run_command(sql, (data["name"], blank_to_none(data.get("category")),
                             data["price"], data["stock"]))


def update_product(product_id, data):
    sql = """UPDATE product SET name = %s, category = %s, price = %s, stock = %s
             WHERE product_id = %s"""
    return run_command(sql, (data["name"], blank_to_none(data.get("category")),
                             data["price"], data["stock"], product_id))


def delete_product(product_id):
    sql = """SELECT (SELECT COUNT(*) FROM order_line WHERE product_id = %s)
                  + (SELECT COUNT(*) FROM review WHERE product_id = %s) AS n"""
    if run_query(sql, (product_id, product_id))[0]["n"]:
        raise ValueError("สินค้านี้มีในออเดอร์หรือรีวิวแล้ว ลบไม่ได้")
    return run_command("DELETE FROM product WHERE product_id = %s", (product_id,))


# ---------- ออเดอร์ (shop_order) ----------
def search_orders(filters):
    # CAST AS CHAR ให้วันที่เป็น 'YYYY-MM-DD' ที่ <input type=date> อ่านได้
    sql = """SELECT o.order_id, o.cust_id, c.name AS customer_name,
                    CAST(o.order_date AS CHAR) AS order_date,
                    o.status, IFNULL(t.total, 0) AS total
             FROM shop_order o
             INNER JOIN customer c ON o.cust_id = c.cust_id
             LEFT JOIN (SELECT order_id, SUM(qty * unit_price) AS total
                        FROM order_line GROUP BY order_id) t ON o.order_id = t.order_id
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
    sql = """SELECT order_id, cust_id, CAST(order_date AS CHAR) AS order_date, status
             FROM shop_order WHERE order_id = %s"""
    rows = run_query(sql, (order_id,))
    return rows[0] if rows else None


def _is_paid(order_id):
    sql = "SELECT EXISTS (SELECT 1 FROM payment WHERE order_id = %s) AS paid"
    return bool(run_query(sql, (order_id,))[0]["paid"])


def check_can_ship(order_id):
    """จัดส่งได้เฉพาะออเดอร์ที่มีแถวใน payment"""
    if not _is_paid(order_id):
        raise ValueError("ออเดอร์นี้ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")


def create_order(data):
    if data["status"] == "shipped":
        raise ValueError("ออเดอร์ใหม่ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")
    sql = "INSERT INTO shop_order (cust_id, order_date, status) VALUES (%s, %s, %s)"
    return run_command(sql, (data["cust_id"], data["order_date"], data["status"]))


def update_order(order_id, data):
    if data["status"] == "shipped":
        check_can_ship(order_id)
    sql = "UPDATE shop_order SET cust_id = %s, order_date = %s, status = %s WHERE order_id = %s"
    return run_command(sql, (data["cust_id"], data["order_date"], data["status"], order_id))


def delete_order(order_id):
    if _is_paid(order_id):
        raise ValueError("ออเดอร์นี้ชำระเงินแล้ว ลบไม่ได้")
    run_command("DELETE FROM order_line WHERE order_id = %s", (order_id,))
    return run_command("DELETE FROM shop_order WHERE order_id = %s", (order_id,))


# ============================================================
#  REPORT (รายงาน — ใช้ JOIN + GROUP BY + subquery)
# ============================================================
def report_summary():
    sql = """SELECT
               (SELECT COUNT(*) FROM customer)   AS 'ลูกค้า',
               (SELECT COUNT(*) FROM product)    AS 'สินค้า',
               (SELECT COUNT(*) FROM shop_order) AS 'ออเดอร์',
               (SELECT COUNT(*) FROM review)     AS 'รีวิว',
               (SELECT IFNULL(SUM(amount), 0) FROM payment) AS 'รายได้รวม (บาท)',
               (SELECT COUNT(*) FROM shop_order WHERE status = 'pending') AS 'ออเดอร์รอดำเนินการ'"""
    return run_query(sql)[0]


def report_best_selling():
    # JOIN 3 ตาราง: order_line -> product (ชื่อสินค้า) และ order_line -> shop_order (ตรวจสถานะ)
    # นับเฉพาะออเดอร์ที่ไม่ถูกยกเลิก เพราะออเดอร์ที่ยกเลิกไม่ถือว่าขายได้
    sql = """SELECT p.name AS 'สินค้า', p.category AS 'หมวดหมู่',
                    SUM(ol.qty) AS 'จำนวนที่ขายได้'
             FROM order_line ol
             INNER JOIN product p ON ol.product_id = p.product_id
             INNER JOIN shop_order o ON ol.order_id = o.order_id
             WHERE o.status <> 'cancelled'
             GROUP BY p.product_id, p.name, p.category
             ORDER BY SUM(ol.qty) DESC, p.name
             LIMIT 5"""
    return run_query(sql)


def report_customers_above_avg():
    # subquery: ยอดรวมต่อลูกค้าแต่ละคนก่อน แล้วค่อย AVG ของยอดเหล่านั้น
    sql = """SELECT c.name AS 'ลูกค้า', c.tier AS 'ระดับ',
                    SUM(ol.qty * ol.unit_price) AS 'ยอดซื้อรวม'
             FROM customer c
             INNER JOIN shop_order o ON c.cust_id = o.cust_id
             INNER JOIN order_line ol ON o.order_id = ol.order_id
             WHERE o.status <> 'cancelled'
             GROUP BY c.cust_id, c.name, c.tier
             HAVING SUM(ol.qty * ol.unit_price) > (
                 SELECT AVG(per_cust.total)
                 FROM (SELECT SUM(ol2.qty * ol2.unit_price) AS total
                       FROM shop_order o2
                       INNER JOIN order_line ol2 ON o2.order_id = ol2.order_id
                       WHERE o2.status <> 'cancelled'
                       GROUP BY o2.cust_id) per_cust)
             ORDER BY SUM(ol.qty * ol.unit_price) DESC"""
    return run_query(sql)


def report_high_rated():
    # JOIN 3 ตาราง: review -> product (ชื่อสินค้า) และ review -> customer (นับจำนวนผู้รีวิว)
    # WHERE กรองก่อนจัดกลุ่ม / HAVING กรองหลังจัดกลุ่ม (คะแนนเฉลี่ยต้อง >= 4)
    sql = """SELECT p.name AS 'สินค้า', ROUND(AVG(r.rating), 2) AS 'คะแนนเฉลี่ย',
                    COUNT(DISTINCT c.cust_id) AS 'จำนวนผู้รีวิว'
             FROM review r
             INNER JOIN product p ON r.product_id = p.product_id
             INNER JOIN customer c ON r.cust_id = c.cust_id
             GROUP BY p.product_id, p.name
             HAVING AVG(r.rating) >= 4
             ORDER BY AVG(r.rating) DESC"""
    return run_query(sql)


# ============================================================
#  รายการรายงานที่แสดงบนหน้า /report  (ต้องอยู่ท้ายไฟล์)
# ============================================================
REPORTS = [
    ("best-selling",  "📈 สินค้าขายดี (Best Sellers)",                    report_best_selling),
    ("top-customers", "🏅 ลูกค้าที่ซื้อมากกว่าค่าเฉลี่ย (Above Average)", report_customers_above_avg),
    ("high-rated",    "⭐ สินค้าคะแนนรีวิวเฉลี่ย ≥ 4 (HAVING)",           report_high_rated),
]
