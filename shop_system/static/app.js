// app.js — หน้าจัดการข้อมูล (ลูกค้า / สินค้า / ออเดอร์)

// ---------- ตั้งค่า ----------
const LABELS = {
  regular: "ทั่วไป", silver: "ซิลเวอร์", gold: "โกลด์",
  pending: "รอชำระเงิน", paid: "ชำระแล้ว", shipped: "จัดส่งแล้ว", completed: "สำเร็จ", cancelled: "ยกเลิก",
};
const withLabels = values => values.map(value => ({ value, label: LABELS[value] }));

const TIER_OPTIONS = withLabels(["regular", "silver", "gold"]);
const STATUS_OPTIONS = withLabels(["pending", "paid", "shipped", "completed", "cancelled"]);
const CATEGORY_GROUPS = [
  { label: "ชิ้นส่วนหลัก",        options: ["ซีพียู", "เมนบอร์ด", "แรม", "การ์ดจอ", "พาวเวอร์ซัพพลาย", "เคสคอมพิวเตอร์"] },
  { label: "อุปกรณ์จัดเก็บข้อมูล", options: ["SSD", "ฮาร์ดดิสก์"] },
  { label: "อุปกรณ์เกมมิ่ง",       options: ["เมาส์เกมมิ่ง, คีย์บอร์ดเกมมิ่ง", "หูฟังเกมมิ่ง"] },
];
const CUSTOMER_OPTIONS = { api: "/api/customers", value: "cust_id", label: "name" };

const COLUMN_LABELS = {
  name: "ชื่อ", email: "อีเมล", address: "ที่อยู่", tier: "ระดับ",
  category: "หมวดหมู่", price: "ราคา (บาท)", stock: "สต็อก",
  customer_name: "ลูกค้า", order_date: "วันที่สั่ง", status: "สถานะ",
  items: "สินค้าที่สั่ง", quantity: "จำนวน (ชิ้น)",
  total: "ยอดรวม (บาท)",
};
const MONEY_COLUMNS = ["price", "total"];
const NUMBER_COLUMNS = ["price", "total", "stock", "quantity"];
const BADGE_COLUMNS = ["tier", "status"];

const ENTITIES = {
  customers: {
    label: "ลูกค้า",
    api: "/api/customers",
    idKey: "cust_id",
    nameKey: "name",
    search: [
      { key: "name",  label: "ชื่อ",  type: "text", placeholder: "พิมพ์ชื่อ..." },
      { key: "email", label: "อีเมล", type: "text", placeholder: "พิมพ์อีเมล..." },
      { key: "tier",  label: "ระดับสมาชิก", type: "chips", options: TIER_OPTIONS, wide: true },
    ],
    form: [
      { key: "name",    label: "ชื่อ",   type: "text", required: true },
      { key: "email",   label: "อีเมล",  type: "email" },
      { key: "address", label: "ที่อยู่", type: "text" },
      { key: "tier",    label: "ระดับสมาชิก", type: "chips", options: TIER_OPTIONS },
    ],
  },

  products: {
    label: "สินค้า",
    api: "/api/products",
    idKey: "product_id",
    nameKey: "name",
    search: [
      { key: "name",     label: "ชื่อสินค้า", type: "text", placeholder: "พิมพ์ชื่อสินค้า..." },
      { key: "category", label: "หมวดหมู่",  type: "select", groups: CATEGORY_GROUPS, all: true },
    ],
    form: [
      { key: "name",     label: "ชื่อสินค้า", type: "text", required: true },
      { key: "category", label: "หมวดหมู่",  type: "select", groups: CATEGORY_GROUPS,
        placeholder: "เลือกหมวดหมู่", required: true },
      { key: "price",    label: "ราคา (บาท)", type: "number", min: 0, required: true },
      { key: "stock",    label: "สต็อก",     type: "number", min: 0, integer: true, required: true },
    ],
  },

  orders: {
    label: "ออเดอร์",
    api: "/api/orders",
    idKey: "order_id",
    hide: ["cust_id"],
    search: [
      { key: "cust_id", label: "ลูกค้า", type: "select", optionsFrom: CUSTOMER_OPTIONS, all: true },
      { key: "status",  label: "สถานะ",  type: "chips", options: STATUS_OPTIONS, wide: true },
    ],
    form: [
      { key: "cust_id",    label: "ลูกค้า",    type: "select", optionsFrom: CUSTOMER_OPTIONS,
        placeholder: "เลือกลูกค้า", required: true },
      { key: "order_date", label: "วันที่สั่ง", type: "date", default: today, required: true },
      { key: "status",     label: "สถานะ",    type: "chips", options: STATUS_OPTIONS },
      { key: "amount",     label: "ยอดเงิน (บาท)", type: "number", min: 0, placeholder: "เว้นว่างถ้ายังไม่ชำระ" },
    ],
  },
};


