<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Momentum — Stay On Track</title>
<link href="https://fonts.googleapis.com/css2?family=Fraunces:ital,wght@0,300;0,500;0,700;1,300&family=DM+Sans:wght@300;400;500&display=swap" rel="stylesheet">
<style>
  :root {
    --cream: #FAF6F0; --warm-white: #FFF9F2; --amber: #E8873A;
    --amber-light: #F5A55C; --amber-pale: #FDE8D2; --brown: #3D2B1F;
    --brown-mid: #7A5C48; --brown-light: #B89080; --green: #5C8A5E;
    --green-pale: #D8EDD9; --red: #C0442A; --red-pale: #F9DDD8;
    --gray: #A89C94; --card-shadow: 0 2px 16px rgba(61,43,31,0.08);
  }
  * { margin:0; padding:0; box-sizing:border-box; }
  body { font-family:'DM Sans',sans-serif; background:var(--cream); color:var(--brown); min-height:100vh; }

  /* NAV */
  nav { background:var(--warm-white); border-bottom:1px solid rgba(61,43,31,0.08); padding:0 32px; display:flex; align-items:center; justify-content:space-between; height:60px; position:sticky; top:0; z-index:100; }
  .nav-logo { font-family:'Fraunces',serif; font-size:22px; font-weight:700; color:var(--amber); display:flex; align-items:center; gap:8px; }
  .nav-logo span { color:var(--brown); }
  .nav-links { display:flex; align-items:center; gap:8px; }
  .nav-btn { padding:7px 16px; border-radius:20px; font-family:'DM Sans',sans-serif; font-size:13.5px; font-weight:500; cursor:pointer; border:none; transition:all .18s; }
  .nav-btn-ghost { background:transparent; color:var(--brown-mid); }
  .nav-btn-ghost:hover { background:var(--amber-pale); color:var(--brown); }
  .nav-btn-primary { background:var(--amber); color:white; }
  .nav-btn-primary:hover { background:var(--amber-light); transform:translateY(-1px); }

  /* LAYOUT */
  .app-layout { max-width:900px; margin:0 auto; padding:32px 24px; display:grid; grid-template-columns:1fr 280px; gap:24px; }
  @media(max-width:680px){ .app-layout{grid-template-columns:1fr} .sidebar{order:-1} }

  /* STREAK */
  .streak-card { background:linear-gradient(135deg,var(--brown) 0%,#5C3D2A 100%); border-radius:20px; padding:28px; color:white; margin-bottom:20px; position:relative; overflow:hidden; animation:fadeSlideUp .4s ease both; }
  .streak-card::before { content:''; position:absolute; top:-40px; right:-40px; width:200px; height:200px; background:rgba(232,135,58,.15); border-radius:50%; }
  .streak-label { font-size:12px; font-weight:500; letter-spacing:1.5px; text-transform:uppercase; opacity:.6; margin-bottom:8px; }
  .streak-number { font-family:'Fraunces',serif; font-size:64px; font-weight:700; line-height:1; color:var(--amber-light); position:relative; z-index:1; }
  .streak-text { font-size:18px; opacity:.85; margin-top:4px; position:relative; z-index:1; }
  .streak-dots { display:flex; gap:6px; margin-top:20px; position:relative; z-index:1; }
  .streak-dot { width:28px; height:28px; border-radius:50%; background:rgba(255,255,255,.12); display:flex; align-items:center; justify-content:center; font-size:8px; font-weight:500; opacity:.7; flex-direction:column; gap:2px; }
  .streak-dot.active { background:var(--amber); opacity:1; }

  /* TASKS */
  .tasks-header { display:flex; align-items:center; justify-content:space-between; margin-bottom:16px; animation:fadeSlideUp .4s .1s ease both; }
  .tasks-title { font-family:'Fraunces',serif; font-size:22px; font-weight:500; }
  .task-count { font-size:13px; color:var(--brown-light); background:var(--amber-pale); padding:4px 10px; border-radius:20px; font-weight:500; }
  .add-task-btn { background:var(--amber); color:white; border:none; border-radius:12px; padding:10px 18px; font-family:'DM Sans',sans-serif; font-size:14px; font-weight:500; cursor:pointer; display:flex; align-items:center; gap:6px; transition:all .18s; }
  .add-task-btn:hover { background:var(--amber-light); transform:translateY(-1px); box-shadow:0 4px 12px rgba(232,135,58,.3); }

  /* ADD FORM */
  .add-task-form { background:var(--warm-white); border:1.5px solid var(--amber-pale); border-radius:16px; padding:20px; margin-bottom:16px; display:none; animation:fadeSlideUp .25s ease both; }
  .add-task-form.visible { display:block; }
  .form-row { display:flex; gap:10px; align-items:flex-end; }
  .form-field { flex:1; }
  .form-field label { display:block; font-size:11px; font-weight:500; letter-spacing:.8px; text-transform:uppercase; color:var(--brown-light); margin-bottom:6px; }
  .form-input { width:100%; padding:10px 14px; border:1.5px solid rgba(61,43,31,.12); border-radius:10px; font-family:'DM Sans',sans-serif; font-size:14px; color:var(--brown); background:white; outline:none; transition:border-color .18s; }
  .form-input:focus { border-color:var(--amber); }
  .form-actions { display:flex; gap:8px; margin-top:14px; justify-content:flex-end; }
  .btn-cancel { padding:9px 16px; border-radius:10px; border:1.5px solid rgba(61,43,31,.12); background:white; color:var(--brown-mid); font-family:'DM Sans',sans-serif; font-size:13px; cursor:pointer; }
  .btn-save { padding:9px 20px; border-radius:10px; border:none; background:var(--amber); color:white; font-family:'DM Sans',sans-serif; font-size:13px; font-weight:500; cursor:pointer; transition:all .18s; }
  .btn-save:hover { background:var(--amber-light); }

  /* TASK CARDS */
  .task-list { display:flex; flex-direction:column; gap:10px; }
  .task-card { background:var(--warm-white); border:1px solid rgba(61,43,31,.07); border-radius:14px; padding:16px 18px; display:flex; align-items:center; gap:14px; transition:all .2s; animation:fadeSlideUp .35s ease both; }
  .task-card:hover { box-shadow:var(--card-shadow); transform:translateY(-1px); }
  .task-card.completed { opacity:.6; }
  .task-card.completed .task-title { text-decoration:line-through; color:var(--brown-light); }
  .task-card.warned { border-color:rgba(192,68,42,.2); background:linear-gradient(135deg,var(--warm-white),#FFF5F3); }
  .task-checkbox { width:22px; height:22px; border-radius:50%; border:2px solid rgba(61,43,31,.2); cursor:pointer; flex-shrink:0; display:flex; align-items:center; justify-content:center; transition:all .18s; background:white; }
  .task-checkbox:hover { border-color:var(--amber); }
  .task-checkbox.checked { background:var(--green); border-color:var(--green); }
  .task-checkbox.checked::after { content:'✓'; color:white; font-size:12px; font-weight:700; }
  .task-body { flex:1; min-width:0; }
  .task-title { font-size:15px; font-weight:500; color:var(--brown); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
  .task-meta { display:flex; align-items:center; gap:10px; margin-top:4px; flex-wrap:wrap; }
  .task-due { font-size:12px; color:var(--brown-light); }
  .task-due.overdue { color:var(--red); font-weight:500; }
  .task-badge { font-size:11px; font-weight:500; padding:2px 8px; border-radius:20px; }
  .badge-warn { background:var(--red-pale); color:var(--red); }
  .postpone-count { font-size:12px; color:var(--brown-light); }
  .task-delete { background:none; border:none; cursor:pointer; color:var(--brown-light); font-size:14px; padding:4px; border-radius:6px; transition:all .18s; opacity:0; }
  .task-card:hover .task-delete { opacity:1; }
  .task-delete:hover { background:var(--red-pale); color:var(--red); }

  /* SIDEBAR */
  .sidebar { display:flex; flex-direction:column; gap:16px; }
  .sidebar-card { background:var(--warm-white); border:1px solid rgba(61,43,31,.07); border-radius:16px; padding:20px; animation:fadeSlideUp .4s .15s ease both; }
  .sidebar-title { font-family:'Fraunces',serif; font-size:15px; font-weight:500; margin-bottom:14px; color:var(--brown); }
  .stat-row { display:flex; justify-content:space-between; align-items:center; padding:8px 0; border-bottom:1px solid rgba(61,43,31,.06); font-size:14px; color:var(--brown-mid); }
  .stat-row:last-child { border-bottom:none; }
  .stat-value { font-family:'Fraunces',serif; font-size:20px; color:var(--brown); font-weight:700; }

  /* EMPTY */
  .empty-state { text-align:center; padding:48px 24px; color:var(--brown-light); }
  .empty-emoji { font-size:40px; margin-bottom:12px; }
  .empty-title { font-family:'Fraunces',serif; font-size:18px; font-weight:500; color:var(--brown-mid); margin-bottom:6px; }
  .empty-sub { font-size:14px; }

  /* MODAL */
  .modal-overlay { position:fixed; inset:0; background:rgba(61,43,31,.4); backdrop-filter:blur(4px); z-index:200; display:none; align-items:center; justify-content:center; animation:fadeIn .2s ease; }
  .modal-overlay.visible { display:flex; }
  .modal { background:var(--warm-white); border-radius:20px; padding:32px; max-width:460px; width:90%; animation:scaleIn .25s ease; }
  .modal-icon { font-size:36px; margin-bottom:12px; }
  .modal-title { font-family:'Fraunces',serif; font-size:22px; font-weight:700; color:var(--brown); margin-bottom:8px; }
  .modal-desc { font-size:14px; color:var(--brown-mid); margin-bottom:24px; line-height:1.6; }
  .modal-actions { display:flex; gap:10px; justify-content:flex-end; }
  .btn-primary { padding:10px 20px; border-radius:10px; border:none; background:var(--amber); color:white; font-family:'DM Sans',sans-serif; font-size:14px; font-weight:500; cursor:pointer; transition:all .18s; }
  .btn-primary:hover { background:var(--amber-light); }
  .btn-secondary { padding:10px 20px; border-radius:10px; border:1.5px solid rgba(61,43,31,.12); background:white; color:var(--brown-mid); font-family:'DM Sans',sans-serif; font-size:14px; cursor:pointer; }

  /* AUTH */
  .auth-page { min-height:100vh; display:none; align-items:center; justify-content:center; background:var(--cream); }
  .auth-page.visible { display:flex; }
  .auth-card { background:var(--warm-white); border-radius:24px; padding:48px 40px; width:100%; max-width:400px; box-shadow:0 8px 40px rgba(61,43,31,.12); animation:scaleIn .3s ease; }
  .auth-logo { font-family:'Fraunces',serif; font-size:28px; font-weight:700; color:var(--amber); margin-bottom:4px; text-align:center; }
  .auth-subtitle { text-align:center; color:var(--brown-light); font-size:14px; margin-bottom:32px; }
  .auth-tabs { display:flex; background:var(--cream); border-radius:12px; padding:4px; margin-bottom:24px; }
  .auth-tab { flex:1; padding:8px; text-align:center; border-radius:9px; cursor:pointer; font-size:14px; font-weight:500; color:var(--brown-light); transition:all .18s; border:none; background:none; }
  .auth-tab.active { background:white; color:var(--amber); box-shadow:0 1px 6px rgba(61,43,31,.1); }
  .auth-field { margin-bottom:16px; }
  .auth-field label { display:block; font-size:12px; font-weight:500; letter-spacing:.8px; text-transform:uppercase; color:var(--brown-light); margin-bottom:6px; }
  .auth-input { width:100%; padding:12px 16px; border:1.5px solid rgba(61,43,31,.12); border-radius:12px; font-family:'DM Sans',sans-serif; font-size:14px; color:var(--brown); background:white; outline:none; transition:border-color .18s; }
  .auth-input:focus { border-color:var(--amber); }
  .auth-submit { width:100%; padding:13px; background:var(--amber); color:white; border:none; border-radius:12px; font-family:'DM Sans',sans-serif; font-size:15px; font-weight:500; cursor:pointer; margin-top:8px; transition:all .18s; }
  .auth-submit:hover { background:var(--amber-light); transform:translateY(-1px); }
  .msg { padding:10px 14px; border-radius:10px; font-size:13px; margin-bottom:14px; display:none; }
  .msg-error { background:var(--red-pale); color:var(--red); }
  .msg-success { background:var(--green-pale); color:var(--green); }

  /* LOADING */
  .spinner { display:inline-block; width:16px; height:16px; border:2px solid rgba(255,255,255,.4); border-top-color:white; border-radius:50%; animation:spin .6s linear infinite; vertical-align:middle; margin-right:6px; }
  @keyframes spin { to { transform:rotate(360deg); } }

  @keyframes fadeSlideUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:translateY(0)} }
  @keyframes fadeIn { from{opacity:0} to{opacity:1} }
  @keyframes scaleIn { from{opacity:0;transform:scale(.95)} to{opacity:1;transform:scale(1)} }
</style>
</head>
<body>

<!-- AUTH -->
<div class="auth-page visible" id="authPage">
  <div class="auth-card">
    <div class="auth-logo">🔥 Momentum</div>
    <div class="auth-subtitle">Stay consistent. Avoid burnout.</div>
    <div class="auth-tabs">
      <button class="auth-tab active" id="tabLogin" onclick="switchTab('login')">Log In</button>
      <button class="auth-tab" id="tabRegister" onclick="switchTab('register')">Sign Up</button>
    </div>
    <div class="msg msg-error" id="authError"></div>
    <div class="msg msg-success" id="authSuccess"></div>
    <div class="auth-field">
      <label>Email</label>
      <input class="auth-input" type="email" id="authEmail" placeholder="you@college.edu">
    </div>
    <div class="auth-field">
      <label>Password</label>
      <input class="auth-input" type="password" id="authPass" placeholder="8+ characters">
    </div>
    <button class="auth-submit" id="authSubmit" onclick="handleAuth()">Log In</button>
  </div>
</div>

<!-- MAIN APP -->
<div id="mainApp" style="display:none;">
  <nav>
    <div class="nav-logo">🔥 <span>Momentum</span></div>
    <div class="nav-links">
      <span style="font-size:13px;color:var(--brown-light);" id="navEmail"></span>
      <button class="nav-btn nav-btn-ghost" id="adminLink" onclick="showAdminStats()" style="display:none;">Admin Panel</button>
      <button class="nav-btn nav-btn-ghost" onclick="doLogout()">Log out</button>
    </div>
  </nav>

  <div class="app-layout">
    <div>
      <div class="streak-card">
        <div class="streak-label">Current Streak</div>
        <div class="streak-number" id="streakNum">0</div>
        <div class="streak-text" id="streakText">Day Streak 🔥</div>
        <div class="streak-dots" id="streakDots"></div>
      </div>

      <div class="tasks-header">
        <div style="display:flex;align-items:center;gap:12px;">
          <div class="tasks-title">My Tasks</div>
          <div class="task-count" id="taskCountLabel">0 tasks</div>
        </div>
        <button class="add-task-btn" onclick="toggleAddForm()">+ Add Task</button>
      </div>

      <div class="add-task-form" id="addTaskForm">
        <div class="form-row">
          <div class="form-field" style="flex:2;">
            <label>Task Title</label>
            <input class="form-input" id="newTitle" placeholder="What needs to get done?" maxlength="100">
          </div>
          <div class="form-field">
            <label>Due Date</label>
            <input class="form-input" id="newDue" type="date">
          </div>
        </div>
        <div class="form-actions">
          <button class="btn-cancel" onclick="toggleAddForm()">Cancel</button>
          <button class="btn-save" id="saveBtn" onclick="addTask()">Save Task</button>
        </div>
      </div>

      <div class="task-list" id="taskList"></div>
    </div>

    <div class="sidebar">
      <div class="sidebar-card">
        <div class="sidebar-title">Overview</div>
        <div class="stat-row"><span>Total Tasks</span><span class="stat-value" id="statTotal">0</span></div>
        <div class="stat-row"><span>Completed</span><span class="stat-value" id="statDone">0</span></div>
        <div class="stat-row"><span>Overdue</span><span class="stat-value" id="statOverdue" style="color:var(--red)">0</span></div>
      </div>
      <div class="sidebar-card" style="background:linear-gradient(135deg,var(--amber-pale),var(--warm-white));">
        <div class="sidebar-title">💡 Tip</div>
        <div style="font-size:13.5px;color:var(--brown-mid);line-height:1.6;">Complete at least one task each day to keep your streak alive. Small steps add up!</div>
      </div>
    </div>
  </div>
</div>

<!-- BREAKDOWN MODAL -->
<div class="modal-overlay" id="breakdownModal">
  <div class="modal">
    <div class="modal-icon">😰</div>
    <div class="modal-title">This task seems tough!</div>
    <div class="modal-desc" id="breakdownDesc"></div>
    <div class="modal-actions">
      <button class="btn-secondary" onclick="closeModal()">Not Now</button>
      <button class="btn-primary" onclick="breakdownTask()">Break It Down ✂️</button>
    </div>
  </div>
</div>

<script>
const API = '';   // same origin
let currentUser  = null;
let tasks        = [];
let pendingWarnId = null;
let authMode     = 'login';
const today = new Date().toISOString().split('T')[0];

// ── API helpers ───────────────────────────────────────────────────────────────
async function api(method, path, body) {
  // Detect file:// — fetch() cannot reach a server from a local file
  if (location.protocol === 'file:') {
    showServerError();
    return { ok: false, status: 0, data: { error: 'Not connected to server' } };
  }
  try {
    const opts = { method, headers:{'Content-Type':'application/json'}, credentials:'include' };
    if (body) opts.body = JSON.stringify(body);
    const res = await fetch(API + path, opts);
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, status: res.status, data };
  } catch (err) {
    // Network error — server not running
    showServerError();
    return { ok: false, status: 0, data: { error: 'Cannot connect to server' } };
  }
}

function showServerError() {
  // Only show once
  if (document.getElementById('serverBanner')) return;
  const banner = document.createElement('div');
  banner.id = 'serverBanner';
  banner.style.cssText = `
    position:fixed; top:0; left:0; right:0; z-index:9999;
    background:#C0442A; color:white; text-align:center;
    padding:14px 20px; font-family:'DM Sans',sans-serif; font-size:14px;
    line-height:1.6; box-shadow:0 2px 12px rgba(0,0,0,0.3);
  `;
  const isFile = location.protocol === 'file:';
  banner.innerHTML = isFile
    ? `⚠️ <strong>Open this app via Flask, not as a file.</strong>
       Run <code style="background:rgba(255,255,255,0.2);padding:2px 7px;border-radius:4px;">python app.py</code>
       in your terminal, then visit
       <a href="http://localhost:5000" style="color:white;font-weight:700;">http://localhost:5000</a>`
    : `⚠️ <strong>Cannot reach the server.</strong>
       Make sure Flask is running:
       <code style="background:rgba(255,255,255,0.2);padding:2px 7px;border-radius:4px;">python app.py</code>
       then refresh this page.`;
  document.body.prepend(banner);
}

// ── Auth ──────────────────────────────────────────────────────────────────────
function switchTab(mode) {
  authMode = mode;
  document.getElementById('tabLogin').classList.toggle('active', mode==='login');
  document.getElementById('tabRegister').classList.toggle('active', mode==='register');
  document.getElementById('authSubmit').textContent = mode==='login' ? 'Log In' : 'Create Account';
  hideAuthMsgs();
}

function hideAuthMsgs() {
  document.getElementById('authError').style.display = 'none';
  document.getElementById('authSuccess').style.display = 'none';
}

function showAuthError(msg) {
  const el = document.getElementById('authError');
  el.textContent = msg; el.style.display = 'block';
  document.getElementById('authSuccess').style.display = 'none';
}

function showAuthSuccess(msg) {
  const el = document.getElementById('authSuccess');
  el.textContent = msg; el.style.display = 'block';
  document.getElementById('authError').style.display = 'none';
}

async function handleAuth() {
  const email = document.getElementById('authEmail').value.trim();
  const pass  = document.getElementById('authPass').value;
  hideAuthMsgs();

  if (authMode === 'register') {
    if (!email.includes('@')) return showAuthError('Enter a valid email.');
    if (pass.length < 8)      return showAuthError('Password must be 8+ characters.');
    const r = await api('POST', '/api/register', { email, password: pass });
    if (!r.ok) return showAuthError(r.data.error || 'Registration failed.');
    showAuthSuccess('Account created! You can now log in.');
    switchTab('login');
  } else {
    const r = await api('POST', '/api/login', { email, password: pass });
    if (!r.ok) return showAuthError(r.data.error || 'Login failed.');
    currentUser = r.data.user;
    enterApp();
  }
}

async function doLogout() {
  await api('POST', '/api/logout');
  currentUser = null; tasks = [];
  document.getElementById('mainApp').style.display = 'none';
  document.getElementById('authPage').classList.add('visible');
  document.getElementById('authEmail').value = '';
  document.getElementById('authPass').value = '';
}

async function checkSession() {
  const r = await api('GET', '/api/me');
  if (r.ok) { currentUser = r.data; enterApp(); }
}

function enterApp() {
  document.getElementById('authPage').classList.remove('visible');
  document.getElementById('mainApp').style.display = 'block';
  document.getElementById('navEmail').textContent = currentUser.email;
  if (currentUser.is_admin) document.getElementById('adminLink').style.display = 'inline-block';
  document.getElementById('newDue').value = today;
  loadTasks();
}

document.getElementById('authPass').addEventListener('keydown', e => { if(e.key==='Enter') handleAuth(); });

// ── Tasks ─────────────────────────────────────────────────────────────────────
async function loadTasks() {
  const r = await api('GET', '/api/tasks');
  if (!r.ok) return;
  tasks = r.data;
  renderAll();
  // Show breakdown modal for first warned task
  const warned = tasks.find(t => t.postponement_count >= 3 && !t.completed);
  if (warned) { pendingWarnId = warned.id; setTimeout(() => showBreakdownModal(warned), 600); }
}

function renderAll() {
  renderStreak();
  renderTasks();
  renderStats();
}

function renderStreak() {
  const days = ['Su','Mo','Tu','We','Th','Fr','Sa'];
  const dotsEl = document.getElementById('streakDots');
  dotsEl.innerHTML = '';
  let streak = 0;
  // Count consecutive days from today backwards with at least 1 completion
  for (let i = 0; i < 30; i++) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const ds = d.toISOString().split('T')[0];
    const has = tasks.some(t => t.completed && t.completed_at && t.completed_at.startsWith(ds));
    if (has) streak++; else if (i > 0) break;
  }
  document.getElementById('streakNum').textContent = streak;
  document.getElementById('streakText').textContent = streak === 1 ? 'Day Streak! Keep going 🔥' : streak > 1 ? 'Day Streak! Keep it up 🔥' : 'No streak yet — complete a task!';

  for (let i = 6; i >= 0; i--) {
    const d = new Date(); d.setDate(d.getDate() - i);
    const ds = d.toISOString().split('T')[0];
    const has = tasks.some(t => t.completed && t.completed_at && t.completed_at.startsWith(ds));
    const dot = document.createElement('div');
    dot.className = 'streak-dot' + (has ? ' active' : '');
    dot.innerHTML = `<div>${days[d.getDay()]}</div>`;
    dotsEl.appendChild(dot);
  }
}

function renderTasks() {
  const list = document.getElementById('taskList');
  list.innerHTML = '';
  const sorted = [...tasks].sort((a,b) => a.due_date.localeCompare(b.due_date));
  const incomplete = sorted.filter(t => !t.completed).length;
  document.getElementById('taskCountLabel').textContent = `${incomplete} task${incomplete!==1?'s':''}`;

  if (!sorted.length) {
    list.innerHTML = `<div class="empty-state"><div class="empty-emoji">📝</div><div class="empty-title">No tasks yet!</div><div class="empty-sub">Create one to get started.</div></div>`;
    return;
  }

  sorted.forEach((t, i) => {
    const isOverdue = !t.completed && t.due_date < today;
    const isWarned  = t.postponement_count >= 3;
    const card = document.createElement('div');
    card.className = `task-card${t.completed?' completed':''}${isWarned&&!t.completed?' warned':''}`;
    card.style.animationDelay = `${i*0.05}s`;
    const dueLabel = t.due_date === today ? '📅 Due today' : `📅 ${fmtDate(t.due_date)}`;
    card.innerHTML = `
      <div class="task-checkbox${t.completed?' checked':''}" onclick="toggleTask(${t.id})"></div>
      <div class="task-body">
        <div class="task-title">${escHtml(t.title)}</div>
        <div class="task-meta">
          <span class="task-due${isOverdue?' overdue':''}">${dueLabel}</span>
          ${isWarned&&!t.completed?`<span class="task-badge badge-warn">⚠️ Postponed ${t.postponement_count}x</span>`:''}
          ${t.postponement_count>0&&t.postponement_count<3&&!t.completed?`<span class="postpone-count">Postponed ${t.postponement_count}x</span>`:''}
        </div>
      </div>
      <button class="task-delete" onclick="removeTask(${t.id})" title="Delete">✕</button>
    `;
    list.appendChild(card);
  });
}

function renderStats() {
  const total     = tasks.length;
  const completed = tasks.filter(t => t.completed).length;
  const overdue   = tasks.filter(t => !t.completed && t.due_date < today).length;
  document.getElementById('statTotal').textContent   = total;
  document.getElementById('statDone').textContent    = completed;
  document.getElementById('statOverdue').textContent = overdue;
}

async function toggleTask(id) {
  const r = await api('POST', `/api/tasks/${id}/toggle`);
  if (!r.ok) return;
  const idx = tasks.findIndex(t => t.id === id);
  if (idx > -1) tasks[idx] = r.data;
  renderAll();
}

async function addTask() {
  const title = document.getElementById('newTitle').value.trim();
  const due   = document.getElementById('newDue').value;
  if (!title || !due) return alert('Please enter a title and due date.');
  document.getElementById('saveBtn').innerHTML = '<span class="spinner"></span>Saving…';
  const r = await api('POST', '/api/tasks', { title, due_date: due });
  document.getElementById('saveBtn').textContent = 'Save Task';
  if (!r.ok) return alert(r.data.error || 'Failed to save task.');
  tasks.push(r.data);
  document.getElementById('newTitle').value = '';
  document.getElementById('addTaskForm').classList.remove('visible');
  renderAll();
}

async function removeTask(id) {
  if (!confirm('Delete this task?')) return;
  const r = await api('DELETE', `/api/tasks/${id}`);
  if (!r.ok) return alert('Failed to delete task.');
  tasks = tasks.filter(t => t.id !== id);
  renderAll();
}

function toggleAddForm() {
  const form = document.getElementById('addTaskForm');
  form.classList.toggle('visible');
  if (form.classList.contains('visible')) document.getElementById('newTitle').focus();
}

// ── Breakdown modal ───────────────────────────────────────────────────────────
function showBreakdownModal(task) {
  document.getElementById('breakdownDesc').textContent = `You've postponed "${task.title}" ${task.postponement_count} times. Would you like to break it into smaller, more manageable steps?`;
  document.getElementById('breakdownModal').classList.add('visible');
}

function closeModal() {
  document.getElementById('breakdownModal').classList.remove('visible');
  pendingWarnId = null;
}

async function breakdownTask() {
  closeModal();
  const sub = prompt('Enter 2–5 subtask titles separated by commas:');
  if (!sub || !pendingWarnId) return;
  const parent = tasks.find(t => t.id === pendingWarnId);
  const titles = sub.split(',').map(s=>s.trim()).filter(Boolean).slice(0,5);
  for (const title of titles) {
    const r = await api('POST', '/api/tasks', { title, due_date: parent.due_date, parent_task_id: parent.id });
    if (r.ok) tasks.push(r.data);
  }
  renderAll();
}

// ── Admin ─────────────────────────────────────────────────────────────────────
async function showAdminStats() {
  const [stats, users] = await Promise.all([api('GET','/api/admin/stats'), api('GET','/api/admin/users')]);
  if (!stats.ok) return alert('Admin access denied.');
  const s = stats.data;
  const userList = users.data.map(u => `• ${u.email}${u.is_admin?' (admin)':''}`).join('\n');
  alert(`📊 Admin Stats\n\nUsers: ${s.total_users}\nTasks: ${s.total_tasks}\nCompleted: ${s.completed_tasks}\n\n👥 All Users:\n${userList}`);
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function fmtDate(ds) {
  const d = new Date(ds + 'T00:00:00');
  return d.toLocaleDateString('en-US', { month:'short', day:'numeric' });
}

function escHtml(str) {
  return str.replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;');
}

// ── Init ──────────────────────────────────────────────────────────────────────
checkSession();
</script>
</body>
</html>