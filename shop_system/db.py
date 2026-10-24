import mysql.connector
import config


# ---------- ตัวช่วยพื้นฐาน (ทุกฟังก์ชันใช้) ----------

# เชื่อม MySQL ด้วยค่าใน config.py
def get_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT
    )


# รัน SELECT แล้วคืนผลเป็น list ของ dict (หนึ่ง dict = หนึ่งแถว)
def run_query(sql, params=()):
    # ขั้น 1: เปิดสายแล้วรันคำสั่ง (ค่าส่งแยกผ่าน %s กัน SQL injection)
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, params)

    # ขั้น 2: ดึงผลทุกแถว แล้วปิดสาย
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


# รัน INSERT / UPDATE / DELETE แล้วบันทึกจริง คืนรหัสแถวใหม่และจำนวนแถวที่เปลี่ยน
def run_command(sql, params=()):
    # ขั้น 1: เปิดสายแล้วรันคำสั่ง
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql, params)

    # ขั้น 2: บันทึกจริง (ไม่ commit ข้อมูลจะหาย) แล้วปิดสาย
    connection.commit()
    result = {"new_id": cursor.lastrowid, "affected": cursor.rowcount}
    cursor.close()
    connection.close()
    return result


# ช่องว่างจากฟอร์ม -> None (เก็บเป็น NULL) กันอีเมลที่เป็น UNIQUE ซ้ำกันเอง
def empty_to_none(value):
    if value == "" or value is None:
        return None
    return value


# ---------- customer ----------

TIER_ORDER = ["regular", "silver", "gold", "vip"]  # ลำดับระดับ ต่ำไปสูง
TIER_RULES = [("vip", 60000), ("gold", 30000), ("silver", 15000)]  # ยอดซื้อขั้นต่ำของแต่ละระดับ


# ค้นหาลูกค้าตามชื่อ / อีเมล / ระดับ พร้อมยอดซื้อสะสมของแต่ละคน
def search_customers(filters):
    # ขั้น 1: SQL ตั้งต้น ดึงลูกค้าทุกคนพร้อมยอดซื้อสะสม
    sql = """
        # ดึงข้อมูลลูกค้า + ยอดซื้อสะสม (ไม่เคยซื้อ = 0)
        SELECT customer.*, IFNULL(spending.total, 0) AS total_spent
        FROM customer
        LEFT JOIN (
            # ยอดซื้อรวมต่อลูกค้า ไม่นับออเดอร์ที่ยกเลิก
            SELECT shop_order.cust_id,
                   SUM(order_line.qty * order_line.unit_price) AS total
            FROM shop_order
            JOIN order_line ON shop_order.order_id = order_line.order_id

            WHERE shop_order.status <> 'cancelled'
            
            GROUP BY shop_order.cust_id
        ) AS spending ON customer.cust_id = spending.cust_id
        WHERE 1=1
    """
    params = []

    # ขั้น 2: ต่อเงื่อนไขเฉพาะช่องที่ผู้ใช้กรอก (ค่าเก็บใน params)
    if filters.get("name"):
        sql += " AND customer.name LIKE %s"
        params.append("%" + filters["name"] + "%")
    if filters.get("email"):
        sql += " AND customer.email LIKE %s"
        params.append("%" + filters["email"] + "%")
    if filters.get("tier"):
        sql += " AND customer.tier = %s"
        params.append(filters["tier"])

    # ขั้น 3: เรียงตามรหัสแล้วรัน
    sql += " ORDER BY customer.cust_id"
    return run_query(sql, params)


# รวมยอดซื้อของลูกค้า 1 คน (ไม่นับออเดอร์ที่ยกเลิก) คืนเป็นตัวเลข
def get_total_spent(cust_id):
    sql = """
        # รวม จำนวน x ราคา ของทุกรายการในออเดอร์ของลูกค้าคนนี้
        SELECT IFNULL(SUM(order_line.qty * order_line.unit_price), 0) AS total
        FROM shop_order
        JOIN order_line ON shop_order.order_id = order_line.order_id
        WHERE shop_order.cust_id = %s AND shop_order.status <> 'cancelled'
    """
    return run_query(sql, (cust_id,))[0]["total"]


