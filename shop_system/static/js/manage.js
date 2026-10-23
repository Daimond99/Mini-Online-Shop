// ---------- ตั้งค่า ----------

const THAI_NAMES = {
  regular: "ทั่วไป",
  silver: "ซิลเวอร์",
  gold: "โกลด์",
  vip: "วีไอพี",
  pending: "รอชำระเงิน",
  paid: "ชำระแล้ว",
  shipped: "จัดส่งแล้ว",
  completed: "สำเร็จ",
  cancelled: "ยกเลิก"
};

const TIER_OPTIONS = [
  { value: "regular", label: "ทั่วไป" },
  { value: "silver", label: "ซิลเวอร์" },
  { value: "gold", label: "โกลด์" },
  { value: "vip", label: "วีไอพี" }
];

const STATUS_OPTIONS = [
  { value: "pending", label: "รอชำระเงิน" },
  { value: "paid", label: "ชำระแล้ว" },
  { value: "shipped", label: "จัดส่งแล้ว" },
  { value: "completed", label: "สำเร็จ" },
  { value: "cancelled", label: "ยกเลิก" }
];

const CATEGORY_GROUPS = [
  { label: "ชิ้นส่วนหลัก", options: ["ซีพียู", "เมนบอร์ด", "แรม", "การ์ดจอ", "พาวเวอร์ซัพพลาย", "เคสคอมพิวเตอร์"] },
  { label: "อุปกรณ์จัดเก็บข้อมูล", options: ["SSD", "ฮาร์ดดิสก์"] },
  { label: "อุปกรณ์เกมมิ่ง", options: ["เมาส์เกมมิ่ง, คีย์บอร์ดเกมมิ่ง", "หูฟังเกมมิ่ง"] }
];

const COLUMN_NAMES = {
  name: "ชื่อ",
  email: "อีเมล",
  address: "ที่อยู่",
  tier: "ระดับ",
  total_spent: "ยอดซื้อสะสม (บาท)",
  category: "หมวดหมู่",
  price: "ราคา (บาท)",
  stock: "สต็อก",
  customer_name: "ลูกค้า",
  order_date: "วันที่สั่ง",
  status: "สถานะ",
  items: "สินค้าที่สั่ง",
  quantity: "จำนวน (ชิ้น)",
  total: "ยอดรวม (บาท)"
};

const MONEY_COLUMNS = ["price", "total", "total_spent"];
const NUMBER_COLUMNS = ["price", "total", "total_spent", "stock", "quantity"];
const BADGE_COLUMNS = ["tier", "status"];

