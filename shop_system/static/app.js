// app.js — หน้าจัดการข้อมูล (ลูกค้า / สินค้า / ออเดอร์)
// ส่วนที่ 1: ตั้งค่าแท็บ  ส่วนที่ 2: ฟังก์ชัน  ส่วนที่ 3: หน้าต่างจัดการออเดอร์ (สินค้า + ชำระเงิน)  ส่วนที่ 4: ผูกปุ่ม
// คุยกับหลังบ้านผ่าน API ใน app.py เช่น GET /api/customers?name=สม, POST /api/customers

// ---------- 1) ตั้งค่าแต่ละแท็บ (key = ชื่อคอลัมน์ใน DB, "" ใน options = ทั้งหมด) ----------
const TIERS = ["regular", "silver", "gold"];
const STATUSES = ["pending", "paid", "shipped", "completed", "cancelled"];
const RATINGS = [1, 2, 3, 4, 5];

const ENTITIES = {
  customers: {
    label: "ลูกค้า",
    api: "/api/customers",
    idKey: "cust_id",
    search: [
      { key: "name",  label: "ชื่อ",   type: "text" },
      { key: "email", label: "อีเมล",  type: "text" },
      { key: "tier",  label: "ระดับ",  type: "select", options: ["", ...TIERS] },
    ],
    form: [
      { key: "name",    label: "ชื่อ",    type: "text" },
      { key: "email",   label: "อีเมล",   type: "text" },
      { key: "address", label: "ที่อยู่",  type: "text" },
      { key: "tier",    label: "ระดับ",   type: "select", options: TIERS },
    ],
  },

  products: {
    label: "สินค้า",
    api: "/api/products",
    idKey: "product_id",
    search: [
      { key: "name",     label: "ชื่อสินค้า", type: "text" },
      { key: "category", label: "หมวดหมู่",  type: "text" },
    ],
    form: [
      { key: "name",     label: "ชื่อสินค้า", type: "text" },
      { key: "category", label: "หมวดหมู่",  type: "text" },
      { key: "price",    label: "ราคา",      type: "number" },
      { key: "stock",    label: "สต็อก",     type: "number" },
    ],
  },

  orders: {
    label: "ออเดอร์",
    api: "/api/orders",
    idKey: "order_id",
    search: [
      { key: "cust_id", label: "รหัสลูกค้า", type: "number" },
      { key: "status",  label: "สถานะ",     type: "select", options: ["", ...STATUSES] },
    ],
    form: [
      // dropdown ลูกค้า: ดึงรายชื่อจาก /api/customers แสดง name ส่งค่า cust_id
      { key: "cust_id",    label: "ลูกค้า",   type: "select",
        optionsFrom: { api: "/api/customers", value: "cust_id", label: "name" } },
      { key: "order_date", label: "วันที่สั่ง", type: "date" },
      { key: "status",     label: "สถานะ",    type: "select", options: STATUSES },
    ],
  },

  // รีวิว: คีย์ = cust_id + product_id (idKeys) · lockOnEdit = ตอนแก้ไขเปลี่ยนไม่ได้
  reviews: {
    label: "รีวิว",
    api: "/api/reviews",
    idKeys: ["cust_id", "product_id"],
    search: [
      { key: "cust_id",    label: "ลูกค้า",  type: "select", includeAll: true,
        optionsFrom: { api: "/api/customers", value: "cust_id", label: "name" } },
      { key: "product_id", label: "สินค้า",  type: "select", includeAll: true,
        optionsFrom: { api: "/api/products", value: "product_id", label: "name" } },
      { key: "rating",     label: "คะแนน",  type: "select", options: ["", ...RATINGS] },
    ],
    form: [
      { key: "cust_id",     label: "ลูกค้า", type: "select", lockOnEdit: true,
        optionsFrom: { api: "/api/customers", value: "cust_id", label: "name" } },
      { key: "product_id",  label: "สินค้า", type: "select", lockOnEdit: true,
        optionsFrom: { api: "/api/products", value: "product_id", label: "name" } },
      { key: "rating",      label: "คะแนน (1-5)", type: "select", options: RATINGS },
      { key: "comment",     label: "ความเห็น", type: "text" },
      { key: "review_date", label: "วันที่รีวิว", type: "date" },
    ],
  },
};

