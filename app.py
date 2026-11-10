
import ipaddress
import os
import socket
import sqlite3
import requests
from urllib.parse import urlparse
from flask import Flask, jsonify, request, render_template

app = Flask(__name__)

# Partner's API (AWS Static IP, domain or Render). Set PARTNER_API_URL, or edit the default.
PARTNER_URL = os.environ.get(
    "PARTNER_API_URL", "https://CLASSMATE-APP.onrender.com/api/students"
)


# DATABASE CONNECTION
def get_db_connection():
    conn = sqlite3.connect("students.db")
    conn.row_factory = sqlite3.Row
    return conn


def ensure_source_column():
    conn = get_db_connection()
    cols = [c["name"] for c in conn.execute("PRAGMA table_info(students)")]
    if cols and "source" not in cols:
        conn.execute("ALTER TABLE students ADD COLUMN source TEXT DEFAULT 'Local'")
        conn.execute("UPDATE students SET source = 'Local' WHERE source IS NULL")
        conn.commit()
    conn.close()


ensure_source_column()


# HOME PAGE
@app.route('/')
def home():
    return render_template('index.html')


# ==========================================
# ACTIVITY 4: EXISTING API ENDPOINTS
# ==========================================

@app.route('/student')
def get_student():
    return jsonify({
        "student_id": "26-00201",
        "name": "Jingjing Tan",
        "program": "BSIT",
        "year": 2,
        "section": "A"
    })


@app.route('/hello')
def say_hello():
    name = request.args.get('name', 'Student')
    return jsonify({
        "message": f"Hello, {name}!"
    })


@app.route('/grade')
def get_grade():
    score = float(request.args.get('score', 0))

    if score >= 75:
        remark = "Very Good"
    else:
        remark = "Needs Improvement"

    return jsonify({
        "score": score,
        "remark": remark
    })


# ==========================================
# ACTIVITY 7: STUDENT DATABASE ENDPOINTS
# ==========================================

# GET ALL STUDENTS
@app.route('/students')
def get_all_students():
    conn = get_db_connection()
    students = conn.execute(
        "SELECT * FROM students"
    ).fetchall()
    conn.close()

    return jsonify([dict(student) for student in students])


# GET ONE STUDENT BY ID
@app.route('/students/<int:id>')
def get_student_by_id(id):
    conn = get_db_connection()
    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()
    conn.close()

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(student))


# FILTER STUDENTS
@app.route('/students/filter')
def filter_students():
    program = request.args.get('program')
    year = request.args.get('year')
    section = request.args.get('section')

    filters = []
    values = []

    if program:
        filters.append("program = ?")
        values.append(program)

    if year:
        filters.append("year = ?")
        values.append(year)

    if section:
        filters.append("section = ?")
        values.append(section)

    if not filters:
        return jsonify({
            "error": "Please provide program, year, or section."
        }), 400

    query = "SELECT * FROM students WHERE " + " AND ".join(filters)

    conn = get_db_connection()
    students = conn.execute(query, values).fetchall()
    conn.close()

    return jsonify([dict(student) for student in students])


# ==========================================
# ACTIVITY 8: CRUD API ENDPOINTS
# ==========================================