// แต่ละแท็บ: ช่องค้นหา (search) และช่องในฟอร์ม (form)
const TABS = {
  customers: {
    label: "ลูกค้า",
    api: "/api/customers",
    idColumn: "cust_id",
    nameColumn: "name",
    hideColumns: [],
    search: [
      { key: "name", label: "ชื่อ", type: "text", placeholder: "พิมพ์ชื่อ..." },
      { key: "email", label: "อีเมล", type: "text", placeholder: "พิมพ์อีเมล..." },
      { key: "tier", label: "ระดับสมาชิก", type: "chips", options: TIER_OPTIONS, wide: true }
    ],
    form: [
      { key: "name", label: "ชื่อ", type: "text", required: true },
      { key: "email", label: "อีเมล", type: "email" },
      { key: "address", label: "ที่อยู่", type: "text" },
      { key: "tier", label: "ระดับสมาชิก", type: "chips", options: TIER_OPTIONS }
    ]
  },

  products: {
    label: "สินค้า",
    api: "/api/products",
    idColumn: "product_id",
    nameColumn: "name",
    hideColumns: [],
    search: [
      { key: "name", label: "ชื่อสินค้า", type: "text", placeholder: "พิมพ์ชื่อสินค้า..." },
      { key: "category", label: "หมวดหมู่", type: "select", groups: CATEGORY_GROUPS, showAll: true }
    ],
    form: [
      { key: "name", label: "ชื่อสินค้า", type: "text", required: true },
      { key: "category", label: "หมวดหมู่", type: "select", groups: CATEGORY_GROUPS, placeholder: "เลือกหมวดหมู่", required: true },
      { key: "price", label: "ราคา (บาท)", type: "number", min: 0, required: true },
      { key: "stock", label: "สต็อก", type: "number", min: 0, wholeNumber: true, required: true }
    ]
  },

  orders: {
    label: "ออเดอร์",
    api: "/api/orders",
    idColumn: "order_id",
    nameColumn: "",
    hideColumns: ["cust_id"],
    search: [
      { key: "cust_id", label: "ลูกค้า", type: "select", customerList: true, showAll: true },
      { key: "status", label: "สถานะ", type: "chips", options: STATUS_OPTIONS, wide: true }
    ],
    form: [
      { key: "cust_id", label: "ลูกค้า", type: "select", customerList: true, placeholder: "เลือกลูกค้า", required: true },
      { key: "order_date", label: "วันที่สั่ง", type: "date", todayByDefault: true, required: true },
      { key: "status", label: "สถานะ", type: "chips", options: STATUS_OPTIONS },
      { key: "amount", label: "ยอดเงิน (บาท)", type: "number", min: 0, placeholder: "เว้นว่างถ้ายังไม่ชำระ" }
    ]
  }
};


// ---------- ตัวแปรของหน้า ----------

let currentTab = "customers";
let currentRows = [];
let editingId = null;
let searchNumber = 0;
let searchTimer = null;
let toastTimer = null;


// ---------- ตัวช่วยทั่วไป ----------

