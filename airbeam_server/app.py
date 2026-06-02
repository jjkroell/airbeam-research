"""
AirBeam Research Server
-----------------------
Run with:  python app.py
Requires:  pip install flask flask-cors

All data is stored in airbeam.db (SQLite) in the same folder.
"""

from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, json, os

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

DB = os.path.join(os.path.dirname(__file__), "airbeam.db")

# ── Database setup ────────────────────────────────────────────────────────────
def get_db():
    con = sqlite3.connect(DB)
    con.row_factory = sqlite3.Row
    return con

def init_db():
    with get_db() as con:
        con.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sheet     TEXT UNIQUE,
            category  TEXT,
            name      TEXT,
            date      TEXT,
            time      TEXT,
            trial     INTEGER DEFAULT 0,
            location  TEXT DEFAULT '',
            iv1       TEXT DEFAULT '',
            iv2       TEXT DEFAULT '',
            iv3       TEXT DEFAULT '',
            iv4       TEXT DEFAULT '',
            pm1       REAL,
            pm25      REAL,
            pm10      REAL,
            temp      REAL,
            humidity  REAL,
            notes     TEXT DEFAULT '',
            max_pm25  REAL,
            time_series TEXT DEFAULT '[]',
            note_markers TEXT DEFAULT '[]',
            note_photos  TEXT DEFAULT '[]'
        );

        CREATE TABLE IF NOT EXISTS scenarios (
            category TEXT PRIMARY KEY,
            scenario TEXT DEFAULT ''
        );

        CREATE TABLE IF NOT EXISTS custom_categories (
            name TEXT PRIMARY KEY,
            hex  TEXT,
            text_color TEXT,
            icon TEXT
        );
        """)
    print("Database ready:", DB)

init_db()

# ── Static files ──────────────────────────────────────────────────────────────
@app.route("/")
def index():
    return send_from_directory("templates", "index.html")

# ── Sessions API ──────────────────────────────────────────────────────────────
@app.route("/api/sessions", methods=["GET"])
def get_sessions():
    with get_db() as con:
        rows = con.execute("SELECT * FROM sessions ORDER BY category, trial").fetchall()
    sessions = []
    for r in rows:
        s = dict(r)
        s["timeSeries"]   = json.loads(s.pop("time_series",  "[]") or "[]")
        s["noteMarkers"]  = json.loads(s.pop("note_markers", "[]") or "[]")
        s["notePhotos"]   = json.loads(s.pop("note_photos",  "[]") or "[]")
        s["maxPm25"]      = s.pop("max_pm25", None)
        sessions.append(s)
    return jsonify(sessions)

@app.route("/api/sessions", methods=["POST"])
def upsert_sessions():
    """Bulk upsert sessions (called when uploading merged_sessions.xlsx)"""
    data = request.get_json()
    sessions = data if isinstance(data, list) else [data]
    with get_db() as con:
        for s in sessions:
            con.execute("""
                INSERT INTO sessions
                  (sheet,category,name,date,time,trial,location,iv1,iv2,iv3,iv4,
                   pm1,pm25,pm10,temp,humidity,notes,max_pm25,time_series,note_markers,note_photos)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(sheet) DO UPDATE SET
                  time_series=excluded.time_series,
                  note_markers=excluded.note_markers,
                  category=excluded.category,
                  name=excluded.name,
                  date=excluded.date,
                  time=excluded.time,
                  trial=excluded.trial,
                  pm1=excluded.pm1,
                  pm25=excluded.pm25,
                  pm10=excluded.pm10,
                  temp=excluded.temp,
                  humidity=excluded.humidity,
                  max_pm25=excluded.max_pm25
            """, (
                s.get("sheet"), s.get("category"), s.get("name"),
                s.get("date"), s.get("time"), s.get("trial",""),
                s.get("location",""), s.get("iv1",""), s.get("iv2",""),
                s.get("iv3",""), s.get("iv4",""),
                s.get("pm1"), s.get("pm25"), s.get("pm10"),
                s.get("temp"), s.get("humidity"), s.get("notes",""),
                s.get("maxPm25"), 
                json.dumps(s.get("timeSeries",[])),
                json.dumps(s.get("noteMarkers",[])),
                json.dumps(s.get("notePhotos",[]))
            ))
        # Recalculate trial numbers after bulk insert
        _recalc_trials(con)
    return jsonify({"ok": True})

@app.route("/api/sessions/<int:sid>", methods=["PUT"])
def update_session(sid):
    """Update a single session's editable fields — only updates fields that are present in the request"""
    s = request.get_json()
    with get_db() as con:
        # Fetch existing row first
        row = con.execute("SELECT * FROM sessions WHERE id=?", (sid,)).fetchone()
        if not row:
            return jsonify({"ok": False, "error": "Not found"}), 404
        existing = dict(row)
        # Only update fields that were actually sent
        con.execute("""
            UPDATE sessions SET
              location=?, iv1=?, iv2=?, iv3=?, iv4=?,
              notes=?, trial=?, note_photos=?,
              pm1=?, pm25=?, pm10=?, temp=?, humidity=?
            WHERE id=?
        """, (
            s.get("location", existing.get("location","")),
            s.get("iv1",     existing.get("iv1","")),
            s.get("iv2",     existing.get("iv2","")),
            s.get("iv3",     existing.get("iv3","")),
            s.get("iv4",     existing.get("iv4","")),
            s.get("notes",   existing.get("notes","")),
            s.get("trial",   existing.get("trial","")),
            json.dumps(s.get("notePhotos", json.loads(existing.get("note_photos","[]") or "[]"))),
            s.get("pm1",     existing.get("pm1")),
            s.get("pm25",    existing.get("pm25")),
            s.get("pm10",    existing.get("pm10")),
            s.get("temp",    existing.get("temp")),
            s.get("humidity",existing.get("humidity")),
            sid
        ))
    return jsonify({"ok": True})

