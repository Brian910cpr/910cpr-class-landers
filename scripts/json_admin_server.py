from __future__ import annotations

import copy
import difflib
import json
import re
import shutil
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, Response


ROOT = Path(__file__).resolve().parents[1]
ALLOWLIST_PATH = ROOT / "data" / "config" / "json_editor_allowlist.json"
BACKUP_DIR = ROOT / "debug" / "backups" / "json-editor"
AUDIT_LOG_PATH = ROOT / "debug" / "json_editor_audit_log.jsonl"
CURATED_CATALOG_PATH = ROOT / "docs" / "data" / "course_catalog_map.json"

SECRET_VALUE_PATTERNS = [
    ("private ICS token", re.compile(r"private-[a-z0-9]{16,}", re.I)),
    ("private ICS URL", re.compile(r"https://calendar\.google\.com/calendar/ical/[^\"'\s]+/private-[^\"'\s]+/basic\.ics", re.I)),
    ("OpenAI-style API key", re.compile(r"sk-[A-Za-z0-9_-]{20,}")),
]
SENSITIVE_KEY_PATTERN = re.compile(r"(api[_-]?key|secret|token|password|credential)", re.I)

app = Flask(__name__)


def timestamp() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def repo_path(relative_path: str) -> Path:
    candidate = (ROOT / relative_path).resolve()
    if ROOT.resolve() != candidate and ROOT.resolve() not in candidate.parents:
        raise ValueError("Path escapes repository root.")
    return candidate


def load_allowlist() -> list[dict[str, Any]]:
    payload = json.loads(ALLOWLIST_PATH.read_text(encoding="utf-8"))
    entries = []
    seen: set[str] = set()
    for entry in payload.get("files", []):
        if not isinstance(entry, dict) or not entry.get("id") or not entry.get("path"):
            continue
        if entry["id"] in seen:
            continue
        seen.add(entry["id"])
        path = repo_path(str(entry["path"]))
        if entry.get("only_if_exists") and not path.exists():
            continue
        clean = dict(entry)
        clean["exists"] = path.exists()
        clean["relative_path"] = str(entry["path"]).replace("\\", "/")
        clean["size"] = path.stat().st_size if path.exists() else 0
        entries.append(clean)
    return entries


def allow_entry(file_id: str) -> dict[str, Any]:
    for entry in load_allowlist():
        if entry["id"] == file_id:
            return entry
    raise KeyError(f"File id is not allowlisted: {file_id}")


def load_json_file(entry: dict[str, Any]) -> Any:
    path = repo_path(entry["relative_path"])
    if not path.exists():
        return [] if entry["id"] == "course_catalog_map" else {}
    return json.loads(path.read_text(encoding="utf-8"))


def json_shape(data: Any) -> dict[str, Any]:
    if isinstance(data, dict):
        nested = any(isinstance(value, (dict, list)) for value in data.values())
        return {"type": "nested_object" if nested else "object", "keys": list(data.keys())[:200]}
    if isinstance(data, list):
        if not data:
            return {"type": "array_empty", "length": 0}
        object_count = sum(isinstance(item, dict) for item in data)
        primitive_count = sum(not isinstance(item, (dict, list)) for item in data)
        if object_count == len(data):
            keys = sorted({key for item in data for key in item.keys()})
            return {"type": "array_of_objects", "length": len(data), "keys": keys}
        if primitive_count == len(data):
            return {"type": "array_of_primitives", "length": len(data)}
        return {"type": "mixed_array", "length": len(data)}
    return {"type": type(data).__name__}


def looks_like_real_secret(value: str) -> bool:
    if not value:
        return False
    if re.fullmatch(r"[A-Z0-9_]{8,}", value):
        return False
    if value.startswith("$"):
        return False
    return len(value) >= 16 or "://" in value


def detect_secret_patterns(data: Any) -> list[str]:
    matches: set[str] = set()

    def walk(value: Any, path: str = "$") -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                child_path = f"{path}.{key}"
                if isinstance(child, str) and SENSITIVE_KEY_PATTERN.search(str(key)) and looks_like_real_secret(child):
                    matches.add(f"secret-like value at {child_path}")
                walk(child, child_path)
            return
        if isinstance(value, list):
            for index, child in enumerate(value):
                walk(child, f"{path}[{index}]")
            return
        if isinstance(value, str):
            for label, pattern in SECRET_VALUE_PATTERNS:
                if pattern.search(value):
                    matches.add(f"{label} at {path}")

    walk(data)
    return sorted(matches)


