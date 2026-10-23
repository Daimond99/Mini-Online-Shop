from flask import Flask, request, jsonify, render_template
import db

app = Flask(__name__)
app.json.sort_keys = False


def reply(function, *args):
    try:
        data = function(*args)
        return jsonify({"ok": True, "data": data})
    except KeyError as error:
        return jsonify({"ok": False, "error": "ข้อมูลไม่ครบ: ขาด " + str(error)}), 400
    except Exception as error:
        return jsonify({"ok": False, "error": str(error)}), 400


def get_body():
    body = request.get_json(silent=True)
    if body is None:
        return {}
    return body


def get_filters():
    filters = {}
    for key in request.args:
        if request.args[key] != "":
            filters[key] = request.args[key]
    return filters


# ---------- pages ----------

@app.route("/")
def home_page():
    return render_template("index.html")


@app.route("/report")
def report_page():
    return render_template("report.html")


# ---------- customer ----------

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


# ---------- product ----------

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


# ---------- order ----------

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


# ---------- report ----------

@app.route("/api/reports/summary")
def reports_summary():
    return reply(db.report_summary)


@app.route("/api/reports/best-selling")
def reports_best_selling():
    return reply(db.report_best_selling)


@app.route("/api/reports/top-customers")
def reports_top_customers():
    return reply(db.report_customers_above_avg)


@app.route("/api/reports/high-rated")
def reports_high_rated():
    return reply(db.report_high_rated)


# ---------- top 10 ----------

@app.route("/api/rankings/products-qty")
def rankings_products_qty():
    return reply(db.ranking_products_by_quantity)


@app.route("/api/rankings/products-revenue")
def rankings_products_revenue():
    return reply(db.ranking_products_by_revenue)


@app.route("/api/rankings/customers-spend")
def rankings_customers_spend():
    return reply(db.ranking_customers_by_spending)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
