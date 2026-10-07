# ============================================================
#  app.py — เว็บแอป Flask (ทำให้เสร็จแล้ว ★ ปกติไม่ต้องแก้)
#  รัน:  python app.py  แล้วเปิด http://127.0.0.1:5000
#  ★ เพิ่มรายงานใหม่ไม่ต้องแก้ไฟล์นี้ — ไปเพิ่มที่ REPORTS ท้าย db.py
# ============================================================
from datetime import date, datetime
from flask import Flask, request, jsonify, render_template
from flask.json.provider import DefaultJSONProvider
import db


class JSONProvider(DefaultJSONProvider):
    """- ส่งวันที่เป็นรูปแบบ YYYY-MM-DD ให้ช่อง <input type="date"> ในฟอร์มอ่านได้
       - ไม่เรียงชื่อคอลัมน์ใหม่ → หัวตารางเรียงตามลำดับใน SELECT"""
    sort_keys = False

    @staticmethod
    def default(o):
        if isinstance(o, (date, datetime)):
            return o.isoformat()
        return DefaultJSONProvider.default(o)


app = Flask(__name__)
app.json = JSONProvider(app)


def safe(fn, *args, **kwargs):
    try:
        return jsonify({"ok": True, "data": fn(*args, **kwargs)})
    except NotImplementedError as e:
        return jsonify({"ok": False, "todo": True, "error": str(e)}), 501
    except ValueError as e:
        # ข้อผิดพลาดที่ db.py ตั้งใจแจ้งผู้ใช้ เช่น raise ValueError("คลาสนี้เต็มแล้ว")
        return jsonify({"ok": False, "error": str(e)}), 400
    except Exception as e:
        return jsonify({"ok": False, "error": f"{type(e).__name__}: {e}"}), 500


@app.route("/")
def page_home():
    return render_template("index.html")

@app.route("/report")
def page_report():
    return render_template("report.html")


# ---- ลูกค้า ----
@app.route("/api/customers", methods=["GET"])
def customers_list():
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_customers, filters)

@app.route("/api/customers/<int:_id>", methods=["GET"])
def customer_get(_id):
    return safe(db.get_customer, _id)

@app.route("/api/customers", methods=["POST"])
def customer_create():
    return safe(db.create_customer, request.json)

@app.route("/api/customers/<int:_id>", methods=["PUT"])
def customer_update(_id):
    return safe(db.update_customer, _id, request.json)

@app.route("/api/customers/<int:_id>", methods=["DELETE"])
def customer_delete(_id):
    return safe(db.delete_customer, _id)

# ---- สินค้า ----
@app.route("/api/products", methods=["GET"])
def products_list():
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_products, filters)

@app.route("/api/products/<int:_id>", methods=["GET"])
def product_get(_id):
    return safe(db.get_product, _id)

@app.route("/api/products", methods=["POST"])
def product_create():
    return safe(db.create_product, request.json)

@app.route("/api/products/<int:_id>", methods=["PUT"])
def product_update(_id):
    return safe(db.update_product, _id, request.json)

@app.route("/api/products/<int:_id>", methods=["DELETE"])
def product_delete(_id):
    return safe(db.delete_product, _id)

# ---- ออเดอร์ ----
@app.route("/api/orders", methods=["GET"])
def orders_list():
    filters = {k: v for k, v in request.args.items() if v}
    return safe(db.search_orders, filters)

@app.route("/api/orders/<int:_id>", methods=["GET"])
def order_get(_id):
    return safe(db.get_order, _id)

@app.route("/api/orders", methods=["POST"])
def order_create():
    return safe(db.create_order, request.json)

@app.route("/api/orders/<int:_id>", methods=["PUT"])
def order_update(_id):
    return safe(db.update_order, _id, request.json)

@app.route("/api/orders/<int:_id>", methods=["DELETE"])
def order_delete(_id):
    return safe(db.delete_order, _id)


# ---- รายงาน ----
@app.route("/api/reports/summary")
def report_summary():
    return safe(db.report_summary)

@app.route("/api/reports")
def report_list():
    """รายชื่อรายงานทั้งหมด (อ่านจาก db.REPORTS) ให้หน้าเว็บสร้างกล่องรายงาน"""
    return jsonify({"ok": True, "data": [{"key": k, "title": t} for k, t, _ in db.REPORTS]})

@app.route("/api/reports/<key>")
def report_run(key):
    """รันรายงานตามชื่อ เช่น /api/reports/overdue"""
    for k, _, fn in db.REPORTS:
        if k == key:
            return safe(fn)
    return jsonify({"ok": False, "error": f"ไม่พบรายงาน '{key}' ใน db.REPORTS"}), 404


if __name__ == "__main__":
    app.run(debug=True, port=5000)