# เลื่อนระดับลูกค้าตามยอดซื้อ (เลื่อนขึ้นอย่างเดียว ไม่ลดระดับ)
def promote_customer(cust_id):
    # ขั้น 1: ดูยอดซื้อสะสม แล้วหาว่าถึงเกณฑ์ระดับไหน (ไล่จากสูงสุดลงมา)
    total_spent = get_total_spent(cust_id)
    new_tier = "regular"
    for tier, minimum in TIER_RULES:
        if total_spent >= minimum:
            new_tier = tier
            break

    # ขั้น 2: ถ้าระดับใหม่สูงกว่าระดับปัจจุบัน ค่อยแก้ในตาราง
    customer = get_customer(cust_id)
    if customer is None or customer["tier"] not in TIER_ORDER:
        return
    if TIER_ORDER.index(new_tier) > TIER_ORDER.index(customer["tier"]):
        sql = """
            # ตั้งระดับใหม่ให้ลูกค้าคนนี้
            UPDATE customer SET tier = %s WHERE cust_id = %s
        """
        run_command(sql, (new_tier, cust_id))


# ดึงลูกค้า 1 คนตามรหัส (ใช้เติมฟอร์มแก้ไข) ไม่เจอคืน None
def get_customer(cust_id):
    sql = """
        # ดึงทุกคอลัมน์ของลูกค้ารหัสนี้
        SELECT * FROM customer WHERE cust_id = %s
    """
    rows = run_query(sql, (cust_id,))
    if len(rows) == 0:
        return None
    return rows[0]


# ตรวจว่าอีเมลซ้ำกับลูกค้าคนอื่นไหม (cust_id = ตัวเองตอนแก้ไข จะได้ไม่นับตัวเอง)
def check_email(email, cust_id=0):
    if email is None:
        return

    sql = """
        # หาลูกค้าอื่นที่ใช้อีเมลนี้อยู่
        SELECT * FROM customer WHERE email = %s AND cust_id <> %s
    """
    rows = run_query(sql, (email, cust_id))
    if len(rows) > 0:
        raise ValueError("อีเมล " + email + " ถูกใช้แล้ว")


# ตรวจเงินคงเหลือต้องเป็นตัวเลข >= 0 (ไม่กรอก = 0) คืนเป็นตัวเลข
def check_balance(balance):
    if balance is None or balance == "":
        return 0

    try:
        balance = float(balance)
    except (TypeError, ValueError):
        raise ValueError("เงินคงเหลือต้องเป็นตัวเลข")
    if balance < 0:
        raise ValueError("เงินคงเหลือต้องเป็น 0 หรือมากกว่า")
    return balance


# เพิ่มลูกค้าใหม่ (data = ข้อมูลจากฟอร์ม)
def create_customer(data):
    # ขั้น 1: เตรียมค่า (ช่องว่างเก็บเป็น NULL) และตรวจอีเมลซ้ำ
    email = empty_to_none(data["email"])
    address = empty_to_none(data["address"])
    balance = check_balance(data.get("balance"))
    check_email(email)

    # ขั้น 2: บันทึกลงตาราง customer
    sql = """
        # เพิ่มลูกค้า 1 แถว
        INSERT INTO customer (name, email, address, tier, balance) VALUES (%s, %s, %s, %s, %s)
    """
    return run_command(sql, (data["name"], email, address, data["tier"], balance))


