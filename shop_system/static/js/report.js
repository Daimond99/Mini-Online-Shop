// ขอข้อมูลจากหลังบ้าน แล้วคืนเฉพาะส่วน data
async function getData(url) {
  const response = await fetch(url);
  const result = await response.json();
  return result.data;
}

// กันข้อความแปลก ๆ ไม่ให้กลายเป็น HTML
function safe(text) {
  return String(text).replaceAll("<", "&lt;").replaceAll(">", "&gt;");
}

// ใส่ลูกน้ำให้ตัวเลข เช่น 112620.00 -> 112,620
function formatNumber(value) {
  return Number(value).toLocaleString("th-TH");
}


// การ์ดตัวเลขด้านบน
async function showSummary() {
  const data = await getData("/api/reports/summary");

  let html = "";
  for (const label in data) { //วนทุกชื่อใน dict ต่อ HTML เป็นการ์ด
    html += "<div class='metric'>";
    html += "<div class='metric-num'>" + formatNumber(data[label]) + "</div>";
    html += "<div class='metric-label'>" + label + "</div>";
    html += "</div>";
  }
  document.getElementById("summary").innerHTML = html;
}


// กราฟแท่ง Top 10: คอลัมน์แรก = ชื่อ, คอลัมน์ที่สอง = ตัวเลข
async function showChart(key) {
  const rows = await getData("/api/rankings/" + key); //list ของ dict [{"สินค้า": "G502", "จำนวนที่ขายได้ (ชิ้น)": 1, ...}
  const box = document.getElementById("chart-" + key);

  if (rows.length === 0) {
    box.innerHTML = "<p class='status'>ยังไม่มีข้อมูล</p>";
    return;
  }

  const columns = Object.keys(rows[0]);
  const nameColumn = columns[0]; //ชื่อหลัง AS ใน SQL
  const valueColumn = columns[1]; //ตัวเลขหลัง AS ใน SQL

  //หาค่าที่มากที่สุดในคอลัมน์ตัวเลข วนหา max (ค่ามากสุด) เพื่อเป็นตัวหาร
  let max = 0;
  for (const row of rows) {
    if (Number(row[valueColumn]) > max) {
      max = Number(row[valueColumn]);
    }
  }

  let html = "";
  for (let i = 0; i < rows.length; i++) {
    const row = rows[i];
    const percent = Number(row[valueColumn]) / max * 100;  //percent = ค่า ÷ max × 100 อันดับ 1 ได้ 100% อันอื่นสั้นลงตามสัดส่วน แล้วใส่เป็นความกว้าง

    html += "<div class='chart-row'>";
    html += "<span class='chart-no'>" + (i + 1) + "</span>";
    html += "<span class='chart-name'>" + safe(row[nameColumn]) + "</span>";
    html += "<div class='chart-bar'><div style='width:" + percent + "%'></div></div>";
    html += "<span class='chart-value'>" + formatNumber(row[valueColumn]) + "</span>";
    html += "</div>";
  }
  box.innerHTML = html;
}


// ตารางรายงาน: หัวตาราง = ชื่อหลัง AS ใน SQL
async function showReport(key) { //key = รับชื่อรายงานเข้ามา เช่น best-selling
  const rows = await getData("/api/reports/" + key); //list ของ dict {"สินค้า": "Logitech G502 HERO","หมวดหมู่": "เมาส์เกมมิ่ง", "จำนวนที่ขายได้": "15"}
  const box = document.getElementById("report-" + key); // box คือกล่องว่างใน report.html

  if (rows.length === 0) {
    box.innerHTML = "<p class='status'>ไม่มีข้อมูล</p>";
    return;
  }

  const columns = Object.keys(rows[0]); //list ชื่อหลัง AS ใน SQL เช่น ["สินค้า", "หมวดหมู่", "จำนวนที่ขายได้"]

  let html = "<table><tr><th>#</th>";
  for (const column of columns) { //วนทุกชื่อใน list ต่อ HTML
    html += "<th>" + column + "</th>";
  }
  html += "</tr>";

  //สร้างแถวข้อมูล วนทุกแถวใน list ต่อ HTML
  for (let i = 0; i < rows.length; i++) {
    html += "<tr><td>" + (i + 1) + "</td>";
    for (const column of columns) {
      const value = rows[i][column];
      if (isNaN(value)) {
        html += "<td>" + safe(value) + "</td>";
      } else {
        html += "<td>" + formatNumber(value) + "</td>";
      }
    }
    html += "</tr>";
  }
  html += "</table>";

  box.innerHTML = html;
}


showSummary();

showChart("products-qty");
showChart("products-revenue");
showChart("customers-spend");

showReport("best-selling");
showReport("top-customers");
showReport("high-rated");