def changed_fields(old: Any, new: Any) -> list[str]:
    fields: set[str] = set()
    if isinstance(old, dict) and isinstance(new, dict):
        for key in set(old) | set(new):
            if old.get(key) != new.get(key):
                fields.add(str(key))
    elif isinstance(old, list) and isinstance(new, list):
        for index, (before, after) in enumerate(zip(old, new)):
            if before != after:
                if isinstance(before, dict) and isinstance(after, dict):
                    for key in set(before) | set(after):
                        if before.get(key) != after.get(key):
                            fields.add(str(key))
                else:
                    fields.add(f"[{index}]")
        if len(old) != len(new):
            fields.add("row_count")
    else:
        fields.add("$root")
    return sorted(fields)


def row_change_count(old: Any, new: Any) -> int:
    if isinstance(old, list) and isinstance(new, list):
        changed = abs(len(old) - len(new))
        changed += sum(1 for before, after in zip(old, new) if before != after)
        return changed
    return 1 if old != new else 0


def unified_diff(old: Any, new: Any, path: str) -> str:
    before = json.dumps(old, indent=2, ensure_ascii=False).splitlines()
    after = json.dumps(new, indent=2, ensure_ascii=False).splitlines()
    return "\n".join(difflib.unified_diff(before, after, fromfile=f"{path}:before", tofile=f"{path}:after", lineterm=""))


def backup_file(path: Path) -> str | None:
    if not path.exists():
        return None
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    backup_path = BACKUP_DIR / f"{path.stem}_{timestamp()}{path.suffix}"
    shutil.copy2(path, backup_path)
    return str(backup_path.relative_to(ROOT)).replace("\\", "/")


def write_audit(record: dict[str, Any]) -> None:
    AUDIT_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    with AUDIT_LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=False) + "\n")


def atomic_write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    tmp.replace(path)


def error(message: str, status: int = 400):
    response = jsonify({"ok": False, "error": message})
    response.status_code = status
    return response


@app.after_request
def no_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response


@app.route("/")
def index():
    return Response(INDEX_HTML, mimetype="text/html")


@app.route("/api/files")
def files():
    return jsonify({"ok": True, "files": load_allowlist()})


@app.route("/api/file/<file_id>")
def get_file(file_id: str):
    try:
        entry = allow_entry(file_id)
        data = load_json_file(entry)
        return jsonify({"ok": True, "file": entry, "shape": json_shape(data), "data": data, "secret_warnings": detect_secret_patterns(data)})
    except Exception as exc:
        return error(str(exc), 404)


@app.route("/api/file/<file_id>/diff", methods=["POST"])
def diff_file(file_id: str):
    try:
        entry = allow_entry(file_id)
        old = load_json_file(entry)
        new = request.get_json(force=True)
        json.dumps(new)
        return jsonify({
            "ok": True,
            "changed_row_count": row_change_count(old, new),
            "changed_fields": changed_fields(old, new),
            "secret_warnings": detect_secret_patterns(new),
            "diff": unified_diff(old, new, entry["relative_path"]),
        })
    except Exception as exc:
        return error(str(exc))


@app.route("/api/file/<file_id>", methods=["POST"])
def save_file(file_id: str):
    try:
        entry = allow_entry(file_id)
        if entry.get("mode") != "editable":
            return error("File is read-only.", 403)
        old = load_json_file(entry)
        new = request.get_json(force=True)
        json.dumps(new)
        secret_warnings = detect_secret_patterns(new)
        if secret_warnings and entry["relative_path"].startswith("docs/"):
            return error(f"Secret-like patterns detected in public docs file: {secret_warnings}", 400)
        path = repo_path(entry["relative_path"])
        backup_path = backup_file(path) if entry.get("backup_required", True) else None
        atomic_write_json(path, new)
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_path": entry["relative_path"],
            "changed_row_count": row_change_count(old, new),
            "changed_fields": changed_fields(old, new),
            "backup_path": backup_path,
            "user_action": request.headers.get("X-Json-Editor-Action", "save"),
            "validation_result": "ok",
            "secret_warnings": secret_warnings,
        }
        write_audit(audit)
        return jsonify({"ok": True, "audit": audit})
    except Exception as exc:
        return error(str(exc))


