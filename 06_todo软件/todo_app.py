# -*- coding: utf-8 -*-
"""
轻量 Todo 工具 — PyWebView + HTML/CSS (Apple 风格)
"""

import webview
import json
import os
import sys
import datetime
import tempfile
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).parent
else:
    APP_DIR = Path(__file__).parent
DATA_FILE = APP_DIR / "todo_data.json"


# ═══════════ 数据管理 ═══════════
class DM:
    def __init__(self):
        self.d = {
            "tasks": [],
            "history": [],
            "settings": {
                "auto_start": False,
                "red_days": 3,
                "window_width": 310,
                "window_height": 420,
            },
        }
        self._load()

    def _load(self):
        if DATA_FILE.exists():
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    self.d.update(json.load(f))
            except:
                pass

    def _save(self):
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(self.d, f, ensure_ascii=False, indent=2)

    def tasks(self):
        return self.d.get("tasks", [])

    def hist(self):
        return self.d.get("history", [])

    def settings(self):
        return self.d.get("settings", {})

    def add(self, text):
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.d.setdefault("tasks", []).append(
            {"text": text, "done": False, "created_at": now}
        )
        self._sort()
        self._save()

    def toggle(self, i):
        self.d["tasks"][i]["done"] ^= 1
        self._sort()
        self._save()

    def delete(self, i):
        del self.d["tasks"][i]
        self._save()

    def clear_done(self):
        done = [t for t in self.d["tasks"] if t["done"]]
        if not done:
            return 0
        self.d["tasks"] = [t for t in self.d["tasks"] if not t["done"]]
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        for t in done:
            t["archived_at"] = now
        self.d.setdefault("history", []).extend(done)
        self._save()
        return len(done)

    def restore_one(self, i):
        if 0 <= i < len(self.d.get("history", [])):
            it = self.d["history"].pop(i)
            # 恢复时保留原始的created_at字段
            restored_task = {
                "text": it["text"],
                "done": True,
                "created_at": it.get(
                    "created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
            self.d["tasks"].append(restored_task)
            self._sort()
            self._save()
            return True
        return False

    def restore_all(self):
        h = self.d.get("history", [])
        c = len(h)
        for it in h:
            # 恢复时保留原始的created_at字段
            restored_task = {
                "text": it["text"],
                "done": True,
                "created_at": it.get(
                    "created_at", datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                ),
            }
            self.d["tasks"].append(restored_task)
        self.d["history"] = []
        self._sort()
        self._save()
        return c

    def clear_hist(self):
        self.d["history"] = []
        self._save()

    def update_setting(self, k, v):
        self.d.setdefault("settings", {})[k] = v
        self._save()

    def reorder_tasks(self, new_order):
        """重新排序任务，new_order是任务索引列表"""
        if len(new_order) == len(self.d["tasks"]):
            self.d["tasks"] = [self.d["tasks"][i] for i in new_order]
            self._save()

    def _sort(self):
        self.d["tasks"] = sorted(self.d["tasks"], key=lambda t: t["done"])


# ═══════════ 开机自启动 ═══════════
def set_auto(enabled):
    import winreg

    try:
        k = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_SET_VALUE,
        )
        if enabled:
            ep = sys.executable
            if ep.lower().endswith("python.exe") or ep.lower().endswith("pythonw.exe"):
                winreg.SetValueEx(
                    k,
                    "LightTodo",
                    0,
                    winreg.REG_SZ,
                    f'"{sys.executable}" "{os.path.abspath(__file__)}"',
                )
            else:
                winreg.SetValueEx(k, "LightTodo", 0, winreg.REG_SZ, f'"{ep}"')
        else:
            try:
                winreg.DeleteValue(k, "LightTodo")
            except:
                pass
        winreg.CloseKey(k)
    except:
        pass


# ═══════════ HTML 前端 ═══════════
HTML = r"""
<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
:root {
    --bg: #f5f5f7;
    --card: #ffffff;
    --border: #e5e5ea;
    --text: #1d1d1f;
    --dim: #86868b;
    --blue: #007aff;
    --blue-h: #3399ff;
    --green: #34c759;
    --red: #ff3b30;
    --radius: 10px;
    --shadow: 0 1px 3px rgba(0,0,0,0.08);
}

* { margin: 0; padding: 0; box-sizing: border-box; }
html, body {
    width: 100%; height: 100vh;
    font-family: "Microsoft YaHei", sans-serif;
    background: var(--bg);
    color: var(--text);
    overflow: hidden;
    user-select: none;
}

/* ═══ 主布局 (Flex 列) ═══ */
#app {
    display: flex; flex-direction: column;
    height: 100vh; width: 100%; max-width: 100vw;
    background: var(--bg);
}

/* ── 标题栏 (固定) ── */
#titlebar {
    display: flex; align-items: center;
    height: 42px; min-height: 42px;
    background: var(--card);
    padding: 0 14px;
    flex-shrink: 0;
    -webkit-app-region: drag;
    border-bottom: 1px solid var(--border);
}
#titlebar .title {
    font-size: 13px; font-weight: 700;
    color: var(--text);
}
#titlebar .btns {
    display: flex; gap: 12px;
    margin-left: auto;
    -webkit-app-region: no-drag;
}
#titlebar .btns span {
    font-size: 15px; color: var(--dim);
    cursor: pointer; padding: 2px;
    transition: color 0.15s;
}
#titlebar .btns span:hover { color: var(--blue); }
#titlebar .btns .cls:hover { color: var(--red); }

/* ── 任务列表 (可滚动) ── */
#list-wrap {
    flex: 1; overflow-y: auto;
    padding: 8px 8px 4px 8px;
    display: flex; flex-direction: column; gap: 3px;
}
#list-wrap::-webkit-scrollbar { width: 4px; }
#list-wrap::-webkit-scrollbar-thumb {
    background: #ccc; border-radius: 2px;
}

.task-card {
    background: var(--card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 10px 12px;
    display: flex; align-items: center; gap: 8px;
    font-size: 13px;
    box-shadow: var(--shadow);
    cursor: default;
    user-select: none;
    transition: opacity 0.2s, transform 0.2s, background 0.2s;
}
.task-card[draggable="true"] { cursor: move; }
.task-card:hover { background: #fafafa; }
.task-card[draggable="true"]:active { transform: scale(1.02); }
.task-card .check {
    width: 20px; height: 20px;
    border-radius: 50%;
    border: 2px solid var(--dim);
    color: var(--dim);
    font-size: 12px; line-height: 18px;
    text-align: center;
    cursor: pointer; flex-shrink: 0;
    transition: all 0.2s;
}
.task-card.done .check {
    border-color: var(--green);
    background: var(--green);
    color: white;
}
.task-card .text {
    flex: 1; min-width: 0;
    overflow: hidden;
    white-space: nowrap; text-overflow: ellipsis;
}
.task-card.done .text {
    text-decoration: line-through;
    color: var(--dim);
}
.task-card .expand {
    color: transparent; font-size: 12px;
    cursor: pointer; flex-shrink: 0;
    padding: 0 2px;
}
.task-card:hover .expand { color: var(--blue); }
.task-card .expand:hover { color: var(--blue-h); }

.task-card .del {
    color: transparent; font-size: 13px;
    cursor: pointer; flex-shrink: 0;
    transition: color 0.15s;
    margin-left: auto;
}
.task-card:hover .del { color: var(--dim); }
.task-card .del:hover { color: var(--red) !important; }

.task-meta {
    display: flex; flex-direction: column; gap: 2px;
    align-items: flex-end; flex-shrink: 0;
    margin-left: 8px;
}

.task-time {
    font-size: 11px; color: var(--dim);
    white-space: nowrap;
}

.task-days {
    font-size: 11px; color: var(--dim);
    white-space: nowrap;
}

.task-days.days-old {
    color: var(--red); font-weight: 600;
}

/* ── 输入栏 (固定) ── */
#input-bar {
    display: flex; gap: 6px; align-items: center;
    padding: 0 8px 6px 8px;
    flex-shrink: 0;
}
#input-bar input {
    flex: 1; border: 1px solid var(--border);
    border-radius: 8px; padding: 8px 12px;
    font-size: 13px; background: var(--card);
    color: var(--text); outline: none;
    transition: border-color 0.2s;
    user-select: text; -webkit-user-select: text;
}
#input-bar input:focus { border-color: var(--blue); }
#input-bar input::placeholder { color: var(--dim); }

.btn-add {
    background: var(--blue); color: white;
    border: none; border-radius: 8px;
    font-size: 15px; font-weight: 700;
    padding: 7px 14px; cursor: pointer;
    transition: background 0.15s;
}
.btn-add:hover { background: var(--blue-h); }

/* ── 底部操作栏 (固定) ── */
#actions {
    display: flex; gap: 6px; align-items: center;
    padding: 0 8px 10px 8px;
    flex-shrink: 0;
}
.btn-act {
    flex: 1; text-align: center;
    padding: 8px 0; font-size: 12px;
    border: 1px solid var(--border);
    border-radius: 8px; background: var(--card);
    color: var(--dim); cursor: pointer;
    transition: all 0.15s;
}
.btn-act:hover { background: #f0f0f5; }
.btn-act.primary { color: var(--blue); }
#count {
    font-size: 11px; color: var(--dim);
    margin-left: 8px; white-space: nowrap;
    flex-shrink: 0;
}

/* ═══ Toast 轻提示 ═══ */
#toast {
    position: fixed; top: 16px; left: 50%;
    transform: translateX(-50%);
    background: #1d1d1f; color: white;
    padding: 8px 20px; border-radius: 20px;
    font-size: 12px; z-index: 200;
    opacity: 0; transition: opacity 0.25s;
    pointer-events: none;
}
#toast.show { opacity: 1; }

/* ═══ Modal 覆盖层 ═══ */
.modal-overlay {
    display: none; position: fixed;
    inset: 0; background: rgba(0,0,0,0.3);
    z-index: 100; justify-content: center;
    align-items: center;
}
.modal-overlay.show { display: flex; }

.modal-card {
    background: var(--card); width: 300px;
    max-height: 360px; border-radius: 14px;
    box-shadow: 0 8px 32px rgba(0,0,0,0.18);
    display: flex; flex-direction: column;
    overflow: hidden;
}
.modal-card.large { width: 290px; max-height: 70vh; min-height: 200px; }

.modal-header {
    display: flex; align-items: center;
    justify-content: center;
    padding: 14px; position: relative;
    border-bottom: 1px solid var(--border);
    font-size: 14px; font-weight: 700;
    flex-shrink: 0;
}
.modal-header .close {
    position: absolute; right: 14px;
    font-size: 16px; color: var(--dim);
    cursor: pointer;
}
.modal-header .close:hover { color: var(--red); }

.modal-body {
    flex: 1 1 auto; overflow-y: auto; overflow-x: hidden;
    padding: 12px 16px;
    min-height: 0;
}
.modal-body::-webkit-scrollbar { width: 4px; }
.modal-body::-webkit-scrollbar-thumb {
    background: #ccc; border-radius: 2px;
}

.modal-footer {
    border-top: 1px solid var(--border);
    padding: 10px 16px;
    display: flex; gap: 8px;
    flex-shrink: 0;
}

.setting-row {
    display: flex; align-items: center;
    justify-content: space-between;
    padding: 12px 0;
}
.setting-row + .setting-row { border-top: 1px solid var(--border); }
.setting-row .label { font-size: 13px; }

/* Toggle 开关 */
.toggle-switch {
    width: 46px; height: 28px;
    background: #e5e5ea; border-radius: 14px;
    position: relative; cursor: pointer;
    transition: background 0.25s;
    flex-shrink: 0;
}
.toggle-switch.on { background: var(--green); }
.toggle-switch::after {
    content: ''; position: absolute;
    width: 24px; height: 24px;
    border-radius: 50%; background: white;
    top: 2px; left: 2px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.2);
    transition: left 0.25s;
}
.toggle-switch.on::after { left: 20px; }

/* 滑块 */
input[type=range] {
    -webkit-appearance: none; width: 120px;
    height: 4px; background: #e5e5ea;
    border-radius: 2px; outline: none;
}
input[type=range]::-webkit-slider-thumb {
    -webkit-appearance: none;
    width: 20px; height: 20px; border-radius: 50%;
    background: var(--blue); cursor: pointer;
    box-shadow: 0 1px 4px rgba(0,0,0,0.2);
}

.hist-table { width: 100%; border-collapse: collapse; table-layout: fixed; }
.hist-table td { padding: 4px 6px; vertical-align: middle; overflow: hidden; }
.hist-table .htext {
    text-decoration: line-through;
    color: var(--dim); font-size: 13px;
    overflow: hidden; white-space: nowrap; text-overflow: ellipsis;
    max-width: 260px; display: block;
}
.hist-table .rbtn {
    color: var(--blue); cursor: pointer;
    font-size: 12px; text-align: right; width: 36px;
}
.hist-table .rbtn:hover { text-decoration: underline; }
.hist-time { font-size: 10px; color: var(--dim); margin: 6px 0 4px 4px; font-weight: 700; }

.btn {
    flex: 1; text-align: center; padding: 9px 0;
    border-radius: 8px; font-size: 12px; font-weight: 700;
    cursor: pointer; border: none;
}
.btn.blue { background: var(--blue); color: white; }
.btn.blue:hover { background: var(--blue-h); }
.btn.red { background: var(--red); color: white; }
.btn.red:hover { background: #ff6b60; }

.empty-msg { text-align: center; color: var(--dim); padding: 30px 0; font-size: 13px; }

#resize-handle {
    position: fixed; bottom: 0; right: 0;
    width: 14px; height: 14px;
    cursor: se-resize; background: linear-gradient(135deg, transparent 50%, var(--dim) 50%);
    opacity: 0.3; z-index: 1000; pointer-events: all;
    transition: opacity 0.2s;
}
#resize-handle:hover { opacity: 0.6; }
</style>
</head>
<body>

<div id="app">
    <!-- 标题栏 -->
    <div id="titlebar">
        <span class="title">📝 待办事项</span>
        <div class="btns">
            <span onclick="openSettings()" title="设置">⚙</span>
            <span onclick="pywebview.api.minimize()" title="最小化">─</span>
            <span class="cls" onclick="pywebview.api.close()" title="关闭">✕</span>
        </div>
    </div>

    <!-- 任务列表 -->
    <div id="list-wrap"></div>

    <!-- 输入栏 -->
    <div id="input-bar">
        <input id="task-input" type="text" placeholder="添加新任务..." onkeydown="if(event.key==='Enter')add()">
        <button class="btn-add" onclick="add()">+</button>
    </div>

    <!-- 底部操作 -->
    <div id="actions">
        <div class="btn-act" onclick="clearDone()">清空已完成</div>
        <div class="btn-act primary" onclick="openHistory()">历史记录</div>
        <span id="count"></span>
    </div>
    
    <!-- 调整大小把手 -->
    <div id="resize-handle"></div>
</div>

<!-- Toast 提示 -->
<div id="toast"></div>

<!-- ═══ 设置 Modal ═══ -->
<div id="settings-modal" class="modal-overlay">
    <div class="modal-card">
        <div class="modal-header">
            ⚙ 设置
            <span class="close" onclick="closeSettings()">✕</span>
        </div>
        <div class="modal-body">
            <div class="setting-row">
                <span class="label">开机自启动</span>
                <div class="toggle-switch" id="auto-toggle" onclick="toggleAuto()"></div>
            </div>
            <div class="setting-row">
                <span class="label">逾期天数提醒</span>
                <div style="display: flex; align-items: center; gap: 10px;">
                    <input type="range" id="red-days-slider" min="1" max="30" value="3" oninput="updateRedDays(this.value)" onchange="updateRedDays(this.value)">
                    <span id="red-days-value" style="font-size: 13px; min-width: 30px;">3</span>
                </div>
            </div>
            <div style="text-align:center;padding:16px 0 4px;font-size:11px;color:var(--dim);">
                made by vv<br>vvdevpro@gmail.com
            </div>
        </div>
    </div>
</div>

<!-- ═══ 历史记录 Modal ═══ -->
<div id="history-modal" class="modal-overlay">
  <div class="modal-card large">
    <div class="modal-header">
      📋 历史记录
      <span class="close" onclick="closeHistory()">✕</span>
    </div>
    <div class="modal-body" id="history-body"></div>
    <div class="modal-footer">
      <button class="btn blue" onclick="restoreAll()">恢复全部</button>
      <button class="btn red" onclick="clearHistory()">清空历史</button>
    </div>
  </div>
</div>

<!-- ═══ 详情/编辑弹窗 ═══ -->
<div id="detail-modal" class="modal-overlay" onclick="closeDetail()">
    <div class="modal-card" style="max-height:150vh;width:300px;" onclick="event.stopPropagation()">
        <div class="modal-header">
            待办详情
            <span class="close" onclick="closeDetail()">✕</span>
        </div>
        <div class="modal-body" style="padding:16px;">
            <textarea id="detail-textarea" style="width:100%;height:120px;border:1px solid var(--border);border-radius:8px;padding:10px;font-size:13px;font-family:inherit;color:var(--text);background:var(--bg);outline:none;resize:none;user-select:text;-webkit-user-select:text;"></textarea>
        </div>
        <div class="modal-footer">
            <button class="btn" style="background:#e5e5ea;color:var(--text);" onclick="closeDetail()">取消</button>
            <button class="btn blue" onclick="saveDetail()">保存</button>
        </div>
    </div>
</div>

<!-- ═══ 确认弹窗 ═══ -->
<div id="confirm-modal" class="modal-overlay">
    <div class="modal-card" style="max-height:none;width:280px;">
        <div class="modal-header">确认</div>
        <div class="modal-body" style="text-align:center;padding:20px 16px;">
            <span id="confirm-msg" style="font-size:13px;color:var(--text);"></span>
        </div>
        <div class="modal-footer">
            <button class="btn" style="background:#e5e5ea;color:var(--text);" onclick="confirmNo()">取消</button>
            <button class="btn red" onclick="confirmYes()">确定</button>
        </div>
    </div>
</div>

<script>
// ═══════ 全局状态 ═══════
let tasks = [];
let settings = {};

// ═══════ 初始化 ═══════
async function init() {
    tasks = await pywebview.api.get_tasks();
    settings = await pywebview.api.get_settings();
    render();
    document.getElementById('auto-toggle').classList.toggle('on', settings.auto_start);
    // 初始化红字天数滑块
    let redDays = settings.red_days || 3;
    document.getElementById('red-days-slider').value = redDays;
    document.getElementById('red-days-value').textContent = redDays;
    
    // 初始化窗口大小调整把手
    let resizeHandle = document.getElementById('resize-handle');
    if (resizeHandle) {
        resizeHandle.addEventListener('mousedown', function(e) {
            isResizing = true;
            startX = e.screenX;
            startY = e.screenY;
            startWidth = window.innerWidth;
            startHeight = window.innerHeight;
            e.preventDefault();
        });
    }
}
window.addEventListener('pywebviewready', init);

// ═══════ 渲染 ═══════
function getDaysDiff(createdAt) {
    if (!createdAt) return null;
    let created = new Date(createdAt);
    let today = new Date();
    let diff = Math.floor((today - created) / (1000 * 60 * 60 * 24));
    return diff > 0 ? diff : null;
}

function render() {
    let redDaysThreshold = settings.red_days || 3;
    let html = '';
    tasks.forEach((t, i) => {
        // 只为未完成的任务计算逾期时间
        let daysDiff = !t.done ? getDaysDiff(t.created_at) : null;
        let timeDisplay = t.created_at ? t.created_at.substring(0, 10) : '';
        // 只有超过阈值时才显示逾期提醒
        let isOld = daysDiff && daysDiff >= redDaysThreshold;
        let daysStr = isOld ? `已过 ${daysDiff} 天` : '';
        let daysClass = isOld ? 'days-old' : '';
        let isDraggable = !t.done; // 只有未完成的任务可以拖拽
        
        html += `<div class="task-card ${t.done ? 'done' : ''}" ${isDraggable ? `draggable="true" ondragstart="dragStart(event, ${i})" ondragover="dragOver(event)" ondrop="dragDrop(event, ${i})" ondragend="dragEnd(event)"` : ''} ondblclick="${t.done ? `toggle(${i})` : ''}">
            <div class="check" onclick="toggle(${i})">${t.done ? '✓' : ''}</div>
            <div class="text" title="${esc(t.text)}" onclick="openDetail(${i})" style="cursor:pointer;">${trunc(esc(t.text), 18)}</div>
            <div class="task-meta">
                <div class="task-time">${timeDisplay}</div>
                ${daysStr ? `<div class="task-days ${daysClass}">${daysStr}</div>` : ''}
            </div>
            <div class="del" onclick="del(${i})">✕</div>
        </div>`;
    });
    document.getElementById('list-wrap').innerHTML = html || '<div class="empty-msg">暂无任务，添加一个吧 ✨</div>';
    let doneCount = tasks.filter(t => t.done).length;
    document.getElementById('count').textContent = `${tasks.length} 条  ${doneCount} 已完成`;
}

function esc(s) {
    let d = document.createElement('div');
    d.textContent = s;
    return d.innerHTML;
}

function trunc(s, max) {
    return s.length > max ? s.substring(0, max) + '…' : s;
}

let currentDetailIdx = -1;

function openDetail(idx) {
    currentDetailIdx = idx;
    document.getElementById('detail-textarea').value = tasks[idx] ? tasks[idx].text : '';
    document.getElementById('detail-modal').classList.add('show');
}
function closeDetail() {
    currentDetailIdx = -1;
    document.getElementById('detail-modal').classList.remove('show');
}
async function saveDetail() {
    let t = document.getElementById('detail-textarea').value.trim();
    if (!t || currentDetailIdx < 0) { closeDetail(); return; }
    await pywebview.api.update_task(currentDetailIdx, t);
    tasks = await pywebview.api.get_tasks();
    render();
    closeDetail();
}
function showHistoryDetail(text) {
    currentDetailIdx = -1;
    document.getElementById('detail-textarea').value = text;
    document.getElementById('detail-modal').classList.add('show');
}

// ═══════ 操作 ═══════
async function add() {
    let inp = document.getElementById('task-input');
    let text = inp.value.trim();
    if (!text) return;
    await pywebview.api.add_task(text);
    inp.value = '';
    tasks = await pywebview.api.get_tasks();
    render();
}

async function toggle(idx) {
    await pywebview.api.toggle_task(idx);
    tasks = await pywebview.api.get_tasks();
    render();
}

async function del(idx) {
    await pywebview.api.delete_task(idx);
    tasks = await pywebview.api.get_tasks();
    render();
}

function toast(msg) {
    let el = document.getElementById('toast');
    el.textContent = msg;
    el.classList.add('show');
    clearTimeout(el._t);
    el._t = setTimeout(() => el.classList.remove('show'), 1800);
}

async function clearDone() {
    let n = await pywebview.api.clear_done();
    if (n) toast('已归档 ' + n + ' 条任务');
    tasks = await pywebview.api.get_tasks();
    render();
}

// ═══════ 历史 ═══════
async function openHistory() {
    let hist = await pywebview.api.get_history();
    let body = document.getElementById('history-body');
    if (hist.length === 0) {
        body.innerHTML = '<div class="empty-msg">暂无历史记录</div>';
    } else {
        let groups = {};
        hist.forEach((it, i) => {
            let at = it.archived_at || '未知时间';
            if (!groups[at]) groups[at] = [];
            groups[at].push({...it, _idx: i});
        });
        let html = '';
        Object.entries(groups).sort((a,b) => b[0].localeCompare(a[0])).forEach(([time, items]) => {
            html += `<div class="hist-time">${time}</div>
            <table class="hist-table">`;
            items.forEach(it => {
                html += `<tr>
                    <td class="htext" title="${esc(it.text)}">${trunc(esc(it.text), 16)}${it.text.length > 16 ? ' <span class="rbtn" style="margin-left:4px" onclick="showDetail(this.parentElement.querySelector(\'.htext\').title)">查看</span>' : ''}</td>
                    <td class="rbtn" onclick="restoreOne(${it._idx})">恢复</td>
                </tr>`;
            });
            html += '</table><br>';
        });
        body.innerHTML = html;
    }
    document.getElementById('history-modal').classList.add('show');
}

function closeHistory() { document.getElementById('history-modal').classList.remove('show'); }

async function restoreOne(idx) {
    await pywebview.api.restore_one(idx);
    tasks = await pywebview.api.get_tasks();
    render();
    openHistory();
}

async function restoreAll() {
    let n = await pywebview.api.restore_all();
    if (n) toast('已恢复 ' + n + ' 条任务');
    tasks = await pywebview.api.get_tasks();
    render();
    closeHistory();
}

async function clearHistory() {
    if (!await showConfirm('永久删除所有历史记录？')) return;
    await pywebview.api.clear_history();
    closeHistory();
}

// ═══════ 自定义确认弹窗 ═══════
function showConfirm(msg) {
    return new Promise(resolve => {
        document.getElementById('confirm-msg').textContent = msg;
        let modal = document.getElementById('confirm-modal');
        modal.classList.add('show');
        modal._resolve = resolve;
    });
}
function confirmYes() {
    let m = document.getElementById('confirm-modal');
    m.classList.remove('show');
    if (m._resolve) { m._resolve(true); m._resolve = null; }
}
function confirmNo() {
    let m = document.getElementById('confirm-modal');
    m.classList.remove('show');
    if (m._resolve) { m._resolve(false); m._resolve = null; }
}

// ═══════ 设置 ═══════
function openSettings() { document.getElementById('settings-modal').classList.add('show'); }
function closeSettings() { document.getElementById('settings-modal').classList.remove('show'); }

async function toggleAuto() {
    settings.auto_start = !settings.auto_start;
    await pywebview.api.update_setting('auto_start', settings.auto_start);
    document.getElementById('auto-toggle').classList.toggle('on', settings.auto_start);
}

async function updateRedDays(value) {
    settings.red_days = parseInt(value);
    document.getElementById('red-days-value').textContent = value;
    await pywebview.api.update_setting('red_days', settings.red_days);
    render(); // 重新渲染以更新红字显示
}

// ═══════ 任务拖拽排序 ═══════
let draggedIdx = -1;

function dragStart(e, idx) {
    draggedIdx = idx;
    e.dataTransfer.effectAllowed = 'move';
    e.target.style.opacity = '0.5';
}

function dragOver(e) {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
}

async function dragDrop(e, targetIdx) {
    e.preventDefault();
    if (draggedIdx === targetIdx || draggedIdx === -1) return;
    
    // 交换任务位置
    let newOrder = tasks.map((_, i) => i);
    let temp = newOrder[draggedIdx];
    newOrder[draggedIdx] = newOrder[targetIdx];
    newOrder[targetIdx] = temp;
    
    await pywebview.api.reorder_tasks(newOrder);
    tasks = await pywebview.api.get_tasks();
    render();
}

function dragEnd(e) {
    e.target.style.opacity = '1';
    draggedIdx = -1;
}

// ═══════ 窗口拖拽 ═══════
let dragging = false, startMX = 0, startMY = 0, startWX = 0, startWY = 0;
document.getElementById('titlebar').addEventListener('mousedown', async function(e) {
    if (e.target.closest('.btns')) return;
    dragging = true;
    startMX = e.screenX;
    startMY = e.screenY;
    let pos = await pywebview.api.get_window_pos();
    startWX = pos[0]; startWY = pos[1];
});
document.addEventListener('mousemove', function(e) {
    if (!dragging) return;
    pywebview.api.move_absolute(
        startWX + e.screenX - startMX,
        startWY + e.screenY - startMY
    );
});
document.addEventListener('mouseup', function() { dragging = false; });

// ═══════ 窗口大小拖拽调整 ═══════
let isResizing = false, startX = 0, startY = 0, startWidth = 0, startHeight = 0;

document.addEventListener('mousemove', async function(e) {
    if (!isResizing) return;
    let newWidth = Math.max(280, startWidth + e.screenX - startX);
    let newHeight = Math.max(300, startHeight + e.screenY - startY);
    
    // 调用 API 调整窗口大小并保存
    await pywebview.api.set_window_size(newWidth, newHeight);
});

document.addEventListener('mouseup', function() { isResizing = false; });
</script>
</body>
</html>
"""


# ═══════════ Python API ═══════════
class TodoAPI:
    def __init__(self):
        self.dm = DM()
        self._window = None

    def set_window(self, w):
        self._window = w

    def get_tasks(self):
        return self.dm.tasks()

    def get_history(self):
        return self.dm.hist()

    def get_settings(self):
        return self.dm.settings()

    def add_task(self, text):
        self.dm.add(text)

    def toggle_task(self, idx):
        self.dm.toggle(idx)

    def update_task(self, idx, text):
        if 0 <= idx < len(self.dm.tasks()):
            self.dm.tasks()[idx]["text"] = text
            self.dm._save()

    def delete_task(self, idx):
        self.dm.delete(idx)

    def clear_done(self):
        return self.dm.clear_done()

    def restore_one(self, idx):
        return self.dm.restore_one(idx)

    def restore_all(self):
        return self.dm.restore_all()

    def clear_history(self):
        self.dm.clear_hist()

    def update_setting(self, key, value):
        self.dm.update_setting(key, value)
        if key == "auto_start":
            set_auto(value)

    def reorder_tasks(self, new_order):
        """接收前端的新任务顺序"""
        self.dm.reorder_tasks(new_order)

    def get_window_pos(self):
        if self._window:
            return [self._window.x, self._window.y]
        return [0, 0]

    def move_absolute(self, x, y):
        if self._window:
            self._window.move(int(x), int(y))

    def set_window_size(self, width, height):
        """调整和保存窗口大小"""
        try:
            if self._window:
                # 尝试使用 resize 方法调整窗口大小
                self._window.resize(int(width), int(height))
        except Exception:
            # 如果 resize 方法不可用，继续正常运行
            pass
        self.dm.update_setting("window_width", int(width))
        self.dm.update_setting("window_height", int(height))

    def minimize(self):
        if self._window:
            self._window.minimize()

    def close(self):
        if self._window:
            self._window.destroy()


def main():
    api = TodoAPI()

    # 获取屏幕尺寸，计算右上角位置
    import tkinter as tk

    root = tk.Tk()
    root.withdraw()
    sw = root.winfo_screenwidth()
    root.destroy()

    # 读取保存的窗口大小
    settings = api.dm.settings()
    w = settings.get("window_width", 310)
    h = settings.get("window_height", 420)

    x_pos = sw - w - 20
    y_pos = 20

    window = webview.create_window(
        title="Todo",
        html=HTML,
        js_api=api,
        width=w,
        height=h,
        x=x_pos,
        y=y_pos,
        frameless=True,
        on_top=True,
        easy_drag=False,
        focus=True,
    )
    api.set_window(window)
    webview.start(debug=False, gui="edgechromium")


if __name__ == "__main__":
    main()