# แก้ไขข้อมูลลูกค้า
def update_customer(cust_id, data):
    # ขั้น 1: เตรียมค่า และตรวจอีเมลซ้ำ (ไม่นับตัวเอง)
    email = empty_to_none(data["email"])
    address = empty_to_none(data["address"])
    balance = check_balance(data.get("balance"))
    check_email(email, cust_id)

    # ขั้น 2: บันทึกค่าใหม่
    sql = """
        # แก้ข้อมูลของลูกค้าคนนี้
        UPDATE customer
        SET name = %s, email = %s, address = %s, tier = %s, balance = %s
        WHERE cust_id = %s
    """
    return run_command(sql, (data["name"], email, address, data["tier"], balance, cust_id))


# ลบลูกค้า (ถ้ามีออเดอร์หรือรีวิวอยู่ ห้ามลบ)
def delete_customer(cust_id):
    # ขั้น 1: ดูว่าลูกค้ามีออเดอร์หรือรีวิวไหม
    sql_orders = "SELECT * FROM shop_order WHERE cust_id = %s"
    sql_reviews = "SELECT * FROM review WHERE cust_id = %s"
    orders = run_query(sql_orders, (cust_id,))
    reviews = run_query(sql_reviews, (cust_id,))
    if len(orders) > 0 or len(reviews) > 0:
        raise ValueError("ลูกค้ารายนี้มีออเดอร์หรือรีวิวอยู่ ลบไม่ได้")

    # ขั้น 2: ไม่มี -> ลบได้
    sql = "DELETE FROM customer WHERE cust_id = %s"
    return run_command(sql, (cust_id,))


# ---------- product ----------

# ค้นหาสินค้าตามชื่อ / หมวดหมู่
def search_products(filters):
    # ขั้น 1: SQL ตั้งต้น ดึงสินค้าทุกตัว
    sql = "SELECT * FROM product WHERE 1=1"
    params = []

    # ขั้น 2: ต่อเงื่อนไขเฉพาะช่องที่ผู้ใช้กรอก
    if filters.get("name"):
        sql += " AND name LIKE %s"
        params.append("%" + filters["name"] + "%")
    if filters.get("category"):
        sql += " AND category LIKE %s"
        params.append("%" + filters["category"] + "%")

    # ขั้น 3: เรียงตามรหัสแล้วรัน
    sql += " ORDER BY product_id"
    return run_query(sql, params)


# ดึงสินค้า 1 ตัวตามรหัส ไม่เจอคืน None
def get_product(product_id):
    sql = """
        # ดึงทุกคอลัมน์ของสินค้ารหัสนี้
        SELECT * FROM product WHERE product_id = %s
    """
    rows = run_query(sql, (product_id,))
    if len(rows) == 0:
        return None
    return rows[0]


# ตรวจว่าชื่อสินค้าซ้ำกับตัวอื่นไหม (ไม่นับตัวเองตอนแก้ไข)
def check_product_name(name, product_id=0):
    sql = """
        # หาสินค้าตัวอื่นที่ใช้ชื่อนี้อยู่
        SELECT * FROM product WHERE name = %s AND product_id <> %s
    """
    rows = run_query(sql, (name, product_id))
    if len(rows) > 0:
        raise ValueError("มีสินค้าชื่อ " + name + " อยู่แล้ว")


# ตรวจว่าราคาเป็นเลข >= 0 และสต็อกเป็นจำนวนเต็ม >= 0
def check_price_stock(price, stock):
    # ขั้น 1: แปลงเป็นตัวเลข (แปลงไม่ได้ เช่น "abc" = ผิด)
    try:
        price = float(price)
        stock = float(stock)
    except (TypeError, ValueError):
        raise ValueError("ราคาและสต็อกต้องเป็นตัวเลข")

    # ขั้น 2: ตรวจค่า
    if price < 0:
        raise ValueError("ราคาต้องเป็น 0 หรือมากกว่า")
    if stock < 0 or stock != int(stock):
        raise ValueError("สต็อกต้องเป็นจำนวนเต็ม 0 หรือมากกว่า")


