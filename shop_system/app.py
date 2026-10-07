# app.py — รับคำขอจากหน้าเว็บแล้วส่งต่อให้ db.py (ไฟล์นี้ไม่มี SQL)
# รัน: python app.py แล้วเปิด http://127.0.0.1:5000
from flask import Flask, request, jsonify, render_template
import db

app = Flask(__name__)
app.json.sort_keys = False      # ให้หัวตารางเรียงตามลำดับใน SELECT


def reply(function, *args):
    """เรียกฟังก์ชันใน db.py แล้วตอบเป็น JSON: {"ok": true, "data": ...} หรือ {"ok": false, "error": ...}"""
    try:
        return jsonify({"ok": True, "data": function(*args)})
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 400


def get_filters():
    """เงื่อนไขค้นหาจาก URL (?name=สม&tier=gold) เอาเฉพาะช่องที่กรอก"""
    return {key: value for key, value in request.args.items() if value}


# ---------- หน้าเว็บ ----------
@app.route("/")
def home_page():
    """หน้าจัดการข้อมูล"""
    return render_template("index.html")

@app.route("/report")
def report_page():
    """หน้ารายงาน"""
    return render_template("report.html")


# ---------- ลูกค้า ----------
@app.route("/api/customers", methods=["GET"])
def customers_search():
    """ค้นหาลูกค้า"""
    return reply(db.search_customers, get_filters())

@app.route("/api/customers/<int:id>", methods=["GET"])
def customers_get(id):
    """ดึงลูกค้า 1 คน"""
    return reply(db.get_customer, id)

@app.route("/api/customers", methods=["POST"])
def customers_create():
    """เพิ่มลูกค้า"""
    return reply(db.create_customer, request.json)

@app.route("/api/customers/<int:id>", methods=["PUT"])
def customers_update(id):
    """แก้ไขลูกค้า"""
    return reply(db.update_customer, id, request.json)

@app.route("/api/customers/<int:id>", methods=["DELETE"])
def customers_delete(id):
    """ลบลูกค้า"""
    return reply(db.delete_customer, id)


# ---------- สินค้า ----------
@app.route("/api/products", methods=["GET"])
def products_search():
    """ค้นหาสินค้า"""
    return reply(db.search_products, get_filters())

@app.route("/api/products/<int:id>", methods=["GET"])
def products_get(id):
    """ดึงสินค้า 1 รายการ"""
    return reply(db.get_product, id)

@app.route("/api/products", methods=["POST"])
def products_create():
    """เพิ่มสินค้า"""
    return reply(db.create_product, request.json)

@app.route("/api/products/<int:id>", methods=["PUT"])
def products_update(id):
    """แก้ไขสินค้า"""
    return reply(db.update_product, id, request.json)

@app.route("/api/products/<int:id>", methods=["DELETE"])
def products_delete(id):
    """ลบสินค้า"""
    return reply(db.delete_product, id)


# ---------- ออเดอร์ ----------
@app.route("/api/orders", methods=["GET"])
def orders_search():
    """ค้นหาออเดอร์"""
    return reply(db.search_orders, get_filters())

@app.route("/api/orders/<int:id>", methods=["GET"])
def orders_get(id):
    """ดึงออเดอร์ 1 รายการ"""
    return reply(db.get_order, id)

@app.route("/api/orders", methods=["POST"])
def orders_create():
    """เพิ่มออเดอร์"""
    return reply(db.create_order, request.json)

@app.route("/api/orders/<int:id>", methods=["PUT"])
def orders_update(id):
    """แก้ไขออเดอร์"""
    return reply(db.update_order, id, request.json)

@app.route("/api/orders/<int:id>", methods=["DELETE"])
def orders_delete(id):
    """ลบออเดอร์"""
    return reply(db.delete_order, id)


# ---------- รายงาน ----------
@app.route("/api/reports/summary")
def reports_summary():
    """การ์ดตัวเลขสรุปบนหน้ารายงาน"""
    return reply(db.report_summary)

@app.route("/api/reports")
def reports_list():
    """รายชื่อรายงานทั้งหมด (มาจาก REPORTS ท้ายไฟล์ db.py)"""
    names = [{"key": key, "title": title} for key, title, function in db.REPORTS]
    return jsonify({"ok": True, "data": names})

@app.route("/api/reports/<key>")
def reports_run(key):
    """รันรายงานตามชื่อ เช่น /api/reports/best-selling"""
    for report_key, title, function in db.REPORTS:
        if report_key == key:
            return reply(function)
    return jsonify({"ok": False, "error": "ไม่พบรายงานนี้"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