// วิธีชำระเงิน: ค่าที่เก็บใน DB -> คำอ่านภาษาไทย
const PAYMENT_METHODS = [
  { value: "cash",        label: "เงินสด" },
  { value: "credit_card", label: "บัตรเครดิต" },
  { value: "transfer",    label: "โอนเงิน" },
  { value: "promptpay",   label: "พร้อมเพย์" },
];


// ---------- 2) ฟังก์ชัน ----------
let currentTab = "customers";
let editingId = null;             // null = กำลังเพิ่มใหม่

function $(selector) {
  return document.querySelector(selector);
}

// วันนี้ในรูป YYYY-MM-DD (ใช้เป็นค่าเริ่มต้นของช่องวันที่)
function todayText() {
  return new Date().toLocaleDateString("sv-SE");
}

// กันข้อความจากฐานข้อมูลปนเป็น HTML (ใช้กับโค้ดส่วนหน้าต่างจัดการออเดอร์)
function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
}

// คีย์ของแถวเป็นข้อความสำหรับใส่ใน URL เช่น "3" หรือ "1/2" (คีย์ร่วม)
function rowPath(entity, row) {
  return (entity.idKeys || [entity.idKey]).map(key => row[key]).join("/");
}

// ส่งคำขอไปหลังบ้าน คืน {ok, data} หรือ {ok, error}
async function callApi(url, method = "GET", body = null) {
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  return await response.json();
}


// สร้างช่องกรอก 1 ช่อง (idPrefix: "s_" = ช่องค้นหา, "f_" = ฟอร์ม)
function makeFieldHtml(field, idPrefix, value = "", disabled = false) {
  const id = idPrefix + field.key;
  const lock = disabled ? "disabled" : "";
  let input;

  if (field.type === "select") {
    let optionsHtml = "";
    for (const option of field.options) {
      const optionValue = typeof option === "object" ? option.value : option;
      const optionLabel = typeof option === "object" ? option.label : (option || "ทั้งหมด");
      const selected = String(optionValue) === String(value) ? "selected" : "";
      optionsHtml += `<option value="${optionValue}" ${selected}>${optionLabel}</option>`;
    }
    input = `<select id="${id}" ${lock}>${optionsHtml}</select>`;
  } else {
    input = `<input id="${id}" type="${field.type}" value="${value ?? ""}" ${lock}>`;
  }

  return `<div class="field"><label>${field.label}</label>${input}</div>`;
}

// ช่องที่มี optionsFrom: ดึงตัวเลือกจากหลังบ้าน
async function loadOptionsFromApi(fields) {
  for (const field of fields) {
    if (!field.optionsFrom) continue;
    const source = field.optionsFrom;
    const result = await callApi(source.api);
    const options = result.ok ? result.data.map(row => ({ value: row[source.value], label: row[source.label] })) : [];
    field.options = field.includeAll ? [{ value: "", label: "ทั้งหมด" }, ...options] : options;
  }
}

// วาดช่องค้นหาของแท็บที่เปิดอยู่
async function showSearchBox() {
  const entity = ENTITIES[currentTab];
  await loadOptionsFromApi(entity.search);
  let html = "";
  for (const field of entity.search) {
    html += makeFieldHtml(field, "s_");
  }
  $("#searchTitle").textContent = entity.label;
  $("#searchFields").innerHTML = html;
}


// อ่านค่าจากช่องค้นหา ส่งไปหลังบ้าน แล้วแสดงผลเป็นตาราง
async function search() {
  const entity = ENTITIES[currentTab];

  // รวมค่าช่องที่กรอกเป็น ?name=สม&tier=gold
  const params = new URLSearchParams();
  for (const field of entity.search) {
    const value = $("#s_" + field.key).value;
    if (value) params.append(field.key, value);
  }

  $("#status").textContent = "กำลังค้นหา...";
  const result = await callApi(entity.api + "?" + params.toString());
  showTable(result);
}