# เพิ่มสินค้าใหม่
def create_product(data):
    # ขั้น 1: เตรียมค่า แล้วตรวจชื่อซ้ำ ราคา และสต็อก
    name = data["name"].strip()
    category = empty_to_none(data["category"])
    check_product_name(name)
    check_price_stock(data["price"], data["stock"])

    # ขั้น 2: บันทึกลงตาราง product
    sql = """
        # เพิ่มสินค้า 1 แถว
        INSERT INTO product (name, category, price, stock) VALUES (%s, %s, %s, %s)
    """
    return run_command(sql, (name, category, data["price"], data["stock"]))


# แก้ไขสินค้า
def update_product(product_id, data):
    # ขั้น 1: เตรียมค่า แล้วตรวจชื่อซ้ำ (ไม่นับตัวเอง) ราคา และสต็อก
    name = data["name"].strip()
    category = empty_to_none(data["category"])
    check_product_name(name, product_id)
    check_price_stock(data["price"], data["stock"])

    # ขั้น 2: บันทึกค่าใหม่
    sql = """
        # แก้ข้อมูลของสินค้าตัวนี้
        UPDATE product
        SET name = %s, category = %s, price = %s, stock = %s
        WHERE product_id = %s
    """
    return run_command(sql, (name, category, data["price"], data["stock"], product_id))


# ลบสินค้า (ถ้าอยู่ในออเดอร์หรือมีรีวิว ห้ามลบ)
def delete_product(product_id):
    # ขั้น 1: ดูว่าสินค้าเคยถูกสั่งหรือมีรีวิวไหม
    sql_lines = "SELECT * FROM order_line WHERE product_id = %s"
    sql_reviews = "SELECT * FROM review WHERE product_id = %s"
    lines = run_query(sql_lines, (product_id,))
    reviews = run_query(sql_reviews, (product_id,))
    if len(lines) > 0 or len(reviews) > 0:
        raise ValueError("สินค้านี้มีในออเดอร์หรือรีวิวแล้ว ลบไม่ได้")

    # ขั้น 2: ไม่มี -> ลบได้
    sql = "DELETE FROM product WHERE product_id = %s"
    return run_command(sql, (product_id,))


# ---------- order ----------

ORDER_STATUSES = ["pending", "paid", "shipped", "completed", "cancelled"]  # สถานะที่อนุญาต
PAYMENT_METHODS = ["credit_card", "promptpay", "transfer", "cash"]  # วิธีชำระเงินที่อนุญาต


# ค้นหาออเดอร์ตามลูกค้า / สถานะ พร้อมชื่อลูกค้า สินค้าที่สั่ง จำนวน และยอดรวม
def search_orders(filters):
    # ขั้น 1: SQL ตั้งต้น ดึงออเดอร์ทุกใบ
    sql = """
        # ดึงออเดอร์ + ชื่อลูกค้า + สรุปสินค้าในออเดอร์ (ไม่มีสินค้า = จำนวน 0 ยอด 0)
        SELECT shop_order.order_id,
               shop_order.cust_id,
               customer.name AS customer_name,
               CAST(shop_order.order_date AS CHAR) AS order_date,
               shop_order.status,
               order_summary.items,
               IFNULL(order_summary.quantity, 0) AS quantity,
               IFNULL(order_summary.total, 0) AS total
        FROM shop_order
        JOIN customer ON shop_order.cust_id = customer.cust_id
        LEFT JOIN (
            # รวมสินค้าของแต่ละออเดอร์เป็นแถวเดียว: ข้อความรายการ จำนวนรวม ยอดรวม
            SELECT order_line.order_id,
                   GROUP_CONCAT(CONCAT(product.name, ' x', order_line.qty) SEPARATOR ', ') AS items,
                   SUM(order_line.qty) AS quantity,
                   SUM(order_line.qty * order_line.unit_price) AS total
            FROM order_line
            JOIN product ON order_line.product_id = product.product_id
            GROUP BY order_line.order_id
        ) AS order_summary ON shop_order.order_id = order_summary.order_id
        WHERE 1=1
    """
    params = []

    # ขั้น 2: ต่อเงื่อนไขเฉพาะช่องที่ผู้ใช้เลือก
    if filters.get("cust_id"):
        sql += " AND shop_order.cust_id = %s"
        params.append(filters["cust_id"])
    if filters.get("status"):
        sql += " AND shop_order.status = %s"
        params.append(filters["status"])

    # ขั้น 3: เรียงตามรหัสแล้วรัน
    sql += " ORDER BY shop_order.order_id"
    return run_query(sql, params)


