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

# Simple UI

HTML = """
<!doctype html>
<html>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>Ingram Micro • RMA Agent</title>

<style>
  :root{
    --ingram-blue: #0071ce;
    --ingram-light-blue: #e6f0fa;
    --ingram-dark-blue: #003b70;
    --bg: var(--ingram-light-blue);
    --panel: #fff;
    --panel2: #f4f8fb;
    --border: #0071ce;
    --text: #003b70;
    --muted: #5a7ca7;
    --accent: #0071ce;
    --good: #34d399;
    --warn: #fbbf24;
    --bad: #fb7185;
    --shadow: 0 12px 30px rgba(0,113,206,.10);
  }

  *{ box-sizing:border-box; }
  body{
    margin:0;
    font-family: 'Segoe UI', Arial, sans-serif;
    background: var(--bg);
    color:#fff;
  }


  .wrap{
    max-width: 980px;
    margin: 0 auto;
    padding: 22px 16px 28px;
    background: var(--panel);
    border-radius: 18px;
    box-shadow: var(--shadow);
    border: 2px solid var(--border);
    color: #fff;
  }


  .topbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:12px;
    margin-bottom:14px;
    border-bottom: 2px solid var(--border);
    padding-bottom: 10px;
  }


  .brand{
    display:flex;
    align-items:center;
    gap:12px;
  }


  .logo-img{
    width:60px;
    height:60px;
    object-fit:contain;
    border-radius:10px;
    display:block;
    flex-shrink:0;
    margin:0;
    background: #fff;
    border: 2px solid var(--border);
    box-shadow: 0 2px 8px rgba(0,113,206,.08);
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
    color: var(--accent);
    text-transform: uppercase;
  }
  .title span{
    font-size:13px;
    color:var(--muted);
    font-weight: 500;
  }

  .pill{
    display:flex;
    align-items:center;
    gap:8px;
    padding:10px 12px;
    border:1px solid var(--border);
    background: rgba(15,23,42,.6);
    border-radius: 999px;
    box-shadow: 0 6px 18px rgba(0,0,0,.20);
    font-size:12px;
    color:#fff;
    user-select:none;
  }
  #connText {
    color: #fff !important;
    font-weight: bold;
    text-shadow: 0 1px 4px rgba(0,0,0,0.18);
    letter-spacing: 0.5px;
  }
  .dot{
    width:8px; height:8px; border-radius:999px;
    background: var(--good);
    box-shadow: 0 0 12px rgba(52,211,153,.55);
  }
  .dot.off{
    background:#64748b;
    box-shadow:none;
  }

  .card{
    border:1px solid var(--border);
    background: linear-gradient(180deg, rgba(15,23,42,.75), rgba(11,18,32,.75));
    border-radius: 20px;
    box-shadow: var(--shadow);
    overflow:hidden;
  }

  .statusbar{
    display:flex;
    align-items:center;
    justify-content:space-between;
    gap:10px;
    padding: 12px 14px;
    border-bottom: 1px solid rgba(31,42,68,.7);
    background: rgba(15,23,42,.35);
  }
  .status-left{
    display:flex; align-items:center; gap:10px;
    min-width: 0;
  }
  .spinner{
    width:18px; height:18px;
    border:2px solid rgba(159,176,199,.25);
    border-top-color: rgba(96,165,250,.95);
    border-radius: 999px;
    animation: spin .9s linear infinite;
    display:none;
  }
  @keyframes spin { to { transform: rotate(360deg);} }

  .status-text{
    font-size:12px;
    color: #fff !important;
    font-weight: bold;
    text-shadow: 0 1px 4px rgba(0,0,0,0.18);
    white-space:nowrap;
    overflow:hidden;
    text-overflow:ellipsis;
  }

  .actions{
    display:flex; gap:8px;
  }
  .ghost{
    border:1px solid rgba(31,42,68,.9);
    background: rgba(11,18,32,.35);
    color: #fff !important;
    font-weight: bold;
    text-shadow: 0 1px 4px rgba(0,0,0,0.18);
    padding:8px 10px;
    border-radius: 12px;
    cursor:pointer;
    font-size:12px;
    transition: transform .08s ease, background .15s ease;
  }
  .ghost:hover{ background: rgba(11,18,32,.6); }
  .ghost:active{ transform: translateY(1px); }

 .chat{
  height: 62vh;
  overflow:auto;
  padding: 14px;
  scroll-behavior:smooth;

  display: flex;              /* NEW */
  flex-direction: column;     /* NEW */
}

.msg{
  display:flex;
  gap:10px;
  margin: 12px 0;
  opacity:0;
  transform: translateY(6px);
  animation: pop .18s ease forwards;

  width: fit-content;         /* key: message wraps content */
  max-width: 100%;            /* don’t overflow */
}

  /* Bot on the left */
.msg.bot{
   align-self: flex-start;     /* key */    
}

/* User on the right */
.msg.me{
 align-self: flex-end;       /* key */
  flex-direction: row-reverse;/* avatar on the right */
}

.msg.me .bubble{
  background:#dbeafe;
  border-color:#93c5fd;
  color:#0f172a;
}
  @keyframes pop {
    to { opacity:1; transform: translateY(0); }
  }

  /* LEFT (bot) */
  .msg.bot{
    justify-content:flex-start;
  }

  /* RIGHT (user) */
  .msg.me{
    justify-content:flex-end;
    flex-direction: row-reverse;
  }

 .msg.me .bubble{
  margin-left:auto;
  text-align:left;
  background:#dbeafe;
  border-color:#93c5fd;
  color:#0f172a;            /* <-- IMPORTANT (text visible on light bg) */
}
.msg.me{
  margin-left:auto;         /* <-- forces the whole row to the right */
  flex-direction: row-reverse;
}

.msg.bot{
  margin-right:auto;        /* keeps bot on the left */
}

  .msg.bot .bubble{
    margin-right:auto;
  }

  .avatar{
    width:34px; height:34px;
    border-radius: 14px;
    display:flex;
    align-items:center;
    justify-content:center;
    font-weight:700;
    font-size:12px;
    flex: 0 0 auto;
    border:1px solid rgba(31,42,68,.85);
    background: rgba(11,18,32,.55);
    color: var(--muted);
  }
  .avatar.me{
    background: rgba(96,165,250,.16);
    color: #cfe6ff;
  }
  .avatar.bot{
    background: rgba(52,211,153,.14);
    color: #c9ffea;
  }

  .bubble{
    max-width: 74%;
    border:1px solid rgba(31,42,68,.9);
    background: rgba(11,18,32,.55);
    padding: 12px 12px;
    border-radius: 16px;
    line-height:1.45;
    font-size: 14px;
    white-space: pre-wrap;
  }
  .bubble.bot{
    background: rgba(15,23,42,.55);
  }

  .meta{
    margin-top:6px;
    font-size: 11px;
    color: rgba(159,176,199,.85);
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
    width:6px; height:6px; border-radius:999px;
    background: rgba(159,176,199,.85);
    animation: bounce 1s infinite;
  }
  .dots span:nth-child(2){ animation-delay: .12s; }
  .dots span:nth-child(3){ animation-delay: .24s; }
  @keyframes bounce{
    0%, 60%, 100%{ transform: translateY(0); opacity:.55; }
    30%{ transform: translateY(-4px); opacity:1; }
  }

  .composer{
    border-top: 1px solid rgba(31,42,68,.7);
    padding: 12px 14px 14px;
    background: rgba(15,23,42,.35);
  }
  .row{
    display:flex;
    gap:10px;
    align-items:flex-end;
  }
  textarea{
    width:100%;
    resize:none;
    min-height: 44px;
    max-height: 160px;
    padding: 12px 12px;
    border-radius: 14px;
    border: 1px solid rgba(31,42,68,.95);
    background: rgba(11,18,32,.55);
    color: #fff;
    outline:none;
    font-size: 14px;
    line-height: 1.35;
  }
  textarea:focus{
    border-color: rgba(96,165,250,.55);
    box-shadow: 0 0 0 3px rgba(96,165,250,.15);
  }
  .send{
    padding: 12px 14px;
    border-radius: 14px;
    border: 1px solid rgba(96,165,250,.55);
    background: rgba(96,165,250,.22);
    color: #d9ecff;
    cursor:pointer;
    font-weight: 650;
    transition: transform .08s ease, background .15s ease;
    white-space:nowrap;
  }
  .send:hover{ background: rgba(96,165,250,.30); }
  .send:active{ transform: translateY(1px); }
  .send:disabled{
    cursor:not-allowed;
    opacity:.55;
  }

  .hint{
    margin-top: 10px;
    font-size: 12px;
    color: rgba(159,176,199,.85);
    display:flex;
    justify-content:space-between;
    gap:10px;
    flex-wrap:wrap;
  }
  .kbd{
    font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, "Liberation Mono";
    font-size: 11px;
    padding: 2px 6px;
    border: 1px solid rgba(31,42,68,.9);
    border-bottom-color: rgba(31,42,68,.55);
    border-radius: 8px;
    background: rgba(11,18,32,.55);
    color: rgba(207,230,255,.9);
  }

  .toast{
    position: fixed;
    left: 50%;
    bottom: 18px;
    transform: translateX(-50%);
    padding: 10px 12px;
    border-radius: 12px;
    border: 1px solid rgba(31,42,68,.9);
    background: rgba(15,23,42,.85);
    color: rgba(231,238,248,.95);
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
  <img src="/static/ingram_logo.png" class="logo-img" alt="Ingram Micro Logo" onerror="this.onerror=null;this.src='https://upload.wikimedia.org/wikipedia/commons/2/2b/Ingram_Micro_logo.svg';">
        <div class="title">
          <h1>Ingram Micro</h1>
          <span>RMA Agent • Internal Demo</span>
        </div>
      </div>
python -m email_intake_poc.server
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
          <textarea id="msg" placeholder="Ask something… (e.g., “Summarize today’s agenda.”)"></textarea>
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
  bubble.textContent = text;

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
    <span style="color: rgba(159,176,199,.95)">Thinking</span>
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
      addMsg("bot", `Error ${r.status}\n${raw}` , `Welcome • ${nowTime()}`);
      setConn(false, "Error");
      setBusy(false, "Idle"); // Ensure Send button is re-enabled after error
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
    addMsg("bot", "Fetch error: " + e, `Welcome • ${nowTime()}`);
    setConn(false, "Offline");
    setBusy(false, "Idle"); // Ensure Send button is re-enabled after error
  }
  finally{
    clearInterval(stepTimer);
    setBusy(false, "Idle");
  }
}

addMsg("bot", "Hi! I’m Rise. Ask me anything, and I’ll respond using your ADK agent.", "Welcome");
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

    # 1) Get or create session (ASYNC in your ADK version)
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
            state={},                 # <- important
            session_id=requested_session_id,  # if your version ignores this, we'll still use session.id
        )
        print("SESSION CREATED:", session.id)

    # 2) Always use the actual session.id from ADK
    actual_session_id = session.id

    # 3) Run agent
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

    # If reply is empty, return a clear error message
    if not reply.strip():
        return JSONResponse({
            "reply": "Sorry, the system could not process your request due to a technical issue. Please try again or rephrase your question.",
            "session_id": actual_session_id
        })

    # Return session_id so the browser keeps using the right one next turn
    return JSONResponse({"reply": reply, "session_id": actual_session_id})


if __name__ == "__main__":
    port = int(os.getenv("PORT", "9000"))
    uvicorn.run(app, host="0.0.0.0", port=port)