@app.route("/api/course-catalog/import", methods=["POST"])
def import_course_catalog():
    try:
        payload = request.get_json(force=True)
        rows = payload.get("rows", [])
        if not isinstance(rows, list):
            return error("rows must be an array")
        existing = []
        if CURATED_CATALOG_PATH.exists():
            existing = json.loads(CURATED_CATALOG_PATH.read_text(encoding="utf-8"))
            if not isinstance(existing, list):
                existing = []
        by_id = {str(item.get("course_id")): item for item in existing if isinstance(item, dict)}
        for row in rows:
            if not isinstance(row, dict):
                continue
            course_id = str(row.get("course_id") or row.get("courseId") or "").strip()
            course_name = str(row.get("course_name") or row.get("courseName") or row.get("name") or "").strip()
            if not course_id:
                continue
            by_id[course_id] = {
                **by_id.get(course_id, {}),
                "course_key": by_id.get(course_id, {}).get("course_key", ""),
                "course_id": course_id,
                "course_name": course_name,
                "display_name": by_id.get(course_id, {}).get("display_name", course_name),
                "hub_slug": by_id.get(course_id, {}).get("hub_slug", ""),
                "appointment_enabled": by_id.get(course_id, {}).get("appointment_enabled", False),
                "public_enabled": by_id.get(course_id, {}).get("public_enabled", False),
                "course_family": by_id.get(course_id, {}).get("course_family", ""),
                "notes": by_id.get(course_id, {}).get("notes", "review_needed"),
            }
        old = existing
        new = list(by_id.values())
        backup_path = backup_file(CURATED_CATALOG_PATH) if CURATED_CATALOG_PATH.exists() else None
        atomic_write_json(CURATED_CATALOG_PATH, new)
        audit = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "file_path": "docs/data/course_catalog_map.json",
            "changed_row_count": row_change_count(old, new),
            "changed_fields": changed_fields(old, new),
            "backup_path": backup_path,
            "user_action": "import_selected_course_ids",
            "validation_result": "ok",
        }
        write_audit(audit)
        return jsonify({"ok": True, "imported_count": len(rows), "audit": audit, "data": new})
    except Exception as exc:
        return error(str(exc))


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Local JSON Editor</title>
  <style>
    body{font-family:system-ui,-apple-system,Segoe UI,sans-serif;margin:0;background:#f5f7fb;color:#172033}
    header{padding:16px 20px;background:#172033;color:white}
    main{display:grid;grid-template-columns:300px 1fr;gap:16px;padding:16px}
    button,input,select,textarea{font:inherit}
    .panel{background:white;border:1px solid #d9e1ef;border-radius:8px;padding:12px}
    .file{display:block;width:100%;text-align:left;margin:0 0 8px;padding:8px;border:1px solid #d9e1ef;background:#fff;border-radius:6px}
    .file[aria-current=true]{border-color:#234fe5;background:#eef3ff}
    table{width:100%;border-collapse:collapse;font-size:13px}
    th,td{border-bottom:1px solid #e6ebf5;padding:6px;text-align:left;vertical-align:top}
    th{cursor:pointer;background:#f8fafc;position:sticky;top:0}
    textarea{width:100%;min-height:220px}
    .toolbar{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:10px}
    .danger{color:#a11212}
    .muted{color:#647084}
    .grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px}
    details{border:1px solid #e0e7f2;border-radius:6px;margin:6px 0;padding:6px}
    .field{display:grid;grid-template-columns:260px 1fr;gap:8px;align-items:center;margin:6px 0}
    .field input[type=text],.field input[type=number]{width:100%;box-sizing:border-box}
  </style>
</head>
<body>
<header><strong>Local/Admin JSON Editor</strong> <span class="muted">127.0.0.1 only - allowlisted files only</span></header>
<main>
  <aside class="panel">
    <h3>Files</h3>
    <div id="files"></div>
  </aside>
  <section class="panel">
    <div id="meta"></div>
    <div class="toolbar">
      <input id="search" placeholder="Search/filter rows">
      <button id="addRow">Add row</button>
      <button id="dupRows">Duplicate selected</button>
      <button id="delRows">Delete selected</button>
      <button id="bulkSet">Bulk set field</button>
      <button id="addField">Add field</button>
      <button id="bulkClear">Clear field</button>
      <button id="bulkCopy">Copy field</button>
      <button id="exportRows">Export selected</button>
      <button id="importCatalog">Import selected to catalog</button>
      <button id="diffBtn">Preview diff</button>
      <button id="saveBtn">Save</button>
    </div>
    <div id="warnings"></div>
    <div id="editor"></div>
    <pre id="diff"></pre>
  </section>
</main>
<script>
let current=null, data=null, shape=null, selected=new Set(), sortKey=null, sortAsc=true;
const $=id=>document.getElementById(id);
async function api(url,opt){const r=await fetch(url,opt);const j=await r.json();if(!j.ok)throw new Error(j.error||'Request failed');return j}
function esc(v){return String(v??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function loadFiles(){const j=await api('/api/files');$('files').innerHTML=j.files.map(f=>`<button class="file" data-id="${esc(f.id)}"><b>${esc(f.label)}</b><br><span class="muted">${esc(f.mode)} - ${esc(f.relative_path)}${f.exists?'':' (missing)'}</span></button>`).join('');document.querySelectorAll('.file').forEach(b=>b.onclick=()=>openFile(b.dataset.id))}
async function openFile(id){const j=await api('/api/file/'+id);current=j.file;data=j.data;shape=j.shape;selected.clear();$('diff').textContent='';render()}
function render(warnings=[]){document.querySelectorAll('.file').forEach(b=>b.setAttribute('aria-current', current&&b.dataset.id===current.id));$('meta').innerHTML=`<h2>${esc(current.label)}</h2><p>${esc(current.description)}</p><p><b>${esc(current.mode)}</b> ${esc(shape.type)} ${current.backup_required?'backup required':''}</p>`;$('warnings').innerHTML=warnings.map(w=>`<p class="danger">${esc(w)}</p>`).join('');$('importCatalog').style.display=(current&&current.id.startsWith('extracted_course_ids'))?'inline-block':'none';if(shape.type==='array_of_objects'||shape.type==='array_empty')renderTable();else renderTree()}
function filteredRows(){let rows=Array.isArray(data)?data:[];const q=$('search').value.toLowerCase();if(q)rows=rows.filter(r=>JSON.stringify(r).toLowerCase().includes(q));if(sortKey)rows=[...rows].sort((a,b)=>String(a[sortKey]??'').localeCompare(String(b[sortKey]??''))*(sortAsc?1:-1));return rows.map(r=>({r,i:data.indexOf(r)}))}
function renderTable(){const keys=[...new Set(data.flatMap(r=>Object.keys(r||{})))];const rows=filteredRows();$('editor').innerHTML=`<table><thead><tr><th></th>${keys.map(k=>`<th data-k="${esc(k)}">${esc(k)}</th>`).join('')}</tr></thead><tbody>${rows.map(({r,i})=>`<tr><td><input type="checkbox" data-sel="${i}" ${selected.has(i)?'checked':''}></td>${keys.map(k=>`<td><input data-row="${i}" data-field="${esc(k)}" value="${esc(r?.[k]??'')}"></td>`).join('')}</tr>`).join('')}</tbody></table>`;document.querySelectorAll('th[data-k]').forEach(th=>th.onclick=()=>{sortAsc=sortKey===th.dataset.k?!sortAsc:true;sortKey=th.dataset.k;renderTable()});document.querySelectorAll('[data-sel]').forEach(c=>c.onchange=()=>{c.checked?selected.add(+c.dataset.sel):selected.delete(+c.dataset.sel)});document.querySelectorAll('[data-row][data-field]').forEach(inp=>inp.onchange=()=>{data[+inp.dataset.row][inp.dataset.field]=parseValue(inp.value)})}
function parseValue(v){if(v==='true')return true;if(v==='false')return false;if(v==='null')return null;if(v!==''&&!isNaN(Number(v)))return Number(v);return v}
function getPath(path){return path.reduce((obj,key)=>obj?.[key],data)}
function setPath(path,value){let obj=data;for(let i=0;i<path.length-1;i++)obj=obj[path[i]];obj[path[path.length-1]]=value}
function renderNode(value,path,label){
  if(Array.isArray(value)){
    const body=value.map((item,i)=>renderNode(item,path.concat(i),`[${i}]`)).join('');
    return `<details open><summary>${esc(label)} array (${value.length})</summary>${body}<button data-add-array="${esc(path.join('.'))}">Add item</button></details>`;
  }
  if(value&&typeof value==='object'){
    const body=Object.keys(value).map(k=>renderNode(value[k],path.concat(k),k)).join('');
    return `<details open><summary>${esc(label)} object</summary>${body}<button data-add-object="${esc(path.join('.'))}">Add field</button></details>`;
  }
  const p=esc(JSON.stringify(path));
  if(typeof value==='boolean')return `<label class="field"><span>${esc(label)}</span><input data-path='${p}' type="checkbox" ${value?'checked':''}></label>`;
  if(typeof value==='number')return `<label class="field"><span>${esc(label)}</span><input data-path='${p}' type="number" value="${esc(value)}"></label>`;
  return `<label class="field"><span>${esc(label)}</span><input data-path='${p}' type="text" value="${esc(value??'')}"></label>`;
}
function bindTree(){
  document.querySelectorAll('[data-path]').forEach(inp=>inp.onchange=()=>{const p=JSON.parse(inp.dataset.path);setPath(p,inp.type==='checkbox'?inp.checked:parseValue(inp.value))});
  document.querySelectorAll('[data-add-object]').forEach(btn=>btn.onclick=()=>{const path=btn.dataset.addObject?btn.dataset.addObject.split('.').filter(Boolean):[];const obj=getPath(path);const key=prompt('New field name');if(key)obj[key]='';renderTree()});
  document.querySelectorAll('[data-add-array]').forEach(btn=>btn.onclick=()=>{const path=btn.dataset.addArray?btn.dataset.addArray.split('.').filter(Boolean):[];const arr=getPath(path);if(Array.isArray(arr))arr.push('');renderTree()});
}
function renderTree(){ $('editor').innerHTML=renderNode(data,[],'root')+`<h3>Raw JSON</h3><textarea id="raw">${esc(JSON.stringify(data,null,2))}</textarea>`;bindTree();$('raw').onchange=()=>{data=JSON.parse($('raw').value);renderTree()} }
$('search').oninput=()=>shape&&render();
$('addRow').onclick=()=>{if(!Array.isArray(data))return;data.push({});render()};
$('dupRows').onclick=()=>{[...selected].forEach(i=>data.push(JSON.parse(JSON.stringify(data[i]))));render()};
$('delRows').onclick=()=>{data=data.filter((_,i)=>!selected.has(i));selected.clear();render()};
$('bulkSet').onclick=()=>{const f=prompt('Field name');if(!f)return;const v=parseValue(prompt('Value')??'');selected.forEach(i=>data[i][f]=v);render()};
$('addField').onclick=()=>{const f=prompt('New field name');if(!f)return;const v=parseValue(prompt('Default value')??'');selected.forEach(i=>{if(!(f in data[i]))data[i][f]=v});render()};
$('bulkClear').onclick=()=>{const f=prompt('Field to clear');if(!f)return;selected.forEach(i=>delete data[i][f]);render()};
$('bulkCopy').onclick=()=>{const from=prompt('Copy from field');const to=prompt('Copy to field');if(!from||!to)return;selected.forEach(i=>data[i][to]=data[i][from]);render()};
$('exportRows').onclick=()=>{const out=[...selected].map(i=>data[i]);navigator.clipboard.writeText(JSON.stringify(out,null,2));alert('Selected rows copied as JSON')};
$('importCatalog').onclick=async()=>{const rows=[...selected].map(i=>data[i]);if(!rows.length)return alert('Select raw course rows first');const j=await api('/api/course-catalog/import',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({rows})});alert(`Imported ${j.imported_count} selected rows to course_catalog_map.json`)};
$('diffBtn').onclick=async()=>{const j=await api('/api/file/'+current.id+'/diff',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});$('diff').textContent=j.diff;render(j.secret_warnings||[])};
$('saveBtn').onclick=async()=>{if(current.mode!=='editable')return alert('Read only');const j=await api('/api/file/'+current.id,{method:'POST',headers:{'Content-Type':'application/json','X-Json-Editor-Action':'manual_save'},body:JSON.stringify(data)});alert('Saved. Backup: '+(j.audit.backup_path||'none'));openFile(current.id)};
loadFiles();
</script>
</body></html>"""


def main() -> int:
    app.run(host="127.0.0.1", port=5062, debug=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