# ดึงออเดอร์ 1 ใบ พร้อมวิธีและยอดชำระ (ใช้เติมฟอร์มแก้ไข) ไม่เจอคืน None
def get_order(order_id):
    sql = """
        # ดึงออเดอร์นี้ + การชำระเงิน (ยังไม่จ่ายก็ยังได้ออเดอร์ เพราะใช้ LEFT JOIN)
        SELECT shop_order.order_id,
               shop_order.cust_id,
               CAST(shop_order.order_date AS CHAR) AS order_date,
               shop_order.status,
               payment.method,
               payment.amount
        FROM shop_order
        LEFT JOIN payment ON shop_order.order_id = payment.order_id
        WHERE shop_order.order_id = %s
    """
    rows = run_query(sql, (order_id,))
    if len(rows) == 0:
        return None
    return rows[0]


# ตรวจว่าสถานะอยู่ในรายการที่อนุญาต
def check_status(status):
    if status not in ORDER_STATUSES:
        raise ValueError("สถานะ " + status + " ไม่ถูกต้อง")


# ออเดอร์นี้จ่ายแล้วหรือยัง (มีแถวใน payment = จ่ายแล้ว) คืน True / False
def is_paid(order_id):
    sql = """
        # หาการชำระเงินของออเดอร์นี้
        SELECT * FROM payment WHERE order_id = %s
    """
    rows = run_query(sql, (order_id,))
    return len(rows) > 0


# ตรวจยอดเงินและวิธีชำระ ไม่กรอกยอด = ไม่มีการชำระ (คืน None) ผ่านแล้วคืน (วิธี, ยอด)
def check_payment(data):
    # ขั้น 1: อ่านค่า ไม่กรอกยอดก็จบ
    method = empty_to_none(data.get("method"))
    amount = empty_to_none(data.get("amount"))
    if amount is None:
        return None
    if method is not None and method not in PAYMENT_METHODS:
        raise ValueError("วิธีชำระเงิน " + method + " ไม่ถูกต้อง")

    # ขั้น 2: ยอดต้องเป็นตัวเลขที่มากกว่า 0
    try:
        amount = float(amount)
    except ValueError:
        raise ValueError("ยอดเงินต้องเป็นตัวเลข")
    if amount <= 0:
        raise ValueError("ยอดเงินต้องมากกว่า 0")

    return method, amount


# บันทึกการชำระเงิน (เคยบันทึกแล้วแก้ยอด ยังไม่เคยเพิ่มใหม่)
def save_payment(order_id, order_date, payment):
    if payment is None:
        return

    method, amount = payment
    if is_paid(order_id):
        # เคยบันทึกแล้ว: แก้ยอด (และวิธี ถ้าระบุมา)
        sql_amount = "UPDATE payment SET amount = %s WHERE order_id = %s"
        run_command(sql_amount, (amount, order_id))
        if method is not None:
            sql_method = "UPDATE payment SET method = %s WHERE order_id = %s"
            run_command(sql_method, (method, order_id))
    else:
        # ยังไม่เคย: เพิ่มใหม่ (ไม่ระบุวิธี = เงินสด)
        if method is None:
            method = "cash"
        sql = """
            # เพิ่มการชำระเงิน 1 แถวให้ออเดอร์นี้
            INSERT INTO payment (order_id, method, amount, paid_date) VALUES (%s, %s, %s, %s)
        """
        run_command(sql, (order_id, method, amount, order_date))


