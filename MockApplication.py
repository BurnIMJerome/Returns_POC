from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
import os
from google.cloud import bigquery
from datetime import datetime, date
from fastapi.staticfiles import StaticFiles
app = FastAPI()

# Align static file mounting with server.py
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

PROJECT_ID = os.environ.get("BIGQUERY_PROJECT", "")
DATASET = os.environ.get("BIGQUERY_DATASET", "")
TABLE = os.environ.get("BIGQUERY_TABLE", "")

def _json_safe(v):
    """Convert BigQuery values into JSON-safe + form-friendly strings."""
    if v is None:
        return ""
    # BigQuery can return datetime/date objects
    if isinstance(v, (datetime, date)):
        # For form: datetime-local expects "YYYY-MM-DDTHH:MM"
        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%dT%H:%M")
        return v.isoformat()
    return str(v)

def fetch_all_records():
    try:
        client = bigquery.Client(project=PROJECT_ID)
        # NOTE: Ensure Created_Date is present in your table. If it's STRING, ordering is lexicographic.
        query = f"""
            SELECT *
            FROM `{PROJECT_ID}.{DATASET}.{TABLE}`
            ORDER BY Created_Date DESC
            LIMIT 20
        """
        rows = list(client.query(query))
        if not rows:
            return []
        records = []
        for row in rows:
            d = dict(row)
            # Normalize all fields to strings for the UI
            records.append({k: _json_safe(v) for k, v in d.items()})
        return records
    except Exception as e:
        print("[BigQuery ERROR]", e)
        return []

@app.get("/records")
def get_records():
    return JSONResponse(fetch_all_records())

