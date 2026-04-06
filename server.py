print("RUNNING:", __file__)

import os
import uvicorn
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService
from google.genai.types import Content, Part

from .agent import root_agent

APP_NAME = "SampleUI"
USER_ID = "web_user"

app = FastAPI()
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ADK session + runner
session_service = InMemorySessionService()
runner = Runner(app_name=APP_NAME, agent=root_agent, session_service=session_service)

HTML = """
<!doctype html>
<html>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>Ingram Micro • RMA Agent</title>

<style>
  :root{
    --ingram-blue: #0071CE;
    --ingram-dark-blue: #003A8F;
    --ingram-light-blue: #E6F2FB;
    --ingram-accent: #00A3E0;

    --bg: #E6F2FB;
    --panel: #FFFFFF;
    --panel2: #F4F9FF;

    --border: #0071CE;
    --text: #003A8F;
    --muted: #6B8DB5;

    --good: #22C55E;
    --warn: #F59E0B;
    --bad: #EF4444;

    --shadow: 0 10px 25px rgba(0,113,206,.12);
  }

  *{ box-sizing:border-box; }

  body{
    margin:0;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: var(--bg);
    color: var(--text);
  }

  .wrap{
    max-width: 980px;
    margin: 0 auto;
    padding: 22px 16px 28px;
  }

  .topbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin-bottom:18px;
    border-bottom: 2px solid var(--border);
    padding-bottom: 12px;
  }

  .brand{
    display:flex;
    align-items:center;
    gap:12px;
  }

  .logo-img{
    width:76px;
    height:76px;
    object-fit:contain;
    border-radius:12px;
    display:block;
    flex-shrink:0;
    background: #fff;
  }

  .title{
    display:flex;
    flex-direction:column;
    line-height:1.15;
  }

  .title h1{
    font-size:22px;
    margin:0;
    font-weight:800;
    letter-spacing:.2px;
    color: var(--ingram-blue);
    text-transform: uppercase;
  }

  .title span{
    font-size:13px;
    color: var(--muted);
    font-weight: 600;
  }

  .pill{
    display:flex;
    align-items:center;
    gap:8px;
    padding:10px 16px;
    border:1px solid var(--ingram-blue);
    background: #FFFFFF;
    border-radius: 999px;
    box-shadow: var(--shadow);
    font-size:14px;
    color: var(--text);
    user-select:none;
    font-weight: 700;
  }

  #connText {
    color: var(--text);
    font-weight: 700;
    letter-spacing: 0.2px;
  }

  .dot{
    width:10px;
    height:10px;
    border-radius:999px;
    background: var(--good);
    box-shadow: 0 0 8px rgba(34,197,94,.35);
  }

  .dot.off{
    background:#94A3B8;
    box-shadow:none;
  }

  .card{
    border: 2px solid var(--border);
    background: var(--panel);
    border-radius: 22px;
    box-shadow: var(--shadow);
    overflow:hidden;
  }

  .statusbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    padding: 16px 18px;
    border-bottom: 1px solid #D7E8F8;
    background: var(--ingram-dark-blue);
  }

  .status-left{
    display:flex;
    align-items:center;
    gap:10px;
    min-width: 0;
  }

  .spinner{
    width:18px;
    height:18px;
    border:2px solid rgba(255,255,255,.25);
    border-top-color: #FFFFFF;
    border-radius: 999px;
    animation: spin .9s linear infinite;
    display:none;
  }

  @keyframes spin { to { transform: rotate(360deg);} }

  .status-text{
    font-size:14px;
    color: #FFFFFF;
    font-weight: 700;
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
  }

  .actions{
    display:flex;
    gap:10px;
  }

  .ghost{
    border:1px solid rgba(255,255,255,.22);
    background: rgba(255,255,255,.08);
    color: #FFFFFF;
    font-weight: 700;
    padding:10px 16px;
    border-radius: 14px;
    cursor:pointer;
    font-size:14px;
    transition: transform .08s ease, background .15s ease;
  }

  .ghost:hover{ background: rgba(255,255,255,.16); }
  .ghost:active{ transform: translateY(1px); }

  .chat{
    height: 62vh;
    overflow:auto;
    padding: 18px;
    scroll-behavior:smooth;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #F4F9FF 0%, #EEF6FD 100%);
  }

  .msg{
    display:flex;
    gap:10px;
    margin: 12px 0;
    opacity:0;
    transform: translateY(6px);
    animation: pop .18s ease forwards;
    width: fit-content;
    max-width: 100%;
  }

  .msg.bot{
    align-self: flex-start;
    margin-right:auto;
  }

  .msg.me{
    align-self: flex-end;
    margin-left:auto;
    flex-direction: row-reverse;
  }

  @keyframes pop {
    to { opacity:1; transform: translateY(0); }
  }

  .avatar{
    width:40px;
    height:40px;
    border-radius: 16px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
    font-size:12px;
    flex: 0 0 auto;
    border:1px solid #CFE3F7;
    background: #FFFFFF;
    color: var(--ingram-blue);
  }

  .avatar.me{
    background: var(--ingram-blue);
    color: #FFFFFF;
    border-color: var(--ingram-blue);
  }

  .avatar.bot{
    background: #E8F4FD;
    color: var(--ingram-dark-blue);
  }

  .bubble{
    max-width: 74%;
    border:1px solid #D6E7F8;
    padding: 14px 14px;
    border-radius: 18px;
    line-height:1.5;
    font-size: 14px;
    white-space: pre-wrap;
    box-shadow: 0 4px 10px rgba(0,113,206,.06);
  }

  .bubble.bot{
    background: #FFFFFF;
    color: var(--text);
  }

  .msg.me .bubble{
    margin-left:auto;
    text-align:left;
    background:#D9ECFF;
    border-color:#A5D3FF;
    color:#003A8F;
  }

  .meta{
    margin-top:6px;
    font-size: 11px;
    color: #7A95B8;
  }

  .typing{
    display:inline-flex;
    align-items:center;
    gap:6px;
  }

  .dots{
    display:inline-flex;
    gap:4px;
    align-items:center;
    height: 14px;
  }

  .dots span{
    width:6px;
    height:6px;
    border-radius:999px;
    background: #7A95B8;
    animation: bounce 1s infinite;
  }

  .dots span:nth-child(2){ animation-delay: .12s; }
  .dots span:nth-child(3){ animation-delay: .24s; }

  @keyframes bounce{
    0%, 60%, 100%{ transform: translateY(0); opacity:.55; }
    30%{ transform: translateY(-4px); opacity:1; }
  }

  .composer{
    border-top: 1px solid #D7E8F8;
    padding: 14px 18px 16px;
    background: #F7FBFF;
  }

  .row{
    display:flex;
    gap:10px;
    align-items:flex-end;
  }

  textarea{
    width:100%;
    resize:none;
    min-height: 50px;
    max-height: 160px;
    padding: 14px 14px;
    border-radius: 16px;
    border: 1px solid #CFE3F7;
    background: #FFFFFF;
    color: var(--text);
    outline:none;
    font-size: 14px;
    line-height: 1.4;
  }

  textarea:focus{
    border-color: var(--ingram-blue);
    box-shadow: 0 0 0 3px rgba(0,113,206,.12);
  }

  .send{
    padding: 14px 18px;
    border-radius: 16px;
    border: 1px solid var(--ingram-blue);
    background: var(--ingram-blue);
    color: #FFFFFF;
    cursor:pointer;
    font-weight: 700;
    transition: transform .08s ease, background .15s ease;
    white-space:nowrap;
  }

  .send:hover{ background: #005FB2; }
  .send:active{ transform: translateY(1px); }

  .send:disabled{
    cursor:not-allowed;
    opacity:.55;
  }

  .hint{
    margin-top: 10px;
    font-size: 12px;
    color: #6B8DB5;
    display:flex;
    justify-content:space-between;
    gap:10px;
    flex-wrap:wrap;
  }

  .kbd{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono";
    font-size: 11px;
    padding: 2px 6px;
    border: 1px solid #CFE3F7;
    border-bottom-color: #B7D6F4;
    border-radius: 8px;
    background: #FFFFFF;
    color: var(--text);
  }

  .toast{
    position: fixed;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid #CFE3F7;
    background: #FFFFFF;
    color: var(--text);
    font-size: 12px;
    box-shadow: var(--shadow);
    opacity:0;
    pointer-events:none;
    transition: opacity .18s ease, transform .18s ease;
  }

  .toast.show{
    opacity:1;
    transform: translateX(-50%) translateY(-4px);
  }
</style>
</head>

<body>
  <div class="wrap">
    <div class="topbar">
      <div class="brand">
        <img src="/static/ingram_logo.png" class="logo-img" alt="Ingram Micro Logo">
        <div class="title">
          <h1>Ingram Micro</h1>
          <span>RMA Agent • Internal Demo</span>
        </div>
      </div>

      <div class="pill" id="connPill" title="Backend connection">
        <span class="dot" id="connDot"></span>
        <span id="connText">Ready</span>
      </div>
    </div>

    <div class="card">
      <div class="statusbar">
        <div class="status-left">
          <span class="spinner" id="spin"></span>
          <div class="status-text" id="statusText">Idle</div>
        </div>
        <div class="actions">
          <button class="ghost" onclick="clearChat()">Clear chat</button>
          <button class="ghost" onclick="newSession()">New session</button>
        </div>
      </div>

      <div class="chat" id="chat"></div>

      <div class="composer">
        <div class="row">
          <textarea id="msg" placeholder="Ask something… (View unread emails, view items needing validation, view reports, or validate an RMA request)"></textarea>
          <button class="send" id="sendBtn" onclick="send()">Send</button>
        </div>
        <div class="hint">
          <div><span class="kbd">Enter</span> send • <span class="kbd">Shift</span> + <span class="kbd">Enter</span> newline</div>
          <div style="opacity:.85">Session: <span id="sessLabel"></span></div>
        </div>
      </div>
    </div>
  </div>

  <div class="toast" id="toast"></div>

<script>
let sessionId = localStorage.getItem("adk_session_id") || "demo_session";
const chatEl = document.getElementById("chat");
const msgEl = document.getElementById("msg");
const sendBtn = document.getElementById("sendBtn");
const statusText = document.getElementById("statusText");
const spinner = document.getElementById("spin");
const sessLabel = document.getElementById("sessLabel");
const connDot = document.getElementById("connDot");
const connText = document.getElementById("connText");
const toastEl = document.getElementById("toast");

sessLabel.textContent = sessionId;

function nowTime(){
  const d = new Date();
  return d.toLocaleTimeString([], {hour:'2-digit', minute:'2-digit'});
}

function toast(msg){
  toastEl.textContent = msg;
  toastEl.classList.add("show");
  setTimeout(()=> toastEl.classList.remove("show"), 1600);
}

function setBusy(isBusy, text){
  spinner.style.display = isBusy ? "inline-block" : "none";
  statusText.textContent = text || (isBusy ? "Working…" : "Idle");
  sendBtn.disabled = isBusy;
}

function setConn(ok, text){
  connDot.classList.toggle("off", !ok);
  connText.textContent = text || (ok ? "Ready" : "Offline");
}

function addMsg(role, text, meta){
  const row = document.createElement("div");
  row.className = "msg " + (role === "me" ? "me" : "bot");

  const avatar = document.createElement("div");
  avatar.className = "avatar " + (role === "me" ? "me" : "bot");
  avatar.textContent = role === "me" ? "You" : "AI";

  const bubbleWrap = document.createElement("div");

  const bubble = document.createElement("div");
  bubble.className = "bubble " + (role === "me" ? "me" : "bot");

  if (role === "bot") {
    bubble.innerHTML = text;
  } else {
    bubble.textContent = text;
  }

  const m = document.createElement("div");
  m.className = "meta";
  m.textContent = meta || nowTime();

  bubbleWrap.appendChild(bubble);
  bubbleWrap.appendChild(m);

  row.appendChild(avatar);
  row.appendChild(bubbleWrap);

  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;

  return bubble;
}

function addTyping(){
  const row = document.createElement("div");
  row.className = "msg bot";

  const avatar = document.createElement("div");
  avatar.className = "avatar bot";
  avatar.textContent = "AI";

  const bubbleWrap = document.createElement("div");
  const bubble = document.createElement("div");
  bubble.className = "bubble bot";

  const typing = document.createElement("div");
  typing.className = "typing";
  typing.innerHTML = `
    <span style="color:#6B8DB5">Thinking</span>
    <span class="dots"><span></span><span></span><span></span></span>
  `;

  bubble.appendChild(typing);

  const m = document.createElement("div");
  m.className = "meta";
  m.textContent = nowTime();

  bubbleWrap.appendChild(bubble);
  bubbleWrap.appendChild(m);

  row.appendChild(avatar);
  row.appendChild(bubbleWrap);

  chatEl.appendChild(row);
  chatEl.scrollTop = chatEl.scrollHeight;

  return row;
}

function clearChat(){
  chatEl.innerHTML = "";
  toast("Chat cleared");
}

function newSession(){
  sessionId = "demo_session_" + crypto.randomUUID();
  localStorage.setItem("adk_session_id", sessionId);
  sessLabel.textContent = sessionId;
  clearChat();
  toast("New session started");
}

function autoGrow(){
  msgEl.style.height = "auto";
  msgEl.style.height = Math.min(msgEl.scrollHeight, 160) + "px";
}

msgEl.addEventListener("input", autoGrow);
msgEl.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
});

async function send(){
  const msg = msgEl.value.trim();
  if (!msg) return;

  addMsg("me", msg);
  msgEl.value = "";
  autoGrow();

  setBusy(true, "Sending to agent…");
  setConn(true, "Working");

  const typingRow = addTyping();

  const steps = [
    "Routing request…",
    "Running tools (if needed)…",
    "Generating response…"
  ];

  let i = 0;
  const stepTimer = setInterval(()=>{
    statusText.textContent = steps[i % steps.length];
    i++;
  }, 900);

  try{
    const r = await fetch("/chat",{
      method:"POST",
      headers:{ "Content-Type":"application/json" },
      body: JSON.stringify({ session_id: sessionId, message: msg })
    });

    const raw = await r.text();

    if(!r.ok){
      typingRow.remove();
      addMsg("bot", `Error ${r.status}<br>${raw}`, `System • ${nowTime()}`);
      setConn(false, "Error");
      setBusy(false, "Idle");
      return;
    }

    const data = JSON.parse(raw);

    if (data.session_id) {
      sessionId = data.session_id;
      localStorage.setItem("adk_session_id", sessionId);
      sessLabel.textContent = sessionId;
    }

    typingRow.remove();
    addMsg("bot", data.reply || "(no reply)", "Just now");
    setConn(true, "Ready");
  }
  catch(e){
    typingRow.remove();
    addMsg("bot", "Fetch error: " + e, `System • ${nowTime()}`);
    setConn(false, "Offline");
    setBusy(false, "Idle");
  }
  finally{
    clearInterval(stepTimer);
    setBusy(false, "Idle");
  }
}

addMsg(
  "bot",
  "Hi! I'm IRA, your Intelligent Returns Agent Assistant. I can help you review incoming emails, validate RMA requests, and create support cases.",
  "Welcome"
);
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML


@app.post("/chat")
async def chat(payload: dict):
    print("CHAT payload:", payload)

    requested_session_id = payload.get("session_id", "demo_session")
    message = payload.get("message", "")

    try:
        session = await session_service.get_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            session_id=requested_session_id,
        )
        print("SESSION FOUND:", session.id)
    except Exception:
        session = await session_service.create_session(
            app_name=APP_NAME,
            user_id=USER_ID,
            state={},
            session_id=requested_session_id,
        )
        print("SESSION CREATED:", session.id)

    actual_session_id = session.id

    events = runner.run(
        user_id=USER_ID,
        session_id=actual_session_id,
        new_message=Content(role="user", parts=[Part(text=message)]),
    )

    reply = ""
    for event in events:
        if event.content and event.content.parts:
            for part in event.content.parts:
                if getattr(part, "text", None):
                    reply += part.text

    print("REPLY:", reply)

    if not reply.strip():
        return JSONResponse({
            "reply": "Sorry, the system could not process your request due to a technical issue. Please try again or rephrase your question.",
            "session_id": actual_session_id
        })

    return JSONResponse({"reply": reply, "session_id": actual_session_id})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "9000"))
    uvicorn.run(app, host="0.0.0.0", port=port)