# เพิ่มออเดอร์ใหม่ (ตรวจทุกอย่างก่อนเขียนข้อมูล)
def create_order(data):
    # ขั้น 1: ตรวจสถานะและยอดชำระ (ออเดอร์ใหม่ที่ยังไม่จ่ายตั้งเป็น shipped ไม่ได้)
    check_status(data["status"])
    payment = check_payment(data)
    if data["status"] == "shipped" and payment is None:
        raise ValueError("ออเดอร์ใหม่ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")

    # ขั้น 2: เพิ่มหัวออเดอร์ลงตาราง shop_order
    sql = """
        # เพิ่มออเดอร์ 1 ใบ
        INSERT INTO shop_order (cust_id, order_date, status) VALUES (%s, %s, %s)
    """
    result = run_command(sql, (data["cust_id"], data["order_date"], data["status"]))

    # ขั้น 3: บันทึกการชำระ (ใช้รหัสออเดอร์ที่เพิ่งได้) แล้วตรวจเลื่อนระดับลูกค้า
    save_payment(result["new_id"], data["order_date"], payment)
    promote_customer(data["cust_id"])
    return result


# แก้ไขออเดอร์ (จะเปลี่ยนเป็น shipped ได้ต้องจ่ายเงินแล้ว)
def update_order(order_id, data):
    # ขั้น 1: ตรวจสถานะและยอดชำระ
    check_status(data["status"])
    payment = check_payment(data)
    if data["status"] == "shipped" and payment is None and not is_paid(order_id):
        raise ValueError("ออเดอร์นี้ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")

    # ขั้น 2: แก้หัวออเดอร์
    sql = """
        # แก้ลูกค้า วันที่ สถานะ ของออเดอร์นี้
        UPDATE shop_order
        SET cust_id = %s, order_date = %s, status = %s
        WHERE order_id = %s
    """
    result = run_command(sql, (data["cust_id"], data["order_date"], data["status"], order_id))

    # ขั้น 3: บันทึกหรือแก้การชำระ แล้วตรวจเลื่อนระดับลูกค้า
    save_payment(order_id, data["order_date"], payment)
    promote_customer(data["cust_id"])
    return result


# ลบออเดอร์ (จ่ายแล้วห้ามลบ)
def delete_order(order_id):
    # ขั้น 1: ตรวจว่าจ่ายแล้วหรือยัง
    if is_paid(order_id):
        raise ValueError("ออเดอร์นี้ชำระเงินแล้ว ลบไม่ได้")

    # ขั้น 2: ลบรายการสินค้า (ลูก) ก่อน แล้วค่อยลบหัวออเดอร์ (แม่) ไม่งั้นติด FOREIGN KEY
    sql_lines = "DELETE FROM order_line WHERE order_id = %s"
    sql_order = "DELETE FROM shop_order WHERE order_id = %s"
    run_command(sql_lines, (order_id,))
    return run_command(sql_order, (order_id,))


# ---------- reports ----------

# การ์ดตัวเลขด้านบนของหน้ารายงาน (ทุกบรรทัดคือตัวเลข 1 ตัว ได้แถวเดียว)
def report_summary():
    sql = """
        # นับลูกค้า สินค้า ออเดอร์ รีวิว / รวมยอดชำระ / นับออเดอร์ที่ยังรอดำเนินการ
        SELECT
            (SELECT COUNT(*) FROM customer) AS 'ลูกค้า',
            (SELECT COUNT(*) FROM product) AS 'สินค้า',
            (SELECT COUNT(*) FROM shop_order) AS 'ออเดอร์',
            (SELECT COUNT(*) FROM review) AS 'รีวิว',
            (SELECT IFNULL(SUM(amount), 0) FROM payment) AS 'รายได้รวม (บาท)',
            (SELECT COUNT(*) FROM shop_order WHERE status = 'pending') AS 'ออเดอร์รอดำเนินการ'
    """
    return run_query(sql)[0]  # หยิบแถวแรก ได้ dict {"ลูกค้า": 9, "สินค้า": 11, ...}


