import mysql.connector
import config


def get_connection():
    return mysql.connector.connect(
        host=config.DB_HOST,
        user=config.DB_USER,
        password=config.DB_PASSWORD,
        database=config.DB_NAME,
        port=config.DB_PORT
    )


def run_query(sql, params=()):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute(sql, params)
    rows = cursor.fetchall()
    cursor.close()
    connection.close()
    return rows


def run_command(sql, params=()):
    connection = get_connection()
    cursor = connection.cursor()
    cursor.execute(sql, params)
    connection.commit()
    result = {"new_id": cursor.lastrowid, "affected": cursor.rowcount}
    cursor.close()
    connection.close()
    return result


def empty_to_none(value):
    if value == "" or value is None:
        return None
    return value


# ---------- customer ----------

TIER_ORDER = ["regular", "silver", "gold", "vip"]
TIER_RULES = [("vip", 60000), ("gold", 30000), ("silver", 15000)]


def search_customers(filters):
    sql = """
        SELECT customer.*,
               IFNULL(spending.total, 0) AS total_spent
        FROM customer
        LEFT JOIN (
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

    if filters.get("name"):
        sql += " AND customer.name LIKE %s"
        params.append("%" + filters["name"] + "%")
    if filters.get("email"):
        sql += " AND customer.email LIKE %s"
        params.append("%" + filters["email"] + "%")
    if filters.get("tier"):
        sql += " AND customer.tier = %s"
        params.append(filters["tier"])

    sql += " ORDER BY customer.cust_id"
    return run_query(sql, params)


def get_total_spent(cust_id):
    sql = """
        SELECT IFNULL(SUM(order_line.qty * order_line.unit_price), 0) AS total
        FROM shop_order
        JOIN order_line ON shop_order.order_id = order_line.order_id
        WHERE shop_order.cust_id = %s AND shop_order.status <> 'cancelled'
    """
    return run_query(sql, (cust_id,))[0]["total"]


def promote_customer(cust_id):
    total_spent = get_total_spent(cust_id)

    new_tier = "regular"
    for tier, minimum in TIER_RULES:
        if total_spent >= minimum:
            new_tier = tier
            break

    customer = get_customer(cust_id)
    if customer is None or customer["tier"] not in TIER_ORDER:
        return
    if TIER_ORDER.index(new_tier) > TIER_ORDER.index(customer["tier"]):
        run_command("UPDATE customer SET tier = %s WHERE cust_id = %s", (new_tier, cust_id))


def get_customer(cust_id):
    rows = run_query("SELECT * FROM customer WHERE cust_id = %s", (cust_id,))
    if len(rows) == 0:
        return None
    return rows[0]


def check_email(email, cust_id=0):
    if email is None:
        return
    rows = run_query("SELECT * FROM customer WHERE email = %s AND cust_id <> %s", (email, cust_id))
    if len(rows) > 0:
        raise ValueError("อีเมล " + email + " ถูกใช้แล้ว")


def create_customer(data):
    email = empty_to_none(data["email"])
    address = empty_to_none(data["address"])
    check_email(email)

    sql = "INSERT INTO customer (name, email, address, tier) VALUES (%s, %s, %s, %s)"
    return run_command(sql, (data["name"], email, address, data["tier"]))


def update_customer(cust_id, data):
    email = empty_to_none(data["email"])
    address = empty_to_none(data["address"])
    check_email(email, cust_id)

    sql = "UPDATE customer SET name = %s, email = %s, address = %s, tier = %s WHERE cust_id = %s"
    return run_command(sql, (data["name"], email, address, data["tier"], cust_id))


def delete_customer(cust_id):
    orders = run_query("SELECT * FROM shop_order WHERE cust_id = %s", (cust_id,))
    reviews = run_query("SELECT * FROM review WHERE cust_id = %s", (cust_id,))
    if len(orders) > 0 or len(reviews) > 0:
        raise ValueError("ลูกค้ารายนี้มีออเดอร์หรือรีวิวอยู่ ลบไม่ได้")

    return run_command("DELETE FROM customer WHERE cust_id = %s", (cust_id,))


# ---------- product ----------

def search_products(filters):
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
    rows = run_query("SELECT * FROM product WHERE product_id = %s", (product_id,))
    if len(rows) == 0:
        return None
    return rows[0]


def check_product_name(name, product_id=0):
    rows = run_query("SELECT * FROM product WHERE name = %s AND product_id <> %s", (name, product_id))
    if len(rows) > 0:
        raise ValueError("มีสินค้าชื่อ " + name + " อยู่แล้ว")


def check_price_stock(price, stock):
    try:
        price = float(price)
        stock = float(stock)
    except (TypeError, ValueError):
        raise ValueError("ราคาและสต็อกต้องเป็นตัวเลข")

    if price < 0:
        raise ValueError("ราคาต้องเป็น 0 หรือมากกว่า")
    if stock < 0 or stock != int(stock):
        raise ValueError("สต็อกต้องเป็นจำนวนเต็ม 0 หรือมากกว่า")


def create_product(data):
    name = data["name"].strip()
    category = empty_to_none(data["category"])
    check_product_name(name)
    check_price_stock(data["price"], data["stock"])

    sql = "INSERT INTO product (name, category, price, stock) VALUES (%s, %s, %s, %s)"
    return run_command(sql, (name, category, data["price"], data["stock"]))


def update_product(product_id, data):
    name = data["name"].strip()
    category = empty_to_none(data["category"])
    check_product_name(name, product_id)
    check_price_stock(data["price"], data["stock"])

    sql = "UPDATE product SET name = %s, category = %s, price = %s, stock = %s WHERE product_id = %s"
    return run_command(sql, (name, category, data["price"], data["stock"], product_id))


def delete_product(product_id):
    lines = run_query("SELECT * FROM order_line WHERE product_id = %s", (product_id,))
    reviews = run_query("SELECT * FROM review WHERE product_id = %s", (product_id,))
    if len(lines) > 0 or len(reviews) > 0:
        raise ValueError("สินค้านี้มีในออเดอร์หรือรีวิวแล้ว ลบไม่ได้")

    return run_command("DELETE FROM product WHERE product_id = %s", (product_id,))


# ---------- order ----------

ORDER_STATUSES = ["pending", "paid", "shipped", "completed", "cancelled"]
PAYMENT_METHODS = ["credit_card", "promptpay", "transfer", "cash"]


def search_orders(filters):
    sql = """
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

    if filters.get("cust_id"):
        sql += " AND shop_order.cust_id = %s"
        params.append(filters["cust_id"])
    if filters.get("status"):
        sql += " AND shop_order.status = %s"
        params.append(filters["status"])

    sql += " ORDER BY shop_order.order_id"
    return run_query(sql, params)


