# app.py — รับคำขอจากหน้าเว็บ แล้วส่งต่อให้ db.py (ไฟล์นี้ไม่มี SQL)
# รัน: python app.py แล้วเปิด http://127.0.0.1:5000

from flask import Flask, request, jsonify, render_template
import db

app = Flask(__name__)
app.json.sort_keys = False      # หัวตารางเรียงตามลำดับใน SELECT


def reply(function, *args):
    """เรียกฟังก์ชันใน db.py แล้วตอบหน้าเว็บเป็น JSON
    สำเร็จ -> {"ok": true, "data": ...}   ผิดพลาด -> {"ok": false, "error": "ข้อความ"}"""
    try:
        return jsonify({"ok": True, "data": function(*args)})
    except KeyError as error:
        return jsonify({"ok": False, "error": f"ข้อมูลไม่ครบ: ขาด {error}"}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 400


def get_body():
    """อ่านข้อมูลที่หน้าเว็บส่งมา (JSON) ถ้าส่งมาผิดรูปแบบจะได้ dict ว่าง"""
    return request.get_json(silent=True) or {}


def get_filters():
    """อ่านเงื่อนไขค้นหาจาก URL เช่น ?name=สม&tier=gold (เอาเฉพาะช่องที่กรอก)"""
    return {key: value for key, value in request.args.items() if value}


# ============================================================
# หน้าเว็บ
# ============================================================

@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/report")
def report_page():
    return render_template("report.html")


# ============================================================
# ลูกค้า   GET = ค้นหา/ดึง   POST = เพิ่ม   PUT = แก้ไข   DELETE = ลบ
# ============================================================

@app.route("/api/customers", methods=["GET"])
def customers_search():
    return reply(db.search_customers, get_filters())


@app.route("/api/customers/<int:cust_id>", methods=["GET"])
def customers_get(cust_id):
    return reply(db.get_customer, cust_id)


@app.route("/api/customers", methods=["POST"])
def customers_create():
    return reply(db.create_customer, get_body())


@app.route("/api/customers/<int:cust_id>", methods=["PUT"])
def customers_update(cust_id):
    return reply(db.update_customer, cust_id, get_body())


@app.route("/api/customers/<int:cust_id>", methods=["DELETE"])
def customers_delete(cust_id):
    return reply(db.delete_customer, cust_id)


# ============================================================
# สินค้า
# ============================================================

@app.route("/api/products", methods=["GET"])
def products_search():
    return reply(db.search_products, get_filters())


@app.route("/api/products/<int:product_id>", methods=["GET"])
def products_get(product_id):
    return reply(db.get_product, product_id)


@app.route("/api/products", methods=["POST"])
def products_create():
    return reply(db.create_product, get_body())


@app.route("/api/products/<int:product_id>", methods=["PUT"])
def products_update(product_id):
    return reply(db.update_product, product_id, get_body())


@app.route("/api/products/<int:product_id>", methods=["DELETE"])
def products_delete(product_id):
    return reply(db.delete_product, product_id)


# ============================================================
# ออเดอร์
# ============================================================

@app.route("/api/orders", methods=["GET"])
def orders_search():
    return reply(db.search_orders, get_filters())


@app.route("/api/orders/<int:order_id>", methods=["GET"])
def orders_get(order_id):
    return reply(db.get_order, order_id)


@app.route("/api/orders", methods=["POST"])
def orders_create():
    return reply(db.create_order, get_body())


@app.route("/api/orders/<int:order_id>", methods=["PUT"])
def orders_update(order_id):
    return reply(db.update_order, order_id, get_body())


@app.route("/api/orders/<int:order_id>", methods=["DELETE"])
def orders_delete(order_id):
    return reply(db.delete_order, order_id)


# ============================================================
# รายงาน
# ============================================================

@app.route("/api/reports/summary")
def reports_summary():
    return reply(db.report_summary)


@app.route("/api/reports")
def reports_list():
    """รายชื่อรายงานทั้งหมด (มาจาก REPORTS ท้าย db.py)"""
    names = [{"key": key, "title": title} for key, title, function in db.REPORTS]
    return jsonify({"ok": True, "data": names})


@app.route("/api/reports/<key>")
def reports_run(key):
    """รันรายงานตาม key เช่น /api/reports/best-selling"""
    for report_key, title, function in db.REPORTS:
        if report_key == key:
            return reply(function)
    return jsonify({"ok": False, "error": "ไม่พบรายงานนี้"}), 404


# ============================================================
# จัดอันดับ Top 10 (ฟีเจอร์พิเศษ)
# ============================================================

@app.route("/api/rankings")
def rankings_list():
    names = [{"key": key, "title": title} for key, title, function in db.RANKINGS]
    return jsonify({"ok": True, "data": names})


@app.route("/api/rankings/<key>")
def rankings_run(key):
    for ranking_key, title, function in db.RANKINGS:
        if ranking_key == key:
            return reply(function)
    return jsonify({"ok": False, "error": "ไม่พบการจัดอันดับนี้"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
