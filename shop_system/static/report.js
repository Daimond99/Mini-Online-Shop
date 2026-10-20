// report.js — หน้ารายงาน: การ์ดสรุป + ตารางรายงาน

// ---------- ตั้งค่า ----------
const SUMMARY_ICONS = {
  "ลูกค้า": "👤", "สินค้า": "📦", "ออเดอร์": "🧾", "รีวิว": "⭐",
  "รายได้รวม (บาท)": "💰", "ออเดอร์รอดำเนินการ": "⏳",
};

const TIER_LABELS = { regular: "ทั่วไป", silver: "ซิลเวอร์", gold: "โกลด์" };

// รายงานบังคับ 3 รายการ: bar = คอลัมน์ที่วาดแถบ, max = ค่าเต็มของแถบ
const REPORT_INFO = {
  "best-selling": {
    number: 1, bar: "จำนวนที่ขายได้",
    desc: "สินค้าที่ขายได้จำนวนชิ้นมากที่สุด (ไม่นับออเดอร์ที่ยกเลิก)",
    tags: ["JOIN 3 ตาราง", "GROUP BY", "SUM"],
  },
  "top-customers": {
    number: 2, bar: "ยอดซื้อรวม",
    desc: "ลูกค้าที่ยอดซื้อรวมสูงกว่าค่าเฉลี่ยของลูกค้าทุกคน",
    tags: ["JOIN 3 ตาราง", "GROUP BY", "HAVING", "Subquery + AVG"],
  },
  "high-rated": {
    number: 3, bar: "คะแนนเฉลี่ย", max: 5,
    desc: "สินค้าที่ได้คะแนนรีวิวเฉลี่ยตั้งแต่ 4 ดาวขึ้นไป (เต็ม 5)",
    tags: ["JOIN 3 ตาราง", "GROUP BY", "AVG", "HAVING"],
  },
};


// ---------- ตัวช่วย ----------
async function getJson(url) {
  const response = await fetch(url);
  return await response.json();
}

function escapeHtml(text) {
  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" };
  return String(text).replace(/[&<>"']/g, ch => map[ch]);
}

function isNumber(value) {
  return value !== null && value !== "" && !isNaN(value);
}

// 112620.00 -> 112,620.00
function formatValue(value) {
  if (value === null) return "—";
  if (!isNumber(value)) return escapeHtml(value);
  const decimals = String(value).includes(".") ? 2 : 0;
  return Number(value).toLocaleString("th-TH", { minimumFractionDigits: decimals, maximumFractionDigits: decimals });
}

function barCell(value, max) {
  const width = max ? Math.min(100, Math.round(Number(value) / max * 100)) : 0;
  return `<div class="bar-cell">
      <div class="bar"><span style="width:${width}%"></span></div>
      <span class="bar-num">${formatValue(value)}</span>
    </div>`;
}

function formatCell(column, value, info, max) {
  if (column === info.bar) return barCell(value, max);
  if (column === "ระดับ") {
    return `<span class="badge ${escapeHtml(value)}">${TIER_LABELS[value] || escapeHtml(value)}</span>`;
  }
  return formatValue(value);
}


// ---------- การ์ดสรุป ----------
async function showSummaryCards() {
  const result = await getJson("/api/reports/summary");
  const box = document.querySelector("#summary");

  if (!result.ok) {
    box.innerHTML = `<div class="status err">⚠️ ${escapeHtml(result.error)}</div>`;
    return;
  }

  let html = "";
  for (const label in result.data) {
    html += `
      <div class="metric">
        <div class="metric-icon">${SUMMARY_ICONS[label] || "📊"}</div>
        <div class="metric-num">${formatValue(result.data[label])}</div>
        <div class="metric-label">${escapeHtml(label)}</div>
      </div>`;
  }
  box.innerHTML = html;
}


// ---------- ตารางรายงาน ----------
function makeTableHtml(rows, info) {
  if (rows.length === 0) return "<p class='status'>ไม่มีข้อมูล</p>";

  const columns = Object.keys(rows[0]);
  const max = info.max || Math.max(...rows.map(row => Number(row[info.bar]) || 0));
  const numClass = column => isNumber(rows[0][column]) && column !== info.bar ? "num" : "";

  let html = "<table><thead><tr><th>#</th>";
  for (const column of columns) {
    html += `<th class="${numClass(column)}">${escapeHtml(column)}</th>`;
  }
  html += "</tr></thead><tbody>";

  rows.forEach((row, index) => {
    html += `<tr><td class="rank">${index + 1}</td>`;
    for (const column of columns) {
      html += `<td class="${numClass(column)}">${formatCell(column, row[column], info, max)}</td>`;
    }
    html += "</tr>";
  });
  return html + "</tbody></table>";
}

function makeReportCard(report, result) {
  const info = REPORT_INFO[report.key] || { tags: [] };
  const number = info.number ? `<span class="report-no">รายงานที่ ${info.number}</span>` : "";
  const tags = (info.tags || []).map(tag => `<span class="tag">${tag}</span>`).join("");
  const content = result.ok
    ? makeTableHtml(result.data, info)
    : `<div class="status err">⚠️ ${escapeHtml(result.error)}</div>`;

  return `
    <section class="card report">
      <div class="report-head">
        ${number}
        <h3>${escapeHtml(report.title)}</h3>
        ${info.desc ? `<p class="report-desc">${info.desc}</p>` : ""}
        <div class="tags">${tags}</div>
      </div>
      <div class="table-wrap">${content}</div>
    </section>`;
}

async function showReports() {
  const list = await getJson("/api/reports");
  const results = await Promise.all(list.data.map(report => getJson("/api/reports/" + report.key)));

  document.querySelector("#reports").innerHTML =
    list.data.map((report, i) => makeReportCard(report, results[i])).join("");
}

showSummaryCards();
showReports();