// วาดตารางผลลัพธ์ พร้อมปุ่มแก้ไข/ลบของแต่ละแถว
function showTable(result) {
  const entity = ENTITIES[currentTab];
  $("#tableHead").innerHTML = "";
  $("#tableBody").innerHTML = "";

  if (!result.ok) {
    $("#status").className = "status err";
    $("#status").textContent = "⚠️ " + result.error;
    return;
  }
  $("#status").className = "status";

  const rows = result.data;
  if (rows.length === 0) {
    $("#status").textContent = "ไม่พบข้อมูล";
    return;
  }
  $("#status").textContent = "พบ " + rows.length + " รายการ";

  const columns = Object.keys(rows[0]);
  let headHtml = "";
  for (const column of columns) {
    headHtml += `<th>${column}</th>`;
  }
  $("#tableHead").innerHTML = headHtml + "<th>จัดการ</th>";

  let bodyHtml = "";
  for (const row of rows) {
    const id = rowPath(entity, row);
    // ปุ่มพิเศษ: ลูกค้า -> สั่งซื้อ (เปิดหน้าต่างเลือกสินค้า) · ออเดอร์ -> สินค้า/ชำระเงิน
    let extraButton = "";
    if (currentTab === "customers") extraButton = `<button class="btn sm add" onclick="newOrderFor(${id})">สั่งซื้อ</button>`;
    if (currentTab === "orders") extraButton = `<button class="btn sm primary" onclick="openOrderModal(${id})">สินค้า/ชำระเงิน</button>`;
    bodyHtml += "<tr>";
    for (const column of columns) {
      bodyHtml += `<td>${row[column] ?? "—"}</td>`;     // NULL แสดงเป็น —
    }
    bodyHtml += `<td>
        ${extraButton}
        <button class="btn sm" onclick="editRow('${id}')">แก้ไข</button>
        <button class="btn sm del" onclick="deleteRow('${id}')">ลบ</button>
      </td></tr>`;
  }
  $("#tableBody").innerHTML = bodyHtml;
}


// เปิดฟอร์ม (ตอนแก้ไขจะใส่ค่าเดิมลงในช่อง)
async function openForm(title, data = {}) {
  const fields = ENTITIES[currentTab].form;
  await loadOptionsFromApi(fields);

  let html = "";
  for (const field of fields) {
    // เพิ่มใหม่: ช่องวันที่เริ่มต้นเป็นวันนี้ · แก้ไข: ช่องที่เป็นคีย์ (lockOnEdit) แก้ไม่ได้
    const value = data[field.key] ?? (field.type === "date" ? todayText() : "");
    html += makeFieldHtml(field, "f_", value, editingId !== null && field.lockOnEdit);
  }
  $("#modalTitle").textContent = title;
  $("#formFields").innerHTML = html;
  $("#modal").classList.remove("hidden");
}

// อ่านค่าทุกช่องในฟอร์มเป็นข้อมูลก้อนเดียว เช่น {name: "...", tier: "..."}
function readForm() {
  const data = {};
  for (const field of ENTITIES[currentTab].form) {
    data[field.key] = $("#f_" + field.key).value;
  }
  return data;
}

// กดบันทึก: เพิ่มใหม่ (POST) หรือแก้ไข (PUT) แล้วโหลดตารางใหม่
async function saveForm() {
  const entity = ENTITIES[currentTab];
  const data = readForm();

  let result;
  if (editingId === null) {
    result = await callApi(entity.api, "POST", data);
  } else {
    result = await callApi(entity.api + "/" + editingId, "PUT", data);
  }

  if (!result.ok) {
    alert("⚠️ " + result.error);
    return;
  }
  $("#modal").classList.add("hidden");
  search();
}

// กดแก้ไข: ดึงข้อมูลเดิมของแถวนั้นมาเปิดฟอร์ม
async function editRow(id) {
  const entity = ENTITIES[currentTab];
  const result = await callApi(entity.api + "/" + id);
  if (!result.ok) {
    alert("⚠️ " + result.error);
    return;
  }
  editingId = id;
  openForm("แก้ไขข้อมูล", result.data);
}

// กดลบ: ถามยืนยันก่อน แล้วลบ
async function deleteRow(id) {
  if (!confirm("ยืนยันการลบ?")) return;

  const result = await callApi(ENTITIES[currentTab].api + "/" + id, "DELETE");
  if (!result.ok) {
    alert("⚠️ " + result.error);
    return;
  }
  search();
}


// ---------- 3) หน้าต่างจัดการออเดอร์: เพิ่ม/แก้/ลบสินค้าในออเดอร์ + บันทึกการชำระเงิน ----------
// orderCtx.orderId = null หมายถึงออเดอร์ใหม่ที่ยังไม่ถูกสร้าง (จะสร้างตอนกด "เพิ่ม" สินค้าชิ้นแรก)
let orderCtx = null;

