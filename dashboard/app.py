"""
DASHBOARD - Web-based GUI for Hydra
Start: python hydra.py --dashboard
Then open http://127.0.0.1:5000
"""

import json
import threading
import time
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from flask import Flask, render_template_string, jsonify, request
from plugins import get_plugin, list_plugins, discover_plugins
from core.engine import Engine
from core.result import ResultCollection

app = Flask(__name__)

scan_history = []
active_scan = None
scan_lock = threading.Lock()

DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hydra Dashboard</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #0a0e17;
            color: #c9d1d9;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #161b22 0%, #0d1117 100%);
            border-bottom: 1px solid #30363d;
            padding: 20px 40px;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .logo {
            font-size: 28px;
            font-weight: 700;
            color: #58a6ff;
            font-family: 'Courier New', monospace;
        }
        .logo span { color: #f0883e; }
        .status-badge {
            padding: 6px 16px;
            border-radius: 20px;
            font-size: 13px;
            font-weight: 600;
        }
        .status-idle { background: #1b2a1b; color: #3fb950; border: 1px solid #238636; }
        .status-running { background: #2a1b1b; color: #f85149; border: 1px solid #da3633; animation: pulse 1.5s infinite; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.6; } }
        .container { max-width: 1200px; margin: 0 auto; padding: 30px 20px; }
        .grid { display: grid; grid-template-columns: 400px 1fr; gap: 24px; }
        @media (max-width: 900px) { .grid { grid-template-columns: 1fr; } }
        .card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 24px;
        }
        .card h2 {
            font-size: 16px;
            color: #58a6ff;
            margin-bottom: 20px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
        .card h2::before {
            content: '';
            width: 4px;
            height: 18px;
            background: #58a6ff;
            border-radius: 2px;
        }
        .form-group { margin-bottom: 16px; }
        .form-group label {
            display: block;
            font-size: 13px;
            color: #8b949e;
            margin-bottom: 6px;
            font-weight: 500;
        }
        .form-group input, .form-group select, .form-group textarea {
            width: 100%;
            padding: 10px 14px;
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            color: #c9d1d9;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            transition: border-color 0.2s;
        }
        .form-group input:focus, .form-group select:focus, .form-group textarea:focus {
            outline: none;
            border-color: #58a6ff;
        }
        .form-group textarea { height: 100px; resize: vertical; }
        .form-row { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
        .btn {
            padding: 12px 24px;
            border: none;
            border-radius: 8px;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
            width: 100%;
            transition: all 0.2s;
        }
        .btn-primary {
            background: linear-gradient(135deg, #238636 0%, #2ea043 100%);
            color: white;
        }
        .btn-primary:hover { transform: translateY(-1px); box-shadow: 0 4px 12px rgba(46,160,67,0.3); }
        .btn-primary:disabled { opacity: 0.5; cursor: not-allowed; transform: none; }
        .btn-danger {
            background: linear-gradient(135deg, #da3633 0%, #f85149 100%);
            color: white;
            margin-top: 8px;
        }
        .stats-bar { display: grid; grid-template-columns: repeat(4, 1fr); gap: 16px; margin-bottom: 24px; }
        .stat-card {
            background: #161b22;
            border: 1px solid #30363d;
            border-radius: 12px;
            padding: 20px;
            text-align: center;
        }
        .stat-number { font-size: 32px; font-weight: 700; font-family: 'Courier New', monospace; }
        .stat-label { font-size: 12px; color: #8b949e; margin-top: 4px; text-transform: uppercase; letter-spacing: 1px; }
        .stat-success .stat-number { color: #3fb950; }
        .stat-failed .stat-number { color: #f85149; }
        .stat-total .stat-number { color: #58a6ff; }
        .stat-targets .stat-number { color: #f0883e; }
        table { width: 100%; border-collapse: collapse; }
        th {
            text-align: left;
            padding: 12px 16px;
            font-size: 12px;
            color: #8b949e;
            text-transform: uppercase;
            letter-spacing: 1px;
            border-bottom: 1px solid #30363d;
        }
        td {
            padding: 12px 16px;
            font-size: 14px;
            font-family: 'Courier New', monospace;
            border-bottom: 1px solid #21262d;
        }
        tr:hover { background: #1c2128; }
        .badge { padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 600; }
        .badge-success { background: #1b2a1b; color: #3fb950; }
        .badge-fail { background: #2a1b1b; color: #f85149; }
        .progress-container { margin: 16px 0; display: none; }
        .progress-bar { height: 6px; background: #21262d; border-radius: 3px; overflow: hidden; }
        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #238636, #3fb950);
            border-radius: 3px;
            transition: width 0.3s;
            width: 0%;
        }
        .progress-text { font-size: 13px; color: #8b949e; margin-top: 8px; text-align: center; }
        .live-log {
            background: #0d1117;
            border: 1px solid #30363d;
            border-radius: 8px;
            padding: 16px;
            height: 200px;
            overflow-y: auto;
            font-family: 'Courier New', monospace;
            font-size: 13px;
            margin-top: 16px;
        }
        .log-entry { padding: 2px 0; }
        .log-success { color: #3fb950; }
        .log-fail { color: #8b949e; }
        .log-info { color: #58a6ff; }
        .empty-state { text-align: center; padding: 60px 20px; color: #484f58; }
        .empty-state .icon { font-size: 48px; margin-bottom: 16px; }
        .empty-state p { font-size: 15px; }
    </style>
</head>
<body>
    <div class="header">
        <div class="logo">HYDRA <span>Dashboard</span></div>
        <div id="statusBadge" class="status-badge status-idle">IDLE</div>
    </div>
    <div class="container">
        <div class="stats-bar">
            <div class="stat-card stat-total">
                <div class="stat-number" id="statTotal">0</div>
                <div class="stat-label">Total Attempts</div>
            </div>
            <div class="stat-card stat-success">
                <div class="stat-number" id="statSuccess">0</div>
                <div class="stat-label">Credentials Found</div>
            </div>
            <div class="stat-card stat-failed">
                <div class="stat-number" id="statFailed">0</div>
                <div class="stat-label">Failed</div>
            </div>
            <div class="stat-card stat-targets">
                <div class="stat-number" id="statScans">0</div>
                <div class="stat-label">Scans Run</div>
            </div>
        </div>
        <div class="grid">
            <div>
                <div class="card">
                    <h2>New Scan</h2>
                    <div class="form-group">
                        <label>Target Host</label>
                        <input type="text" id="target" placeholder="192.168.1.100">
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Port</label>
                            <input type="number" id="port" placeholder="Auto">
                        </div>
                        <div class="form-group">
                            <label>Protocol</label>
                            <select id="protocol"></select>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>Username(s) - one per line</label>
                        <textarea id="usernames" placeholder="admin\nroot\nuser">admin</textarea>
                    </div>
                    <div class="form-group">
                        <label>Passwords - one per line (empty = default wordlist)</label>
                        <textarea id="passwords" placeholder="password\nadmin123"></textarea>
                    </div>
                    <div class="form-row">
                        <div class="form-group">
                            <label>Threads</label>
                            <input type="number" id="threads" value="10" min="1" max="50">
                        </div>
                        <div class="form-group">
                            <label>Options</label>
                            <select id="stopOnSuccess">
                                <option value="false">Test all passwords</option>
                                <option value="true">Stop on first success</option>
                            </select>
                        </div>
                    </div>
                    <button class="btn btn-primary" id="btnScan" onclick="startScan()">Launch Scan</button>
                    <button class="btn btn-danger" id="btnStop" onclick="stopScan()" style="display:none;">Stop Scan</button>
                    <div class="progress-container" id="progressContainer">
                        <div class="progress-bar">
                            <div class="progress-fill" id="progressFill"></div>
                        </div>
                        <div class="progress-text" id="progressText">Starting...</div>
                    </div>
                    <div class="live-log" id="liveLog" style="display:none;"></div>
                </div>
            </div>
            <div>
                <div class="card">
                    <h2>Results</h2>
                    <div id="resultsArea">
                        <div class="empty-state">
                            <div class="icon">&#128274;</div>
                            <p>No scans yet. Configure a target and launch a scan.</p>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
<script>
    var pollingInterval = null;
    var totalScans = 0;

    window.onload = function() { loadPlugins(); loadHistory(); };

    async function loadPlugins() {
        try {
            var res = await fetch('/api/plugins');
            var plugins = await res.json();
            var select = document.getElementById('protocol');
            select.innerHTML = '';
            for (var i = 0; i < plugins.length; i++) {
                var opt = document.createElement('option');
                opt.value = plugins[i].name;
                opt.textContent = plugins[i].name + ' (port ' + plugins[i].default_port + ')';
                select.appendChild(opt);
            }
        } catch(e) {
            console.error('Failed to load plugins:', e);
        }
    }

    async function startScan() {
        var target = document.getElementById('target').value.trim();
        if (!target) { alert('Enter a target host'); return; }
        var protocol = document.getElementById('protocol').value;
        var port = document.getElementById('port').value || '';
        var usernames = document.getElementById('usernames').value.trim();
        var passwords = document.getElementById('passwords').value.trim();
        var threads = document.getElementById('threads').value || 10;
        var stopOnSuccess = document.getElementById('stopOnSuccess').value === 'true';
        if (!usernames) { alert('Enter at least one username'); return; }

        document.getElementById('btnScan').disabled = true;
        document.getElementById('btnScan').textContent = 'Scanning...';
        document.getElementById('btnStop').style.display = 'block';
        document.getElementById('progressContainer').style.display = 'block';
        document.getElementById('liveLog').style.display = 'block';
        document.getElementById('liveLog').innerHTML = '';
        document.getElementById('statusBadge').className = 'status-badge status-running';
        document.getElementById('statusBadge').textContent = 'SCANNING';
        addLog('Starting scan against ' + target + '...', 'info');

        try {
            var usernameList = usernames.split(String.fromCharCode(10)).filter(function(u) { return u.trim(); });
            var passwordList = passwords ? passwords.split(String.fromCharCode(10)).filter(function(p) { return p.trim(); }) : [];

            var res = await fetch('/api/scan', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    target: target,
                    protocol: protocol,
                    port: port,
                    threads: parseInt(threads),
                    usernames: usernameList,
                    passwords: passwordList,
                    stop_on_success: stopOnSuccess
                })
            });
            var data = await res.json();
            if (data.error) { addLog('Error: ' + data.error, 'fail'); resetUI(); return; }
            addLog('Scan started - ID: ' + data.scan_id, 'info');
            pollingInterval = setInterval(function() { pollStatus(data.scan_id); }, 500);
        } catch(e) { addLog('Error: ' + e.message, 'fail'); resetUI(); }
    }

    async function pollStatus(scanId) {
        try {
            var res = await fetch('/api/scan/' + scanId);
            var data = await res.json();
            var total = data.total || 1;
            var done = data.completed || 0;
            var pct = Math.round((done / total) * 100);
            document.getElementById('progressFill').style.width = pct + '%';
            document.getElementById('progressText').textContent = done + ' / ' + total + ' (' + pct + '%)';
            document.getElementById('statTotal').textContent = done;
            document.getElementById('statSuccess').textContent = data.successes || 0;
            document.getElementById('statFailed').textContent = (done - (data.successes || 0));

            if (data.new_results) {
                for (var i = 0; i < data.new_results.length; i++) {
                    var r = data.new_results[i];
                    if (r.success) {
                        addLog('FOUND: ' + r.username + ':' + r.password + ' @ ' + r.host + ':' + r.port, 'success');
                    }
                }
            }
            if (data.status === 'completed') {
                clearInterval(pollingInterval);
                addLog('Scan complete! ' + (data.successes || 0) + ' credentials found.', 'info');
                totalScans++;
                document.getElementById('statScans').textContent = totalScans;
                renderResults(data.results);
                resetUI();
            }
        } catch(e) { console.error('Poll error:', e); }
    }

    async function stopScan() {
        try {
            await fetch('/api/scan/stop', {method: 'POST'});
            addLog('Scan stopped by user.', 'info');
            clearInterval(pollingInterval);
            resetUI();
        } catch(e) { console.error('Stop error:', e); }
    }

    function renderResults(results) {
        var area = document.getElementById('resultsArea');
        if (!results || results.length === 0) {
            area.innerHTML = '<div class="empty-state"><div class="icon">&#128270;</div><p>No credentials found.</p></div>';
            return;
        }
        var html = '<table><thead><tr><th>Host</th><th>Port</th><th>Protocol</th><th>Username</th><th>Password</th><th>Status</th></tr></thead><tbody>';
        for (var i = 0; i < results.length; i++) {
            var r = results[i];
            var badge = r.success ? '<span class="badge badge-success">SUCCESS</span>' : '<span class="badge badge-fail">FAILED</span>';
            html += '<tr><td>' + r.host + '</td><td>' + r.port + '</td><td>' + r.protocol + '</td><td>' + r.username + '</td><td>' + (r.success ? r.password : '***') + '</td><td>' + badge + '</td></tr>';
        }
        html += '</tbody></table>';
        area.innerHTML = html;
    }

    function addLog(msg, type) {
        var log = document.getElementById('liveLog');
        var entry = document.createElement('div');
        entry.className = 'log-entry log-' + type;
        var time = new Date().toLocaleTimeString();
        entry.textContent = '[' + time + '] ' + msg;
        log.appendChild(entry);
        log.scrollTop = log.scrollHeight;
    }

    function resetUI() {
        document.getElementById('btnScan').disabled = false;
        document.getElementById('btnScan').textContent = 'Launch Scan';
        document.getElementById('btnStop').style.display = 'none';
        document.getElementById('statusBadge').className = 'status-badge status-idle';
        document.getElementById('statusBadge').textContent = 'IDLE';
    }

    async function loadHistory() {
        try {
            var res = await fetch('/api/history');
            var data = await res.json();
            if (data.length > 0) {
                totalScans = data.length;
                document.getElementById('statScans').textContent = totalScans;
                var last = data[data.length - 1];
                if (last.results) {
                    var successes = last.results.filter(function(r) { return r.success; });
                    document.getElementById('statTotal').textContent = last.results.length;
                    document.getElementById('statSuccess').textContent = successes.length;
                    document.getElementById('statFailed').textContent = last.results.length - successes.length;
                    renderResults(last.results);
                }
            }
        } catch(e) { console.error('History error:', e); }
    }
</script>
</body>
</html>
"""


@app.route("/")
def index():
    return render_template_string(DASHBOARD_HTML)


@app.route("/api/plugins")
def api_plugins():
    discover_plugins()
    plugins = list_plugins()
    return jsonify([
        {"name": name, "default_port": cls.default_port}
        for name, cls in plugins.items()
    ])


@app.route("/api/scan", methods=["POST"])
def api_start_scan():
    global active_scan

    with scan_lock:
        if active_scan and active_scan.get("status") == "running":
            return jsonify({"error": "A scan is already running"}), 400

    data = request.json
    target = data.get("target", "").strip()
    protocol = data.get("protocol", "").strip()
    port_str = data.get("port", "")
    threads = data.get("threads", 10)
    usernames = data.get("usernames", [])
    passwords = data.get("passwords", [])
    stop_on_success = data.get("stop_on_success", False)

    if not target:
        return jsonify({"error": "Target is required"}), 400
    if not protocol:
        return jsonify({"error": "Protocol is required"}), 400
    if not usernames:
        return jsonify({"error": "At least one username is required"}), 400

    try:
        plugin = get_plugin(protocol)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400

    port = int(port_str) if port_str else plugin.default_port

    if not passwords:
        wordlist_path = Path(__file__).parent.parent / "wordlists" / "common.txt"
        if wordlist_path.exists():
            with open(wordlist_path, "r") as f:
                passwords = [line.strip() for line in f if line.strip()]
        else:
            return jsonify({"error": "No passwords provided and default wordlist not found"}), 400

    scan_id = "scan_" + str(int(time.time()))
    total_combos = len(usernames) * len(passwords)

    with scan_lock:
        active_scan = {
            "scan_id": scan_id,
            "status": "running",
            "target": target,
            "port": port,
            "protocol": protocol,
            "total": total_combos,
            "completed": 0,
            "successes": 0,
            "results": [],
            "new_results": [],
            "started_at": datetime.now().isoformat(),
        }

    def run_scan():
        global active_scan
        engine = Engine(
            plugin=plugin, threads=threads,
            stop_on_success=stop_on_success, verbose=False,
        )
        original_try = engine._try_credential

        def tracked_try(host, port, username, password):
            result = original_try(host, port, username, password)
            if result:
                with scan_lock:
                    active_scan["completed"] += 1
                    result_dict = result.to_dict()
                    active_scan["results"].append(result_dict)
                    if result.success:
                        active_scan["successes"] += 1
                        active_scan["new_results"].append(result_dict)
            return result

        engine._try_credential = tracked_try
        engine.run(host=target, port=port, usernames=usernames, passwords=passwords)

        with scan_lock:
            active_scan["status"] = "completed"
            scan_history.append(active_scan.copy())

    thread = threading.Thread(target=run_scan, daemon=True)
    thread.start()

    return jsonify({"scan_id": scan_id, "total": total_combos})


@app.route("/api/scan/<scan_id>")
def api_scan_status(scan_id):
    with scan_lock:
        if active_scan and active_scan["scan_id"] == scan_id:
            data = active_scan.copy()
            active_scan["new_results"] = []
            return jsonify(data)
    return jsonify({"error": "Scan not found"}), 404


@app.route("/api/scan/stop", methods=["POST"])
def api_stop_scan():
    global active_scan
    with scan_lock:
        if active_scan:
            active_scan["status"] = "completed"
    return jsonify({"status": "stopped"})


@app.route("/api/history")
def api_history():
    return jsonify(scan_history)


def start_dashboard(port=5000):
    discover_plugins()
    print("")
    print("    HYDRA Dashboard")
    print("    Running at: http://127.0.0.1:" + str(port))
    print("    Open this URL in your browser!")
    print("    Press Ctrl+C to stop.")
    print("")
    app.run(host="0.0.0.0", port=port, debug=False)
