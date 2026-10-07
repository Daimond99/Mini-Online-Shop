// report.js — หน้ารายงาน: ขอข้อมูลจาก /api/reports แล้ววาดการ์ดและตาราง

// ขอข้อมูลจากหลังบ้าน
async function getJson(url) {
  const response = await fetch(url);
  return await response.json();
}

// การ์ดตัวเลขด้านบน (1 ชื่อ = 1 การ์ด)
async function showSummaryCards() {
  const result = await getJson("/api/reports/summary");
  const box = document.querySelector("#summary");

  if (!result.ok) {
    box.innerHTML = `<div class="status err">⚠️ ${result.error}</div>`;
    return;
  }

  let html = "";
  for (const label in result.data) {
    html += `
      <div class="metric">
        <div class="metric-num">${result.data[label]}</div>
        <div class="metric-label">${label}</div>
      </div>`;
  }
  box.innerHTML = html;
}

// สร้างตารางจากแถวข้อมูล (หัวตารางคือชื่อหลัง AS ใน SQL)
function makeTableHtml(rows) {
  if (rows.length === 0) return "<p class='status'>ไม่มีข้อมูล</p>";

  const columns = Object.keys(rows[0]);
  let html = "<table><thead><tr>";
  for (const column of columns) {
    html += `<th>${column}</th>`;
  }
  html += "</tr></thead><tbody>";

  for (const row of rows) {
    html += "<tr>";
    for (const column of columns) {
      html += `<td>${row[column]}</td>`;
    }
    html += "</tr>";
  }
  return html + "</tbody></table>";
}

// รายงานทุกตัว: 1 กล่องต่อ 1 รายงาน
async function showReports() {
  const list = await getJson("/api/reports");

  for (const report of list.data) {
    const result = await getJson("/api/reports/" + report.key);
    const content = result.ok ? makeTableHtml(result.data) : `<div class="status err">⚠️ ${result.error}</div>`;

    document.querySelector("#reports").innerHTML += `
      <section class="card">
        <h3>${report.title}</h3>
        <div class="table-wrap">${content}</div>
      </section>`;
  }
}

showSummaryCards();
showReports();