function safe(text) {
  return String(text)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function today() {
  const date = new Date();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return year + "-" + month + "-" + day;
}

async function callApi(url, method, body) {
  if (method === undefined) {
    method = "GET";
  }
  const options = { method: method, headers: { "Content-Type": "application/json" } };
  if (body !== undefined) {
    options.body = JSON.stringify(body);
  }
  const response = await fetch(url, options);
  return await response.json();
}

function showToast(message, isError) {
  const box = document.getElementById("toast");
  box.textContent = message;
  if (isError) {
    box.className = "toast err";
  } else {
    box.className = "toast ok";
  }
  clearTimeout(toastTimer);
  toastTimer = setTimeout(function () {
    box.classList.add("hidden");
  }, 3000);
}


// ---------- สร้างช่องกรอก ----------

async function loadCustomerList(fields) {
  for (const field of fields) {
    if (field.customerList) {
      const result = await callApi("/api/customers");
      field.options = [];
      for (const customer of result.data) {
        field.options.push({ value: customer.cust_id, label: customer.name });
      }
    }
  }
}

function makeOptionTags(options, selectedValue) {
  let html = "";
  for (const option of options) {
    let value = option;
    let label = option;
    if (typeof option === "object") {
      value = option.value;
      label = option.label;
    }

    let selected = "";
    if (String(value) === String(selectedValue)) {
      selected = " selected";
    }
    html += "<option value='" + safe(value) + "'" + selected + ">" + safe(label) + "</option>";
  }
  return html;
}

function makeSelect(field, id, value) {
  let html = "<select id='" + id + "'>";

  if (field.showAll) {
    html += "<option value=''>ทั้งหมด</option>";
  }
  if (field.placeholder) {
    let selected = "";
    if (!value) {
      selected = " selected";
    }
    html += "<option value='' disabled" + selected + ">" + field.placeholder + "</option>";
  }

  if (field.groups) {
    for (const group of field.groups) {
      html += "<optgroup label='" + group.label + "'>";
      html += makeOptionTags(group.options, value);
      html += "</optgroup>";
    }
  } else {
    html += makeOptionTags(field.options, value);
  }

  html += "</select>";
  return html;
}

function makeChips(field, id, value, showAll) {
  let options = field.options;
  if (showAll) {
    options = [{ value: "", label: "ทั้งหมด" }].concat(field.options);
  }
  if (value === undefined || value === null) {
    value = options[0].value;
  }

  let html = "<div class='chips' id='" + id + "' data-value='" + safe(value) + "'>";
  for (const option of options) {
    let active = "";
    if (option.value === value) {
      active = " active";
    }
    html += "<button type='button' class='chip" + active + "' data-value='" + safe(option.value) + "'>" + option.label + "</button>";
  }
  html += "</div>";
  return html;
}

function makeInput(field, id, value) {
  if (value === undefined || value === null) {
    value = "";
  }

  let html = "<input id='" + id + "' type='" + field.type + "' value='" + safe(value) + "'";
  if (field.placeholder) {
    html += " placeholder='" + field.placeholder + "'";
  }
  if (field.min !== undefined) {
    html += " min='" + field.min + "'";
  }
  if (field.type === "number") {
    if (field.wholeNumber) {
      html += " step='1'";
    } else {
      html += " step='0.01'";
    }
  }
  html += ">";
  return html;
}

// prefix: "s_" = ช่องค้นหา, "f_" = ช่องในฟอร์ม
function makeField(field, prefix, value) {
  const id = prefix + field.key;
  const isForm = prefix === "f_";

  let input = "";
  if (field.type === "chips") {
    input = makeChips(field, id, value, !isForm);
  } else if (field.type === "select") {
    input = makeSelect(field, id, value);
  } else {
    input = makeInput(field, id, value);
  }

  let star = "";
  if (field.required && isForm) {
    star = " <span class='req'>*</span>";
  }

  let className = "field";
  if (field.wide) {
    className = "field wide";
  }

  return "<div class='" + className + "'><label for='" + id + "'>" + field.label + star + "</label>" + input + "</div>";
}

function getValue(id) {
  const element = document.getElementById(id);
  if (element.classList.contains("chips")) {
    return element.dataset.value;
  }
  return element.value.trim();
}


// ---------- ค้นหา ----------

async function showSearchBox() {
  const tab = TABS[currentTab];
  await loadCustomerList(tab.search);

  let html = "";
  for (const field of tab.search) {
    html += makeField(field, "s_");
  }
  document.getElementById("searchTitle").textContent = tab.label;
  document.getElementById("searchFields").innerHTML = html;

  for (const field of tab.search) {
    const element = document.getElementById("s_" + field.key);
    if (field.type === "text") {
      element.addEventListener("input", searchLater);
    } else {
      element.addEventListener("change", searchLater);
    }
  }
}

// รอให้พิมพ์เสร็จก่อนค่อยค้นหา
function searchLater() {
  clearTimeout(searchTimer);
  searchTimer = setTimeout(search, 250);
}

async function search() {
  const tab = TABS[currentTab];

  let url = tab.api + "?";
  for (const field of tab.search) {
    const value = getValue("s_" + field.key);
    if (value !== "") {
      url += field.key + "=" + encodeURIComponent(value) + "&";
    }
  }

  searchNumber = searchNumber + 1;
  const myNumber = searchNumber;
  showStatus("กำลังโหลด...", false);

  const result = await callApi(url);

  // ถ้ามีการค้นหาใหม่เกิดขึ้นระหว่างรอ ให้ใช้ผลของอันใหม่แทน
  if (myNumber === searchNumber) {
    showTable(result);
  }
}


// ---------- ตาราง ----------

function showStatus(message, isError) {
  const box = document.getElementById("status");
  box.textContent = message;
  box.className = "status";
  if (isError) {
    box.className = "status err";
  }
  if (message === "") {
    box.className = "status hidden";
  }
}

function formatCell(column, value) {
  if (value === null || value === "") {
    return "<span class='muted'>—</span>";
  }
  if (MONEY_COLUMNS.includes(column)) {
    return Number(value).toLocaleString("th-TH", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  }
  if (BADGE_COLUMNS.includes(column)) {
    let text = THAI_NAMES[value];
    if (text === undefined) {
      text = value;
    }
    return "<span class='badge " + safe(value) + "'>" + safe(text) + "</span>";
  }
  return safe(value);
}

function cellClass(column) {
  if (column === "items") {
    return "wrap";
  }
  if (NUMBER_COLUMNS.includes(column)) {
    return "num";
  }
  return "";
}

function showTable(result) {
  const tab = TABS[currentTab];
  document.getElementById("tableHead").innerHTML = "";
  document.getElementById("tableBody").innerHTML = "";
  document.getElementById("count").textContent = "";
  currentRows = [];

  if (!result.ok) {
    showStatus("⚠️ " + result.error, true);
    return;
  }
  if (result.data.length === 0) {
    showStatus("ไม่พบข้อมูลที่ตรงกับเงื่อนไข", false);
    return;
  }

  currentRows = result.data;
  showStatus("", false);
  document.getElementById("count").textContent = currentRows.length + " รายการ";

  const columns = [];
  for (const column of Object.keys(currentRows[0])) {
    if (!tab.hideColumns.includes(column)) {
      columns.push(column);
    }
  }

  let head = "";
  for (const column of columns) {
    let title = COLUMN_NAMES[column];
    if (column === tab.idColumn) {
      title = "#";
    }
    head += "<th class='" + cellClass(column) + "'>" + title + "</th>";
  }
  document.getElementById("tableHead").innerHTML = head + "<th></th>";

  let body = "";
  for (let i = 0; i < currentRows.length; i++) {
    const row = currentRows[i];
    const id = row[tab.idColumn];

    body += "<tr>";
    for (const column of columns) {
      let cell = formatCell(column, row[column]);
      if (column === tab.idColumn) {
        cell = i + 1;
      }
      body += "<td class='" + cellClass(column) + "'>" + cell + "</td>";
    }
    body += "<td class='actions'>";
    body += "<button class='btn sm' onclick='editRow(" + id + ")'>✏️ แก้ไข</button> ";
    body += "<button class='btn sm del' onclick='deleteRow(" + id + ")'>🗑 ลบ</button>";
    body += "</td></tr>";
  }
  document.getElementById("tableBody").innerHTML = body;
}


// ---------- ฟอร์ม เพิ่ม / แก้ไข ----------

async function openForm(title, data) {
  const fields = TABS[currentTab].form;
  await loadCustomerList(fields);

  let html = "";
  for (const field of fields) {
    html += makeField(field, "f_", data[field.key]);
  }

  document.getElementById("modalTitle").textContent = title;
  document.getElementById("formFields").innerHTML = html;
  document.getElementById("formError").classList.add("hidden");
  document.getElementById("modal").classList.remove("hidden");
  document.querySelector("#formFields input, #formFields select, #formFields .chip").focus();
}

function closeForm() {
  document.getElementById("modal").classList.add("hidden");
}

function readForm() {
  const data = {};
  for (const field of TABS[currentTab].form) {
    data[field.key] = getValue("f_" + field.key);
  }
  return data;
}

// ตรวจค่าในฟอร์ม คืนข้อความเตือน หรือ "" ถ้าผ่าน
function checkForm(fields, data) {
  for (const field of fields) {
    const value = data[field.key];

    if (field.required && value === "") {
      if (field.type === "select") {
        return "กรุณาเลือก" + field.label;
      }
      return "กรุณากรอก" + field.label;
    }

    if (field.type === "number" && value !== "") {
      const number = Number(value);
      if (isNaN(number) || number < field.min) {
        return field.label + " ต้องเป็น " + field.min + " หรือมากกว่า";
      }
      if (field.wholeNumber && !Number.isInteger(number)) {
        return field.label + " ต้องเป็นจำนวนเต็ม";
      }
    }
  }
  return "";
}

function showFormError(message) {
  const box = document.getElementById("formError");
  box.textContent = "⚠️ " + message;
  box.classList.remove("hidden");
}

async function saveForm() {
  const tab = TABS[currentTab];
  const data = readForm();

  const problem = checkForm(tab.form, data);
  if (problem !== "") {
    showFormError(problem);
    return;
  }

  const button = document.getElementById("btnSave");
  button.disabled = true;
  button.textContent = "กำลังบันทึก...";

  let result;
  if (editingId === null) {
    result = await callApi(tab.api, "POST", data);
  } else {
    result = await callApi(tab.api + "/" + editingId, "PUT", data);
  }

  button.disabled = false;
  button.textContent = "บันทึก";

  if (!result.ok) {
    showFormError(result.error);
    return;
  }

  closeForm();
  if (editingId === null) {
    showToast("เพิ่มข้อมูลแล้ว", false);
  } else {
    showToast("บันทึกการแก้ไขแล้ว", false);
  }
  search();
}

function openAddForm() {
  const tab = TABS[currentTab];
  const data = {};
  for (const field of tab.form) {
    if (field.todayByDefault) {
      data[field.key] = today();
    }
  }
  editingId = null;
  openForm("เพิ่ม" + tab.label, data);
}

async function editRow(id) {
  const tab = TABS[currentTab];
  const result = await callApi(tab.api + "/" + id);
  if (!result.ok) {
    showToast("⚠️ " + result.error, true);
    return;
  }
  editingId = id;
  openForm("แก้ไข" + tab.label, result.data);
}

async function deleteRow(id) {
  const tab = TABS[currentTab];

  let name = tab.label + " #" + id;
  for (const row of currentRows) {
    if (row[tab.idColumn] === id && tab.nameColumn !== "") {
      name = row[tab.nameColumn];
    }
  }

  if (!confirm("ลบ \"" + name + "\" ใช่ไหม?")) {
    return;
  }

  const result = await callApi(tab.api + "/" + id, "DELETE");
  if (!result.ok) {
    showToast("⚠️ " + result.error, true);
    return;
  }
  showToast("ลบ \"" + name + "\" แล้ว", false);
  search();
}


// ---------- เปลี่ยนแท็บ และผูกปุ่ม ----------

async function switchTab(tabName) {
  currentTab = tabName;

  for (const button of document.querySelectorAll(".tab")) {
    if (button.dataset.entity === tabName) {
      button.classList.add("active");
    } else {
      button.classList.remove("active");
    }
  }

  const label = TABS[tabName].label;
  document.getElementById("listTitle").textContent = "รายการ" + label;
  document.getElementById("btnAdd").textContent = "+ เพิ่ม" + label;

  await showSearchBox();
  search();
}

for (const button of document.querySelectorAll(".tab")) {
  button.onclick = function () {
    switchTab(button.dataset.entity);
  };
}

document.getElementById("btnClear").onclick = async function () {
  await showSearchBox();
  search();
};
document.getElementById("btnAdd").onclick = openAddForm;
document.getElementById("btnSave").onclick = saveForm;
document.getElementById("btnCancel").onclick = closeForm;

// กดปุ่มตัวเลือก (chip) แล้วจำค่าไว้ที่กล่องของมัน
document.addEventListener("click", function (event) {
  const chip = event.target.closest(".chip");
  if (chip === null) {
    return;
  }
  const group = chip.parentElement;
  group.dataset.value = chip.dataset.value;
  for (const other of group.children) {
    other.classList.remove("active");
  }
  chip.classList.add("active");
  group.dispatchEvent(new Event("change"));
});

document.getElementById("modal").addEventListener("click", function (event) {
  if (event.target.id === "modal") {
    closeForm();
  }
});

document.getElementById("modal").addEventListener("keydown", function (event) {
  if (event.key === "Enter" && event.target.tagName === "INPUT") {
    saveForm();
  }
});

document.addEventListener("keydown", function (event) {
  if (event.key === "Escape") {
    closeForm();
  }
});

switchTab("customers");