def get_order(order_id):
    sql = """
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


def check_status(status):
    if status not in ORDER_STATUSES:
        raise ValueError("สถานะ " + status + " ไม่ถูกต้อง")


def is_paid(order_id):
    rows = run_query("SELECT * FROM payment WHERE order_id = %s", (order_id,))
    return len(rows) > 0


def check_payment(data):
    method = empty_to_none(data.get("method"))
    amount = empty_to_none(data.get("amount"))

    if amount is None:
        return None
    if method is not None and method not in PAYMENT_METHODS:
        raise ValueError("วิธีชำระเงิน " + method + " ไม่ถูกต้อง")

    try:
        amount = float(amount)
    except ValueError:
        raise ValueError("ยอดเงินต้องเป็นตัวเลข")
    if amount <= 0:
        raise ValueError("ยอดเงินต้องมากกว่า 0")

    return method, amount


def save_payment(order_id, order_date, payment):
    if payment is None:
        return

    method, amount = payment
    if is_paid(order_id):
        run_command("UPDATE payment SET amount = %s WHERE order_id = %s", (amount, order_id))
        if method is not None:
            run_command("UPDATE payment SET method = %s WHERE order_id = %s", (method, order_id))
    else:
        if method is None:
            method = "cash"
        sql = "INSERT INTO payment (order_id, method, amount, paid_date) VALUES (%s, %s, %s, %s)"
        run_command(sql, (order_id, method, amount, order_date))


def create_order(data):
    check_status(data["status"])
    payment = check_payment(data)
    if data["status"] == "shipped" and payment is None:
        raise ValueError("ออเดอร์ใหม่ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")

    sql = "INSERT INTO shop_order (cust_id, order_date, status) VALUES (%s, %s, %s)"
    result = run_command(sql, (data["cust_id"], data["order_date"], data["status"]))
    save_payment(result["new_id"], data["order_date"], payment)
    promote_customer(data["cust_id"])
    return result


def update_order(order_id, data):
    check_status(data["status"])
    payment = check_payment(data)
    if data["status"] == "shipped" and payment is None and not is_paid(order_id):
        raise ValueError("ออเดอร์นี้ยังไม่ได้ชำระเงิน จัดส่งไม่ได้")

    sql = "UPDATE shop_order SET cust_id = %s, order_date = %s, status = %s WHERE order_id = %s"
    result = run_command(sql, (data["cust_id"], data["order_date"], data["status"], order_id))
    save_payment(order_id, data["order_date"], payment)
    promote_customer(data["cust_id"])
    return result


def delete_order(order_id):
    if is_paid(order_id):
        raise ValueError("ออเดอร์นี้ชำระเงินแล้ว ลบไม่ได้")

    run_command("DELETE FROM order_line WHERE order_id = %s", (order_id,))
    return run_command("DELETE FROM shop_order WHERE order_id = %s", (order_id,))


# ---------- reports ----------

def report_summary():
    sql = """
        SELECT
            (SELECT COUNT(*) FROM customer) AS 'ลูกค้า',
            (SELECT COUNT(*) FROM product) AS 'สินค้า',
            (SELECT COUNT(*) FROM shop_order) AS 'ออเดอร์',
            (SELECT COUNT(*) FROM review) AS 'รีวิว',
            (SELECT IFNULL(SUM(amount), 0) FROM payment) AS 'รายได้รวม (บาท)',
            (SELECT COUNT(*) FROM shop_order WHERE status = 'pending') AS 'ออเดอร์รอดำเนินการ'
    """
    return run_query(sql)[0]


def report_best_selling():
    sql = """
        SELECT product.name AS 'สินค้า',
               product.category AS 'หมวดหมู่',
               SUM(order_line.qty) AS 'จำนวนที่ขายได้'
        FROM order_line
        JOIN product ON order_line.product_id = product.product_id
        JOIN shop_order ON order_line.order_id = shop_order.order_id
        WHERE shop_order.status <> 'cancelled'
        GROUP BY product.product_id, product.name, product.category
        ORDER BY SUM(order_line.qty) DESC, product.name
        LIMIT 5
    """
    return run_query(sql)


def report_customers_above_avg():
    sql = """
        SELECT customer.name AS 'ลูกค้า',
               customer.tier AS 'ระดับ',
               SUM(order_line.qty * order_line.unit_price) AS 'ยอดซื้อรวม'
        FROM customer
        JOIN shop_order ON customer.cust_id = shop_order.cust_id
        JOIN order_line ON shop_order.order_id = order_line.order_id
        WHERE shop_order.status <> 'cancelled'
        GROUP BY customer.cust_id, customer.name, customer.tier
        HAVING SUM(order_line.qty * order_line.unit_price) > (
            SELECT AVG(total_per_customer.total)
            FROM (
                SELECT SUM(order_line.qty * order_line.unit_price) AS total
                FROM shop_order
                JOIN order_line ON shop_order.order_id = order_line.order_id
                WHERE shop_order.status <> 'cancelled'
                GROUP BY shop_order.cust_id
            ) AS total_per_customer
        )
        ORDER BY SUM(order_line.qty * order_line.unit_price) DESC
    """
    return run_query(sql)


def report_high_rated():
    sql = """
        SELECT product.name AS 'สินค้า',
               ROUND(AVG(review.rating), 2) AS 'คะแนนเฉลี่ย',
               COUNT(DISTINCT customer.cust_id) AS 'จำนวนผู้รีวิว'
        FROM review
        JOIN product ON review.product_id = product.product_id
        JOIN customer ON review.cust_id = customer.cust_id
        GROUP BY product.product_id, product.name
        HAVING AVG(review.rating) >= 4
        ORDER BY AVG(review.rating) DESC
    """
    return run_query(sql)


# ---------- top 10 ----------

def ranking_products_by_quantity():
    sql = """
        SELECT product.name AS 'สินค้า',
               SUM(order_line.qty) AS 'จำนวนที่ขายได้ (ชิ้น)'
        FROM order_line
        JOIN product ON order_line.product_id = product.product_id
        JOIN shop_order ON order_line.order_id = shop_order.order_id
        WHERE shop_order.status <> 'cancelled'
        GROUP BY product.product_id, product.name
        ORDER BY SUM(order_line.qty) DESC, product.name
        LIMIT 10
    """
    return run_query(sql)


def ranking_products_by_revenue():
    sql = """
        SELECT product.name AS 'สินค้า',
               SUM(order_line.qty * order_line.unit_price) AS 'ยอดขาย (บาท)'
        FROM order_line
        JOIN product ON order_line.product_id = product.product_id
        JOIN shop_order ON order_line.order_id = shop_order.order_id
        WHERE shop_order.status <> 'cancelled'
        GROUP BY product.product_id, product.name
        ORDER BY SUM(order_line.qty * order_line.unit_price) DESC, product.name
        LIMIT 10
    """
    return run_query(sql)


def ranking_customers_by_spending():
    sql = """
        SELECT customer.name AS 'ลูกค้า',
               SUM(order_line.qty * order_line.unit_price) AS 'ยอดซื้อรวม (บาท)'
        FROM customer
        JOIN shop_order ON customer.cust_id = shop_order.cust_id
        JOIN order_line ON shop_order.order_id = order_line.order_id
        WHERE shop_order.status <> 'cancelled'
        GROUP BY customer.cust_id, customer.name
        ORDER BY SUM(order_line.qty * order_line.unit_price) DESC, customer.name
        LIMIT 10
    """
    return run_query(sql)