# CREATE - ADD STUDENT
@app.route('/api/students', methods=['POST'])
def add_student():
    data = request.get_json()

    if not data:
        return jsonify({"error": "No student data provided"}), 400

    required_fields = [
        'student_id', 'name', 'program', 'year', 'section'
    ]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required student fields"}), 400

    conn = get_db_connection()

    cursor = conn.execute(
        """INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (
            data['student_id'],
            data['name'],
            data['program'],
            data['year'],
            data['section'],
            data.get('source', 'External API')
        )
    )

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return jsonify({
        "message": "Student added",
        "id": new_id
    }), 201


# READ - GET ALL STUDENTS (READ-ONLY API FOR CLASSMATES)
@app.route('/api/students', methods=['GET'])
def api_students():
    conn = get_db_connection()

    rows = conn.execute(
        "SELECT * FROM students"
    ).fetchall()

    conn.close()

    return jsonify([dict(row) for row in rows])


# READ - GET ONE STUDENT
@app.route('/api/students/<int:id>', methods=['GET'])
def api_get_student(id):
    conn = get_db_connection()

    student = conn.execute(
        "SELECT * FROM students WHERE id = ?",
        (id,)
    ).fetchone()

    conn.close()

    if student is None:
        return jsonify({"error": "Student not found"}), 404

    return jsonify(dict(student))


# UPDATE - EDIT STUDENT
@app.route('/api/students/<int:id>', methods=['PUT'])
def update_student(id):
    data = request.get_json()

    if not data:
        return jsonify({"error": "No student data provided"}), 400

    required_fields = [
        'student_id', 'name', 'program', 'year', 'section'
    ]

    if not all(field in data for field in required_fields):
        return jsonify({"error": "Missing required student fields"}), 400

    conn = get_db_connection()

    cursor = conn.execute(
        """UPDATE students SET
        student_id = ?,
        name = ?,
        program = ?,
        year = ?,
        section = ?
        WHERE id = ?""",
        (
            data['student_id'],
            data['name'],
            data['program'],
            data['year'],
            data['section'],
            id
        )
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({"message": "Student updated"})


# DELETE - REMOVE STUDENT
@app.route('/api/students/<int:id>', methods=['DELETE'])
def delete_student(id):
    conn = get_db_connection()

    cursor = conn.execute(
        "DELETE FROM students WHERE id = ?",
        (id,)
    )

    conn.commit()
    conn.close()

    if cursor.rowcount == 0:
        return jsonify({"error": "Student not found"}), 404

    return jsonify({"message": "Student deleted"})


# ==========================================
# ACTIVITY 9: SYSTEM-TO-SYSTEM INTEGRATION
# ==========================================

REQUIRED_FIELDS = ['student_id', 'name', 'program', 'year', 'section']


def is_public_host(host):
    """True only if every address behind `host` is a public one (no loopback, private or link-local
    ranges such as 169.254.169.254, the cloud metadata address)."""
    try:
        ips = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            ips = [ipaddress.ip_address(info[4][0]) for info in socket.getaddrinfo(host, None)]
        except OSError:
            return False
    return bool(ips) and all(ip.is_global for ip in ips)


def partner_url_from(value):
    """Return a safe partner URL, or None.

    Lab 10: the partner can be an AWS Static IP or a domain (http or https) as well as a Render
    URL. The address must be public and the path must be /api/students.
    """
    url = (value or "").strip() or PARTNER_URL
    parts = urlparse(url)
    host = parts.hostname or ""
    # ALLOW_LOCAL_PARTNER=1 is for testing two apps on one PC; leave it unset on the server.
    local_ok = os.environ.get("ALLOW_LOCAL_PARTNER") == "1" and host in ("127.0.0.1", "localhost")
    try:
        port = parts.port
    except ValueError:
        return None
    if (parts.scheme not in ("http", "https") or parts.username or parts.password or not host
            or parts.path.rstrip("/") != "/api/students" or parts.query):
        return None
    if not local_ok and (port not in (None, 80, 443) or not is_public_host(host)):
        return None
    return url


# RETRIEVE PARTNER'S RECORDS (server-side, avoids browser CORS)
@app.route('/partner-records')
def partner_records():
    url = partner_url_from(request.args.get('url'))
    if url is None:
        return jsonify({"error": "Enter a public API address ending in /api/students (AWS IP, domain or Render URL)."}), 400

    try:
        response = requests.get(url, timeout=15, allow_redirects=False)
        response.raise_for_status()
        return jsonify(response.json())
    except (requests.RequestException, ValueError):
        return jsonify({"error": "Unable to retrieve partner data"}), 502


# SAVE A SELECTED PARTNER RECORD INTO MY DATABASE
@app.route('/import-student', methods=['POST'])
def import_student():
    data = request.get_json(silent=True)

    if not data or not all(f in data for f in REQUIRED_FIELDS):
        return jsonify({"error": "Missing required student fields"}), 400

    conn = get_db_connection()
    conn.execute(
        """INSERT INTO students
        (student_id, name, program, year, section, source)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (data['student_id'], data['name'], data['program'],
         data['year'], data['section'], 'Classmate API')
    )
    conn.commit()
    conn.close()
    return jsonify({"message": "Remote record saved"}), 201


# SEND A PRACTICE RECORD TO MY PARTNER'S POST ENDPOINT
@app.route('/send-record', methods=['POST'])
def send_record():
    body = request.get_json(silent=True) or {}
    url = partner_url_from(body.get('url'))
    if url is None:
        return jsonify({"error": "Enter a public API address ending in /api/students (AWS IP, domain or Render URL)."}), 400

    rec = body.get('record') or {}
    if not all(str(rec.get(f, '')).strip() for f in REQUIRED_FIELDS):
        return jsonify({"error": "Fill in every field of the record."}), 400
    try:
        year = int(rec['year'])
    except (TypeError, ValueError):
        return jsonify({"error": "Year must be a number."}), 400
    if year < 1:
        return jsonify({"error": "Year must be 1 or more."}), 400

    record = {
        "student_id": str(rec['student_id']).strip(),
        "name": str(rec['name']).strip(),
        "program": str(rec['program']).strip(),
        "year": year,
        "section": str(rec['section']).strip(),
        "source": "Partner API"
    }

    try:
        response = requests.post(url, json=record, timeout=15, allow_redirects=False)
    except requests.RequestException:
        return jsonify({"error": "Unable to reach partner API"}), 502

    return jsonify({
        "partner_status": response.status_code,
        "partner_response": response.text,
        "sent": record
    }), (response.status_code if response.status_code >= 400 else 200)


# ==========================================
# RUN FLASK APPLICATION
# ==========================================

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