@app.route("/api/sessions/<int:sid>", methods=["DELETE"])
def delete_session(sid):
    with get_db() as con:
        con.execute("DELETE FROM sessions WHERE id=?", (sid,))
    return jsonify({"ok": True})

@app.route("/api/sessions/new", methods=["POST"])
def add_session():
    """Add a manually created session"""
    s = request.get_json()
    with get_db() as con:
        cur = con.execute("""
            INSERT INTO sessions
              (sheet,category,name,date,time,trial,location,iv1,iv2,iv3,iv4,
               pm1,pm25,pm10,temp,humidity,notes,max_pm25,time_series,note_markers,note_photos)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, (
            s.get("sheet", "manual_"+str(os.urandom(4).hex())),
            s.get("category"), s.get("name",""),
            s.get("date"), s.get("time"), s.get("trial",""),
            s.get("location",""), s.get("iv1",""), s.get("iv2",""),
            s.get("iv3",""), s.get("iv4",""),
            s.get("pm1"), s.get("pm25"), s.get("pm10"),
            s.get("temp"), s.get("humidity"), s.get("notes",""),
            s.get("maxPm25"),
            json.dumps([]), json.dumps([]), json.dumps([])
        ))
        new_id = cur.lastrowid
        _recalc_trials(con)
    return jsonify({"ok": True, "id": new_id})

# ── Scenarios API ─────────────────────────────────────────────────────────────
@app.route("/api/scenarios", methods=["GET"])
def get_scenarios():
    with get_db() as con:
        rows = con.execute("SELECT category, scenario FROM scenarios").fetchall()
    return jsonify({r["category"]: r["scenario"] for r in rows})

@app.route("/api/scenarios/<category>", methods=["PUT"])
def set_scenario(category):
    text = request.get_json().get("scenario","")
    with get_db() as con:
        con.execute("""
            INSERT INTO scenarios (category, scenario) VALUES (?,?)
            ON CONFLICT(category) DO UPDATE SET scenario=excluded.scenario
        """, (category, text))
    return jsonify({"ok": True})

# ── Custom categories API ─────────────────────────────────────────────────────
@app.route("/api/categories", methods=["GET"])
def get_categories():
    with get_db() as con:
        rows = con.execute("SELECT * FROM custom_categories").fetchall()
    return jsonify([dict(r) for r in rows])

@app.route("/api/categories", methods=["POST"])
def add_category():
    c = request.get_json()
    with get_db() as con:
        con.execute("""
            INSERT OR IGNORE INTO custom_categories (name,hex,text_color,icon)
            VALUES (?,?,?,?)
        """, (c["name"], c["hex"], c["text"], c["icon"]))
    return jsonify({"ok": True})

# ── Helper ────────────────────────────────────────────────────────────────────
def _recalc_trials(con):
    """Re-number trials within each category by date+time ascending"""
    rows = con.execute("SELECT id, category, date, time FROM sessions").fetchall()
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(dict(r))
    for cat, ss in by_cat.items():
        ss.sort(key=lambda s: (s["date"] or "", s["time"] or ""))
        for i, s in enumerate(ss):
            con.execute("UPDATE sessions SET trial=? WHERE id=?", (i+1, s["id"]))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