# รายงาน 1: สินค้าขายดี 5 อันดับ (ผลจริง G502 = 15, Samsung 980 = 5, HyperX = 4, NZXT = 2, Ryzen = 1)
def report_best_selling():
    sql = """
        # ดึงชื่อสินค้า หมวดหมู่ และจำนวนที่ขายได้รวม
        SELECT product.name AS 'สินค้า',
               product.category AS 'หมวดหมู่',
               SUM(order_line.qty) AS 'จำนวนที่ขายได้'
        # ต่อ 3 ตาราง: รายการที่สั่ง -> สินค้า (เอาชื่อ) -> ออเดอร์ (เอาสถานะ)
        FROM order_line
        JOIN product ON order_line.product_id = product.product_id
        JOIN shop_order ON order_line.order_id = shop_order.order_id
        # ตัดออเดอร์ที่ยกเลิก แล้วรวมแถวของสินค้าเดียวกันเป็นหนึ่งแถว
        WHERE shop_order.status <> 'cancelled'
        GROUP BY product.product_id, product.name, product.category
        # ขายได้มากสุดก่อน (เท่ากันเรียงตามชื่อ) เอา 5 อันดับแรก
        ORDER BY SUM(order_line.qty) DESC, product.name
        LIMIT 5
    """
    return run_query(sql)


# รายงาน 2: ลูกค้าที่ยอดซื้อรวมมากกว่าค่าเฉลี่ยของลูกค้าทุกคน
def report_customers_above_avg():
    sql = """
        # ดึงชื่อ ระดับ และยอดซื้อรวม (จำนวน x ราคา ของทุกรายการ รวมต่อคน)
        SELECT customer.name AS 'ลูกค้า',
               customer.tier AS 'ระดับ',
               SUM(order_line.qty * order_line.unit_price) AS 'ยอดซื้อรวม'
        # ต่อ 3 ตาราง: ลูกค้า -> ออเดอร์ของลูกค้า -> รายการสินค้าในออเดอร์
        FROM customer
        JOIN shop_order ON customer.cust_id = shop_order.cust_id
        JOIN order_line ON shop_order.order_id = order_line.order_id
        # ตัดออเดอร์ที่ยกเลิก แล้วรวมแถวของลูกค้าคนเดียวกันเป็นแถวเดียว
        WHERE shop_order.status <> 'cancelled'
        GROUP BY customer.cust_id, customer.name, customer.tier
        # เก็บเฉพาะคนที่ยอดมากกว่าค่าเฉลี่ย (ค่าเฉลี่ยคำนวณในวงเล็บ)
        HAVING SUM(order_line.qty * order_line.unit_price) > (
            SELECT AVG(total_per_customer.total)
            FROM (
                # ยอดซื้อรวมของลูกค้าแต่ละคน (ตารางชั่วคราว) เพื่อเอามาหาค่าเฉลี่ย
                SELECT SUM(order_line.qty * order_line.unit_price) AS total
                FROM shop_order
                JOIN order_line ON shop_order.order_id = order_line.order_id
                WHERE shop_order.status <> 'cancelled'
                GROUP BY shop_order.cust_id
            ) AS total_per_customer
        )
        # คนซื้อมากสุดอยู่บนสุด
        ORDER BY SUM(order_line.qty * order_line.unit_price) DESC
    """
    return run_query(sql)


