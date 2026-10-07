// app.js — หน้าจัดการข้อมูล (ลูกค้า / สินค้า / ออเดอร์)
// ส่วนที่ 1: ตั้งค่าแท็บ  ส่วนที่ 2: ฟังก์ชัน  ส่วนที่ 3: ผูกปุ่ม
// คุยกับหลังบ้านผ่าน API ใน app.py เช่น GET /api/customers?name=สม, POST /api/customers

// ---------- 1) ตั้งค่าแต่ละแท็บ (key = ชื่อคอลัมน์ใน DB, "" ใน options = ทั้งหมด) ----------
const TIERS = ["regular", "silver", "gold"];
const STATUSES = ["pending", "paid", "shipped", "completed", "cancelled"];

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
};


// ---------- 2) ฟังก์ชัน ----------
let currentTab = "customers";
let editingId = null;             // null = กำลังเพิ่มใหม่

function $(selector) {
  return document.querySelector(selector);
}

// ส่งคำขอไปหลังบ้าน คืน {ok, data} หรือ {ok, error}
async function callApi(url, method = "GET", body = null) {
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (body) options.body = JSON.stringify(body);
  const response = await fetch(url, options);
  return await response.json();
}


// สร้างช่องกรอก 1 ช่อง (idPrefix: "s_" = ช่องค้นหา, "f_" = ฟอร์ม)
function makeFieldHtml(field, idPrefix, value = "") {
  const id = idPrefix + field.key;
  let input;

  if (field.type === "select") {
    let optionsHtml = "";
    for (const option of field.options) {
      const optionValue = typeof option === "object" ? option.value : option;
      const optionLabel = typeof option === "object" ? option.label : (option || "ทั้งหมด");
      const selected = String(optionValue) === String(value) ? "selected" : "";
      optionsHtml += `<option value="${optionValue}" ${selected}>${optionLabel}</option>`;
    }
    input = `<select id="${id}">${optionsHtml}</select>`;
  } else {
    input = `<input id="${id}" type="${field.type}" value="${value ?? ""}">`;
  }

  return `<div class="field"><label>${field.label}</label>${input}</div>`;
}

// ช่องที่มี optionsFrom: ดึงตัวเลือกจากหลังบ้าน
async function loadOptionsFromApi(fields) {
  for (const field of fields) {
    if (!field.optionsFrom) continue;
    const source = field.optionsFrom;
    const result = await callApi(source.api);
    field.options = result.data.map(row => ({ value: row[source.value], label: row[source.label] }));
  }
}

// วาดช่องค้นหาของแท็บที่เปิดอยู่
function showSearchBox() {
  const entity = ENTITIES[currentTab];
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
    const id = row[entity.idKey];
    bodyHtml += "<tr>";
    for (const column of columns) {
      bodyHtml += `<td>${row[column] ?? "—"}</td>`;     // NULL แสดงเป็น —
    }
    bodyHtml += `<td>
        <button class="btn sm" onclick="editRow(${id})">แก้ไข</button>
        <button class="btn sm del" onclick="deleteRow(${id})">ลบ</button>
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
    html += makeFieldHtml(field, "f_", data[field.key]);
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


// ---------- 3) ผูกปุ่ม ----------
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

showSearchBox();
$("#status").textContent = 'กด "ค้นหา" เพื่อแสดงข้อมูล';