@app.get("/", response_class=HTMLResponse)
def home():
    html = r"""
<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>Ingram Micro • RMA Application</title>

  <style>
    :root{
      --im-blue:#0071CE;
      --im-blue-dark:#005AA6;
      --bg:#F6F8FB;
      --card:#FFFFFF;
      --border:#D9E2EF;
      --text:#0F172A;
      --muted:#5B6B7F;
      --shadow:0 10px 28px rgba(0,0,0,.08);
      --radius:16px;
      --focus:0 0 0 3px rgba(0,113,206,.18);
    }

    *{ box-sizing:border-box; }
    body{
      margin:0;
      font-family: ui-sans-serif, system-ui, -apple-system, Segoe UI, Roboto, Arial, sans-serif;
      background: var(--bg);
      color: var(--text);
      padding: 24px;
    }
    .wrap{ max-width: 1180px; margin: 0 auto; }

    /* Brand header */
    .brandbar{
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:16px;
      background: var(--im-blue);
      color:#fff;
      border-radius: var(--radius);
      padding: 14px 16px;
      box-shadow: var(--shadow);
    }
    .brand-left{
      display:flex;
      align-items:center;
      gap:12px;
      min-width: 260px;
    }
    .logo{
      height:34px;
      width:auto;
      display:block;
      object-fit:contain;
    }
    .brand-title{ display:flex; flex-direction:column; line-height:1.15; }
    .brand-title .app{ font-size:16px; font-weight:800; letter-spacing:.2px; }
    .brand-title .sub{ font-size:12px; opacity:.9; margin-top:4px; }

    .brand-actions{ display:flex; gap:10px; flex-wrap:wrap; justify-content:flex-end; }
    .btn{
      border:1px solid rgba(255,255,255,.35);
      background: rgba(255,255,255,.12);
      color:#fff;
      padding:10px 12px;
      border-radius:12px;
      font-size:13px;
      cursor:pointer;
      user-select:none;
      line-height:1;
    }
    .btn.solid{
      background:#fff;
      color: var(--im-blue);
      border-color:#fff;
      font-weight:800;
    }
    .btn.outline-blue{
      background:#fff;
      color: var(--im-blue);
      border:1px solid var(--border);
      font-weight:700;
    }

    /* Layout */
    .side-main{ display:flex; gap:14px; margin-top:14px; align-items:flex-start; }

    /* Card */
    .card{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow:hidden;
    }
    .card-head{
      padding: 14px 16px;
      border-bottom: 1px solid var(--border);
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:12px;
      flex-wrap:wrap;
      background: linear-gradient(180deg, rgba(0,113,206,.08), rgba(0,113,206,.02));
    }
    .chips{ display:flex; gap:8px; flex-wrap:wrap; }
    .chip{
      font-size:12px;
      padding:6px 10px;
      border-radius:999px;
      border:1px solid var(--border);
      background:#fff;
      color: var(--text);
      white-space:nowrap;
    }
    .chip.blue{
      border-color: rgba(0,113,206,.35);
      background: rgba(0,113,206,.08);
      color: var(--im-blue-dark);
      font-weight:800;
    }

    /* Form grid */
    form{ padding: 16px; }
    .grid{
      display:grid;
      grid-template-columns: repeat(12, 1fr);
      gap: 12px;
    }
    .field{
      grid-column: span 6;
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 10px;
      background: #fff;
    }
    .field.small{ grid-column: span 4; }
    .field.full{ grid-column: span 12; }

    label{
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap:10px;
      font-size:12px;
      color: var(--muted);
      margin: 0 0 6px 0;
    }
    .req{
      color: var(--im-blue-dark);
      font-weight:900;
      font-size:11px;
      letter-spacing:.2px;
    }
    input, select{
      width:100%;
      border:1px solid var(--border);
      background:#fff;
      color: var(--text);
      border-radius: 12px;
      padding: 10px 10px;
      font-size: 14px;
      outline: none;
    }
    input::placeholder{ color: #98A6B8; }
    input:focus, select:focus{
      border-color: rgba(0,113,206,.65);
      box-shadow: var(--focus);
    }

    .footer{
      padding: 14px 16px;
      border-top: 1px solid var(--border);
      display:flex;
      justify-content:space-between;
      align-items:center;
      gap: 12px;
      flex-wrap:wrap;
      background:#fff;
    }
    .hint{
      font-size:12px;
      color: var(--muted);
      line-height:1.35;
      max-width: 760px;
    }

    /* Side table (match theme) */
    .side-table{
      width: 360px;
      flex: 0 0 360px;
    }
    .side-table .table-head{
      padding: 14px 16px;
      border-bottom:1px solid var(--border);
      display:flex;
      align-items:center;
      justify-content:space-between;
      gap:10px;
      background: linear-gradient(180deg, rgba(0,113,206,.08), rgba(0,113,206,.02));
    }
    .side-table .table-head h3{
      margin:0;
      font-size:14px;
      color: var(--im-blue-dark);
      letter-spacing:.2px;
    }
    .side-table .table-wrap{
      padding: 10px 10px 12px;
    }
    .table-controls{
      display:flex;
      gap:8px;
      margin: 0 0 10px;
    }
    .mini-input{
      flex:1;
      border:1px solid var(--border);
      border-radius: 12px;
      padding: 9px 10px;
      font-size: 13px;
      outline:none;
    }
    .mini-input:focus{
      border-color: rgba(0,113,206,.65);
      box-shadow: var(--focus);
    }

    table{
      width:100%;
      border-collapse:separate;
      border-spacing:0;
      overflow:hidden;
      border:1px solid var(--border);
      border-radius: 14px;
      background:#fff;
    }
    thead th{
      text-align:left;
      font-size:12px;
      color:#fff;
      background: var(--im-blue);
      padding:10px 10px;
      border-bottom:1px solid rgba(255,255,255,.15);
      position:sticky;
      top:0;
      z-index:1;
    }
    tbody td{
      font-size:12.5px;
      padding:10px 10px;
      border-top:1px solid var(--border);
      color: var(--text);
    }
    tbody tr{ cursor:pointer; }
    tbody tr:hover{ background: rgba(0,113,206,.06); }
    tbody tr.selected{ background: rgba(0,113,206,.12); }

    /* Make table scroll if many records */
    .table-scroll{
      max-height: 520px;
      overflow:auto;
      border-radius: 14px;
    }

    /* Responsive */
    @media (max-width: 980px){
      body{ padding:16px; }
      .side-main{ flex-direction:column; }
      .side-table{ width:100%; flex: 1 1 auto; }
      .field, .field.small{ grid-column: span 12; }
      .brand-left{ min-width:auto; }
    }
  </style>
</head>

<body>
  <div class="wrap">

    <div class="brandbar">
      <div class="brand-left">
        <!-- Update logo path as needed -->
        <img class="logo" src="/static/ingram_logo.png" alt="Ingram Micro" />
        <div class="brand-title">
          <div class="app">RMA Application</div>
          <div class="sub">Create • Track • Validate Returns</div>
        </div>
      </div>
      <div class="brand-actions">
        <button class="btn" type="button" onclick="loadRecords()">Refresh</button>
        <button class="btn" type="button" onclick="clearForm()">Clear</button>
        <button class="btn solid" type="button">Submit RMA</button>
      </div>
    </div>

    <div class="side-main">

      <!-- LEFT: Records table (theme-aligned) -->
      <div class="card side-table">
        <div class="table-head">
          <h3>RMA Records</h3>
          <span class="chip">Last 20</span>
        </div>
        <div class="table-wrap">
          <div class="table-controls">
            <input id="filterBox" class="mini-input" placeholder="Filter by RMA / Customer / Status…" oninput="applyFilter()" />
          </div>

          <div class="table-scroll">
            <table id="rmaTable">
              <thead>
                <tr>
                  <th style="width:42%;">Order_Number</th>
                  <th style="width:28%;">Status</th>
                  <th style="width:30%;">Customer_ID</th>
                </tr>
              </thead>
              <tbody></tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- RIGHT: Main form -->
      <div style="flex:1;">
        <div class="card">
          <div class="card-head">
            <div class="chips">
              <span class="chip blue">RMA # <span id="chip_RMA_ID">—</span></span>
              <span class="chip"><b>Status:</b>&nbsp;<span id="chip_Status">—</span></span>
              <span class="chip"><b>Priority:</b>&nbsp;<span id="chip_Priority">—</span></span>
              <span class="chip"><b>Source:</b>&nbsp;<span id="chip_Source_Channel">—</span></span>
            </div>
            <div class="chips">
              <span class="chip"><b>Customer:</b>&nbsp;<span id="chip_Customer_ID">—</span></span>
              <span class="chip"><b>Created By:</b>&nbsp;<span id="chip_Created_By">—</span></span>
            </div>
          </div>

          <form id="rmaForm">
            <div class="grid">
              <div class="field small">
                <label>RMA_ID <span class="req">REQUIRED</span></label>
                <input name="RMA_ID" placeholder="e.g., RMA-902134" />
              </div>
              <div class="field small">
                <label>Customer_ID <span class="req">REQUIRED</span></label>
                <input name="Customer_ID" placeholder="e.g., 66724518" />
              </div>
              <div class="field small">
                <label>Source_Channel</label>
                <select name="Source_Channel">
                  <option>Email</option>
                  <option>Portal</option>
                  <option>Phone</option>
                  <option>Chat</option>
                  <option>EDI</option>
                  <option>Other</option>
                </select>
              </div>

              <div class="field">
                <label>Order_Number <span class="req">REQUIRED</span></label>
                <input name="Order_Number" placeholder="e.g., SO-774589" />
              </div>
              <div class="field">
                <label>Invoice_Number <span class="req">REQUIRED</span></label>
                <input name="Invoice_Number" placeholder="e.g., 56382910" />
              </div>

              <div class="field">
                <label>RMA_Type</label>
                <select name="RMA_Type">
                  <option>Replacement</option>
                  <option>Repair</option>
                  <option>Credit</option>
                  <option>Return Only</option>
                  <option>DOA</option>
                </select>
              </div>

              <div class="field">
                <label>Reason_Code</label>
                <select name="Reason_Code">
                  <option>Hardware Failure</option>
                  <option>Damaged in Transit</option>
                  <option>Wrong Item Shipped</option>
                  <option>Missing Parts</option>
                  <option>Not as Described</option>
                  <option>Other</option>
                </select>
              </div>

              <div class="field small">
                <label>Status</label>
                <select name="Status">
                  <option>New</option>
                  <option>Pending</option>
                  <option>Approved</option>
                  <option>Rejected</option>
                  <option>In Progress</option>
                  <option>Closed</option>
                </select>
              </div>

              <div class="field small">
                <label>Priority</label>
                <select name="Priority">
                  <option>Low</option>
                  <option>Medium</option>
                  <option>High</option>
                  <option>Critical</option>
                </select>
              </div>

              <div class="field small">
                <label>Created_By</label>
                <input name="Created_By" placeholder="e.g., Ran / Michael / Jerome" />
              </div>

              <div class="field small">
                <label>Created_Date</label>
                <input name="Created_Date" type="datetime-local" />
              </div>

              <div class="field small">
                <label>Approved_Date</label>
                <input name="Approved_Date" type="datetime-local" />
              </div>

              <div class="field small">
                <label>Closed_Date</label>
                <input name="Closed_Date" type="datetime-local" />
              </div>
            </div>
          </form>

          <div class="footer">
            <div class="hint">
              <b>Schema Mapping:</b> RMA_ID, Order_Number, Invoice_Number, RMA_Type, Reason_Code, Status, Priority,
              Created_Date, Approved_Date, Closed_Date, Created_By, Source_Channel, Customer_ID
            </div>
            <div class="brand-actions">
              <button class="btn outline-blue" type="button" onclick="saveDraft()">Save Draft</button>
              <button class="btn solid" type="button">Submit</button>
            </div>
          </div>

        </div>
      </div>

    </div>
  </div>

  <script>
    let __allRecords = [];

    function esc(v){
      if (v === null || v === undefined) return '';
      return String(v);
    }

    async function loadRecords() {
      const res = await fetch('/records');
      const data = await res.json();
      __allRecords = Array.isArray(data) ? data : [];
      renderTable(__allRecords);
      // Auto-select first record (optional)
      if (__allRecords.length > 0) {
        const firstRow = document.querySelector('#rmaTable tbody tr');
        if (firstRow) firstRow.click();
      }
    }

    function renderTable(records){
      const tbody = document.querySelector('#rmaTable tbody');
      tbody.innerHTML = '';
      records.forEach((rec) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
          <td>${esc(rec.Order_Number)}</td>
          <td>${esc(rec.Status)}</td>
          <td>${esc(rec.Customer_ID)}</td>
        `;
        tr.addEventListener('click', () => selectRecord(rec, tr));
        tbody.appendChild(tr);
      });
    }

    function applyFilter(){
      const q = (document.getElementById('filterBox').value || '').toLowerCase().trim();
      if (!q) return renderTable(__allRecords);
      const filtered = __allRecords.filter(r => {
        const blob = `${r.Order_Number||''} ${r.Customer_ID||''} ${r.Status||''}`.toLowerCase();
        return blob.includes(q);
      });
      renderTable(filtered);
    }

    function selectRecord(rec, tr) {
      // Highlight selected tbody row only
      document.querySelectorAll('#rmaTable tbody tr').forEach(row => row.classList.remove('selected'));
      tr.classList.add('selected');

      // Fill form fields
      for (const key in rec) {
        const el = document.querySelector(`[name="${key}"]`);
        if (el) el.value = rec[key] || '';
        const chip = document.getElementById('chip_' + key);
        if (chip) chip.textContent = rec[key] || '—';
      }
      // If some chips weren't in record, keep them as —
      ['RMA_ID','Status','Priority','Source_Channel','Customer_ID','Created_By'].forEach(k=>{
        const chip = document.getElementById('chip_'+k);
        if (chip && !chip.textContent) chip.textContent = '—';
      });
    }

    function clearForm(){
      // Clear form inputs
      const form = document.getElementById('rmaForm');
      form.reset();

      // Clear chips
      ['RMA_ID','Status','Priority','Source_Channel','Customer_ID','Created_By'].forEach(k=>{
        const chip = document.getElementById('chip_'+k);
        if (chip) chip.textContent = '—';
      });

      // Clear selection highlight
      document.querySelectorAll('#rmaTable tbody tr').forEach(row => row.classList.remove('selected'));
    }

    function saveDraft(){
      alert("Draft saved (sample UI).");
    }

    function submitRMA() {
      const rmaId = document.querySelector("[name='RMA_ID']").value || 'N/A';
      const details = `RMA: ${rmaId} successfully submitted!`;
      alert(details);
    }

    // Attach the submitRMA function to the Submit button
    window.onload = () => {
      loadRecords();
      document.querySelector(".btn.solid").addEventListener("click", submitRMA);
    };
  </script>
</body>
</html>
"""
    return HTMLResponse(content=html)