// กดปุ่ม "สั่งซื้อ" ที่แถวลูกค้า: เปิดหน้าต่างออเดอร์ใหม่ของลูกค้าคนนั้น
async function newOrderFor(custId) {
  const result = await callApi("/api/customers/" + custId);
  if (!result.ok || !result.data) {
    alert("⚠️ " + (result.error || "ไม่พบลูกค้า"));
    return;
  }
  orderCtx = { orderId: null, custId: custId, custName: result.data.name };
  await drawOrderModal();
  $("#orderModal").classList.remove("hidden");
}

// กดปุ่ม "สินค้า/ชำระเงิน" ที่แถวออเดอร์
async function openOrderModal(orderId) {
  orderCtx = { orderId: orderId };
  if (await drawOrderModal()) $("#orderModal").classList.remove("hidden");
}

function closeOrderModal() {
  $("#orderModal").classList.add("hidden");
  if (currentTab === "orders") search();      // ยอดรวม/สถานะในตารางจะได้เป็นปัจจุบัน
}

// วาดหน้าต่างใหม่จากข้อมูลล่าสุดในฐานข้อมูล (คืน false ถ้าโหลดไม่ได้)
async function drawOrderModal() {
  const products = await callApi("/api/products");
  let detail = { order: { status: "pending" }, lines: [], total: 0, payment: null };

  if (orderCtx.orderId !== null) {
    const result = await callApi(`/api/orders/${orderCtx.orderId}/detail`);
    if (!result.ok) {
      alert("⚠️ " + result.error);
      return false;
    }
    detail = result.data;
    orderCtx.custId = detail.order.cust_id;
    orderCtx.custName = detail.order.customer_name;
  }

  const status = detail.order.status;
  const locked = detail.payment !== null || status === "cancelled";   // จ่ายแล้ว/ยกเลิก = แก้รายการสินค้าไม่ได้

  $("#orderTitle").textContent = orderCtx.orderId === null
    ? `ออเดอร์ใหม่ของ ${orderCtx.custName}`
    : `ออเดอร์ #${orderCtx.orderId} — ${orderCtx.custName} (${status})`;

  // รายการสินค้าในออเดอร์
  let linesHtml = "";
  for (const line of detail.lines) {
    const qtyCell = locked
      ? esc(line.qty)
      : `<input id="qty_${line.product_id}" type="number" min="1" value="${esc(line.qty)}" class="qty-input">`;
    const buttons = locked ? "" : `
        <button class="btn sm" onclick="saveLineQty(${line.product_id})">บันทึก</button>
        <button class="btn sm del" onclick="deleteLine(${line.product_id})">เอาออก</button>`;
    linesHtml += `<tr><td>${esc(line.product_name)}</td><td>${qtyCell}</td>
        <td>${esc(line.unit_price)}</td><td>${esc(line.subtotal)}</td><td>${buttons}</td></tr>`;
  }
  if (detail.lines.length === 0) {
    linesHtml = `<tr><td colspan="5" class="status">ยังไม่มีสินค้าในออเดอร์</td></tr>`;
  }

  // แถวเพิ่มสินค้า: dropdown สินค้า + จำนวน
  let addHtml = "";
  if (!locked) {
    let optionsHtml = "";
    for (const product of products.ok ? products.data : []) {
      optionsHtml += `<option value="${product.product_id}">${esc(product.name)} — ${esc(product.price)} บาท (เหลือ ${esc(product.stock)})</option>`;
    }
    addHtml = `<div class="inline-form">
        <select id="ol_product">${optionsHtml}</select>
        <input id="ol_qty" type="number" min="1" value="1" class="qty-input">
        <button class="btn add" onclick="addLine()">+ เพิ่มสินค้า</button>
      </div>`;
  } else {
    addHtml = `<div class="status">${status === "cancelled" ? "ออเดอร์นี้ถูกยกเลิกแล้ว" : "ชำระเงินแล้ว แก้ไขรายการสินค้าไม่ได้ (ถ้าจะแก้ ให้ยกเลิกการชำระเงินก่อน)"}</div>`;
  }

  // ส่วนชำระเงิน: แสดงเมื่อมีสินค้าแล้ว และออเดอร์ไม่ถูกยกเลิก
  let paymentHtml = "";
  if (detail.lines.length > 0 && status !== "cancelled") {
    const payment = detail.payment;
    let methodOptions = "";
    for (const method of PAYMENT_METHODS) {
      const selected = payment && payment.method === method.value ? "selected" : "";
      methodOptions += `<option value="${method.value}" ${selected}>${method.label}</option>`;
    }
    paymentHtml = `
      <h4 class="sub-title">การชำระเงิน ${payment ? "(ชำระแล้ว)" : "(ยังไม่ชำระ)"}</h4>
      <div class="inline-form">
        <select id="pay_method">${methodOptions}</select>
        <input id="pay_amount" type="number" step="0.01" min="0" value="${esc(payment ? payment.amount : detail.total)}">
        <input id="pay_date" type="date" value="${esc(payment ? payment.paid_date : todayText())}">
        <button class="btn primary" onclick="savePayment(${payment ? "true" : "false"})">${payment ? "บันทึกการแก้ไข" : "บันทึกการชำระเงิน"}</button>
        ${payment ? `<button class="btn del" onclick="deletePayment()">ยกเลิกการชำระเงิน</button>` : ""}
      </div>`;
  }

  $("#orderBody").innerHTML = `
    <div class="table-wrap"><table class="line-table">
      <thead><tr><th>สินค้า</th><th>จำนวน</th><th>ราคา/ชิ้น</th><th>รวม</th><th></th></tr></thead>
      <tbody>${linesHtml}</tbody>
    </table></div>
    <div class="total-row">ยอดรวม: <b>${esc(detail.total)}</b> บาท</div>
    ${addHtml}
    ${paymentHtml}`;
  return true;
}