# รายงาน 3: สินค้าที่คะแนนรีวิวเฉลี่ยตั้งแต่ 4 ขึ้นไป
def report_high_rated():
    sql = """
        # ดึงชื่อสินค้า คะแนนเฉลี่ย (ปัดทศนิยม 2 ตำแหน่ง) และจำนวนคนรีวิว (ไม่นับซ้ำ)
        SELECT product.name AS 'สินค้า',
               ROUND(AVG(review.rating), 2) AS 'คะแนนเฉลี่ย',
               COUNT(DISTINCT customer.cust_id) AS 'จำนวนผู้รีวิว'
        # ต่อ 3 ตาราง: รีวิว -> สินค้าที่ถูกรีวิว -> ลูกค้าที่รีวิว
        FROM review
        JOIN product ON review.product_id = product.product_id
        JOIN customer ON review.cust_id = customer.cust_id
        # รวมรีวิวของสินค้าเดียวกันเป็นหนึ่งแถว
        GROUP BY product.product_id, product.name
        # เก็บเฉพาะที่เฉลี่ย 4 ขึ้นไป (กรองหลังเฉลี่ยจึงใช้ HAVING) เรียงคะแนนสูงสุดก่อน
        HAVING AVG(review.rating) >= 4
        ORDER BY AVG(review.rating) DESC
    """
    return run_query(sql)


# ---------- top 10 (ฟีเจอร์พิเศษ) ----------

# Top 10 สินค้าขายดี เรียงตามจำนวนชิ้นที่ขายได้
def ranking_products_by_quantity():
    sql = """
        # ดึงชื่อสินค้าและจำนวนที่ขายได้รวม
        SELECT product.name AS 'สินค้า',
               SUM(order_line.qty) AS 'จำนวนที่ขายได้ (ชิ้น)'
        FROM order_line
        JOIN product ON order_line.product_id = product.product_id
        JOIN shop_order ON order_line.order_id = shop_order.order_id
        # ตัดออเดอร์ที่ยกเลิก รวมเป็นสินค้าละแถว เรียงมากไปน้อย เอา 10 อันดับ
        WHERE shop_order.status <> 'cancelled'
        GROUP BY product.product_id, product.name
        ORDER BY SUM(order_line.qty) DESC, product.name
        LIMIT 10
    """
    return run_query(sql)


# Top 10 สินค้าทำเงินสูงสุด เรียงตามยอดขาย (จำนวน x ราคา)
def ranking_products_by_revenue():
    sql = """
        # ดึงชื่อสินค้าและยอดขายรวม
        SELECT product.name AS 'สินค้า',
               SUM(order_line.qty * order_line.unit_price) AS 'ยอดขาย (บาท)'
        FROM order_line
        JOIN product ON order_line.product_id = product.product_id
        JOIN shop_order ON order_line.order_id = shop_order.order_id
        # ตัดออเดอร์ที่ยกเลิก รวมเป็นสินค้าละแถว เรียงมากไปน้อย เอา 10 อันดับ
        WHERE shop_order.status <> 'cancelled'
        GROUP BY product.product_id, product.name
        ORDER BY SUM(order_line.qty * order_line.unit_price) DESC, product.name
        LIMIT 10
    """
    return run_query(sql)


# Top 10 ลูกค้าซื้อมากสุด เรียงตามยอดซื้อรวม
def ranking_customers_by_spending():
    sql = """
        # ดึงชื่อลูกค้าและยอดซื้อรวม
        SELECT customer.name AS 'ลูกค้า',
               SUM(order_line.qty * order_line.unit_price) AS 'ยอดซื้อรวม (บาท)'
        FROM customer
        JOIN shop_order ON customer.cust_id = shop_order.cust_id
        JOIN order_line ON shop_order.order_id = order_line.order_id
        # ตัดออเดอร์ที่ยกเลิก รวมเป็นลูกค้าคนละแถว เรียงมากไปน้อย เอา 10 อันดับ
        WHERE shop_order.status <> 'cancelled'
        GROUP BY customer.cust_id, customer.name
        ORDER BY SUM(order_line.qty * order_line.unit_price) DESC, customer.name
        LIMIT 10
    """
    return run_query(sql)