// ---------- ตัวช่วย ----------
let currentTab = "customers";
let currentRows = [];
let editingId = null;
let searchCount = 0;
let searchTimer;
let toastTimer;

function $(selector) {
  return document.querySelector(selector);
}

function escapeHtml(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(text).replace(/[&<>"']/g, ch => map[ch]);
}

function today() {
  const date = new Date();
  date.setMinutes(date.getMinutes() - date.getTimezoneOffset());
  return date.toISOString().slice(0, 10);
}

async function callApi(url, method = "GET", body = null) {
  const options = { method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  return await response.json();
}

function toast(message, type = "ok") {
  const box = $("#toast");
  box.textContent = message;
  box.className = "toast " + type;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => box.classList.add("hidden"), 3000);
}


// ---------- ช่องกรอก ----------
function toOptions(options) {
  return options.map(option => typeof option === "object" ? option : { value: option, label: option });
}

function makeOptions(options, value) {
  return toOptions(options).map(option => {
    const selected = String(option.value) === String(value ?? "") ? "selected" : "";
    return `<option value="${escapeHtml(option.value)}" ${selected}>${escapeHtml(option.label)}</option>`;
  }).join("");
}

function makeSelect(field, id, value) {
  let html = "";
  if (field.all) html += `<option value="">ทั้งหมด</option>`;
  if (field.blank) html += `<option value="">${field.blank}</option>`;
  if (field.placeholder) html += `<option value="" disabled ${value ? "" : "selected"}>${field.placeholder}</option>`;

  if (field.groups) {
    for (const group of field.groups) {
      html += `<optgroup label="${group.label}">${makeOptions(group.options, value)}</optgroup>`;
    }
  } else {
    html += makeOptions(field.options, value);
  }
  return `<select id="${id}">${html}</select>`;
}

function makeChips(field, id, value, withAll) {
  const options = toOptions(field.options);
  if (withAll) options.unshift({ value: "", label: "ทั้งหมด" });
  const current = value ?? options[0].value;

  const chips = options.map(option => {
    const active = String(option.value) === String(current) ? "active" : "";
    return `<button type="button" class="chip ${active}" data-value="${escapeHtml(option.value)}">${escapeHtml(option.label)}</button>`;
  }).join("");
  return `<div class="chips" id="${id}" data-value="${escapeHtml(current)}">${chips}</div>`;
}

function makeInput(field, id, value) {
  let attrs = "";
  if (field.placeholder) attrs += ` placeholder="${field.placeholder}"`;
  if (field.min !== undefined) attrs += ` min="${field.min}"`;
  if (field.type === "number") attrs += ` step="${field.integer ? 1 : 0.01}"`;
  return `<input id="${id}" type="${field.type}" value="${escapeHtml(value ?? "")}"${attrs}>`;
}

function makeField(field, prefix, value) {
  const id = prefix + field.key;
  const isForm = prefix === "f_";
  const mark = field.required && isForm ? ' <span class="req">*</span>' : "";

  let input;
  if (field.type === "chips") input = makeChips(field, id, value, !isForm);
  else if (field.type === "select") input = makeSelect(field, id, value);
  else input = makeInput(field, id, value);

  return `<div class="field ${field.wide ? "wide" : ""}"><label for="${id}">${field.label}${mark}</label>${input}</div>`;
}

function getValue(id) {
  const element = $("#" + id);
  return element.classList.contains("chips") ? element.dataset.value : element.value.trim();
}

async function loadOptions(fields) {
  for (const field of fields) {
    if (!field.optionsFrom) continue;
    const source = field.optionsFrom;
    const result = await callApi(source.api);
    field.options = result.data.map(row => ({ value: row[source.value], label: row[source.label] }));
  }
}


// ---------- ค้นหา ----------
async function showSearchBox() {
  const entity = ENTITIES[currentTab];
  await loadOptions(entity.search);
  $("#searchTitle").textContent = entity.label;
  $("#searchFields").innerHTML = entity.search.map(field => makeField(field, "s_")).join("");

  for (const field of entity.search) {
    const event = field.type === "text" ? "input" : "change";
    $("#s_" + field.key).addEventListener(event, searchSoon);
  }
}

function searchSoon() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(search, 250);
}

async function search() {
  const entity = ENTITIES[currentTab];
  const params = new URLSearchParams();
  for (const field of entity.search) {
    const value = getValue("s_" + field.key);
    if (value) params.append(field.key, value);
  }

  const requestId = ++searchCount;
  showStatus("กำลังโหลด...");
  const result = await callApi(entity.api + "?" + params);
  if (requestId === searchCount) showTable(result);    // ข้ามผลของคำขอเก่า
}


// ---------- ตาราง ----------
function showStatus(message, isError = false) {
  const box = $("#status");
  box.textContent = message;
  box.className = "status" + (isError ? " err" : "") + (message ? "" : " hidden");
}

function formatCell(column, value) {
  if (value === null || value === "") return '<span class="muted">—</span>';
  if (MONEY_COLUMNS.includes(column)) {
    return Number(value).toLocaleString("th-TH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (BADGE_COLUMNS.includes(column)) {
    return `<span class="badge ${escapeHtml(value)}">${escapeHtml(LABELS[value] || value)}</span>`;
  }
  return escapeHtml(value);
}

function showTable(result) {
  const entity = ENTITIES[currentTab];
  $("#tableHead").innerHTML = "";
  $("#tableBody").innerHTML = "";
  $("#count").textContent = "";
  currentRows = [];

  if (!result.ok) return showStatus("⚠️ " + result.error, true);
  if (result.data.length === 0) return showStatus("ไม่พบข้อมูลที่ตรงกับเงื่อนไข");

  currentRows = result.data;
  showStatus("");
  $("#count").textContent = currentRows.length + " รายการ";

  const hidden = entity.hide || [];
  const columns = Object.keys(currentRows[0]).filter(column => !hidden.includes(column));
  const numClass = column => {
    if (column === "items") return "wrap";
    return NUMBER_COLUMNS.includes(column) ? "num" : "";
  };

  let head = "";
  for (const column of columns) {
    const title = column === entity.idKey ? "#" : (COLUMN_LABELS[column] || column);
    head += `<th class="${numClass(column)}">${title}</th>`;
  }
  $("#tableHead").innerHTML = head + "<th></th>";

  let body = "";
  for (const [index, row] of currentRows.entries()) {
    const id = row[entity.idKey];
    body += "<tr>";
    for (const column of columns) {
      const cell = column === entity.idKey ? index + 1 : formatCell(column, row[column]);
      body += `<td class="${numClass(column)}">${cell}</td>`;
    }
    body += `<td class="actions">
        <button class="btn sm" onclick="editRow(${id})">✏️ แก้ไข</button>
        <button class="btn sm del" onclick="deleteRow(${id})">🗑 ลบ</button>
      </td></tr>`;
  }
  $("#tableBody").innerHTML = body;
}


// ---------- ฟอร์ม ----------
async function openForm(title, data = {}) {
  const fields = ENTITIES[currentTab].form;
  await loadOptions(fields);

  $("#modalTitle").textContent = title;
  $("#formFields").innerHTML = fields.map(field => makeField(field, "f_", data[field.key])).join("");
  $("#formError").classList.add("hidden");
  $("#modal").classList.remove("hidden");
  $("#formFields input, #formFields select, #formFields .chip").focus();
}

function closeForm() {
  $("#modal").classList.add("hidden");
}

function readForm() {
  const data = {};
  for (const field of ENTITIES[currentTab].form) {
    data[field.key] = getValue("f_" + field.key);
  }
  return data;
}

function validate(fields, data) {
  for (const field of fields) {
    const value = data[field.key];
    if (field.required && value === "") return (field.type === "select" ? "กรุณาเลือก" : "กรุณากรอก") + field.label;
    if (field.type === "number" && value !== "") {
      const number = Number(value);
      if (Number.isNaN(number) || number < field.min) return `${field.label} ต้องเป็น ${field.min} หรือมากกว่า`;
      if (field.integer && !Number.isInteger(number)) return field.label + " ต้องเป็นจำนวนเต็ม";
    }
  }
  return null;
}

function showFormError(message) {
  $("#formError").textContent = "⚠️ " + message;
  $("#formError").classList.remove("hidden");
}

async function saveForm() {
  const entity = ENTITIES[currentTab];
  const data = readForm();

  const error = validate(entity.form, data);
  if (error) return showFormError(error);

  const button = $("#btnSave");
  button.disabled = true;
  button.textContent = "กำลังบันทึก...";
  const result = editingId === null
    ? await callApi(entity.api, "POST", data)
    : await callApi(entity.api + "/" + editingId, "PUT", data);
  button.disabled = false;
  button.textContent = "บันทึก";

  if (!result.ok) return showFormError(result.error);

  closeForm();
  toast(editingId === null ? "เพิ่มข้อมูลแล้ว" : "บันทึกการแก้ไขแล้ว");
  search();
}


// ---------- แก้ไข / ลบ ----------
function openAddForm() {
  const entity = ENTITIES[currentTab];
  const defaults = {};
  for (const field of entity.form) {
    if (field.default) defaults[field.key] = field.default();
  }
  editingId = null;
  openForm("เพิ่ม" + entity.label, defaults);
}

async function editRow(id) {
  const entity = ENTITIES[currentTab];
  const result = await callApi(entity.api + "/" + id);
  if (!result.ok) return toast("⚠️ " + result.error, "err");

  editingId = id;
  openForm("แก้ไข" + entity.label, result.data);
}

async function deleteRow(id) {
  const entity = ENTITIES[currentTab];
  const row = currentRows.find(r => r[entity.idKey] === id);
  const name = entity.nameKey ? row[entity.nameKey] : `${entity.label} #${id}`;
  if (!confirm(`ลบ "${name}" ใช่ไหม?`)) return;

  const result = await callApi(entity.api + "/" + id, "DELETE");
  if (!result.ok) return toast("⚠️ " + result.error, "err");

  toast(`ลบ "${name}" แล้ว`);
  search();
}


// ---------- เริ่มต้น ----------
async function switchTab(tabName) {
  currentTab = tabName;
  for (const tab of document.querySelectorAll(".tab")) {
    tab.classList.toggle("active", tab.dataset.entity === tabName);
  }
  const label = ENTITIES[tabName].label;
  $("#listTitle").textContent = "รายการ" + label;
  $("#btnAdd").textContent = "+ เพิ่ม" + label;
  await showSearchBox();
  search();
}

for (const tab of document.querySelectorAll(".tab")) {
  tab.onclick = () => switchTab(tab.dataset.entity);
}

$("#btnClear").onclick = () => showSearchBox().then(search);
$("#btnAdd").onclick = openAddForm;
$("#btnSave").onclick = saveForm;
$("#btnCancel").onclick = closeForm;

document.addEventListener("click", event => {
  const chip = event.target.closest(".chip");
  if (!chip) return;
  const group = chip.parentElement;
  group.dataset.value = chip.dataset.value;
  for (const other of group.children) other.classList.toggle("active", other === chip);
  group.dispatchEvent(new Event("change"));
});

$("#modal").addEventListener("click", event => {
  if (event.target.id === "modal") closeForm();
});
$("#modal").addEventListener("keydown", event => {
  if (event.key === "Enter" && event.target.tagName === "INPUT") saveForm();
});
document.addEventListener("keydown", event => {
  if (event.key === "Escape") closeForm();
});

switchTab("customers");