// ทุกปุ่มด้านล่าง: เรียก API -> ถ้า error แจ้งผู้ใช้ -> วาดหน้าต่างใหม่
async function runOrderAction(url, method, body) {
  const result = await callApi(url, method, body);
  if (!result.ok) alert("⚠️ " + result.error);
  await drawOrderModal();
  return result;
}

async function addLine() {
  // ออเดอร์ใหม่: สร้างออเดอร์ (pending, วันนี้) ก่อน แล้วค่อยเพิ่มสินค้า
  if (orderCtx.orderId === null) {
    const created = await callApi("/api/orders", "POST",
      { cust_id: orderCtx.custId, order_date: todayText(), status: "pending" });
    if (!created.ok) {
      alert("⚠️ " + created.error);
      return;
    }
    orderCtx.orderId = created.data.new_id;
  }
  await runOrderAction(`/api/orders/${orderCtx.orderId}/lines`, "POST",
    { product_id: $("#ol_product").value, qty: $("#ol_qty").value });
}

function saveLineQty(productId) {
  return runOrderAction(`/api/orders/${orderCtx.orderId}/lines/${productId}`, "PUT",
    { qty: $("#qty_" + productId).value });
}

function deleteLine(productId) {
  return runOrderAction(`/api/orders/${orderCtx.orderId}/lines/${productId}`, "DELETE");
}

function savePayment(alreadyPaid) {
  return runOrderAction(`/api/orders/${orderCtx.orderId}/payment`, alreadyPaid ? "PUT" : "POST",
    { method: $("#pay_method").value, amount: $("#pay_amount").value, paid_date: $("#pay_date").value });
}

function deletePayment() {
  if (!confirm("ยืนยันการยกเลิกการชำระเงิน?")) return;
  return runOrderAction(`/api/orders/${orderCtx.orderId}/payment`, "DELETE");
}


// ---------- 4) ผูกปุ่ม ----------
for (const tab of document.querySelectorAll(".tab")) {
  tab.onclick = function () {
    for (const other of document.querySelectorAll(".tab")) other.classList.remove("active");
    tab.classList.add("active");
    currentTab = tab.dataset.entity;
    showSearchBox();
    $("#tableHead").innerHTML = "";
    $("#tableBody").innerHTML = "";
    $("#status").textContent = 'กด "ค้นหา" เพื่อแสดงข้อมูล';
  };
}

$("#btnSearch").onclick = search;
$("#btnClear").onclick = showSearchBox;
$("#btnAdd").onclick = function () { editingId = null; openForm("เพิ่มข้อมูลใหม่"); };
$("#btnSave").onclick = saveForm;
$("#btnCancel").onclick = function () { $("#modal").classList.add("hidden"); };
$("#btnOrderClose").onclick = closeOrderModal;

showSearchBox();
$("#status").textContent = 'กด "ค้นหา" เพื่อแสดงข้อมูล';
