import sqlite3

conn = sqlite3.connect("students.db")

conn.execute("DROP TABLE IF EXISTS students")
conn.execute("""
CREATE TABLE students (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    name TEXT NOT NULL,
    program TEXT NOT NULL,
    year INTEGER NOT NULL,
    section TEXT NOT NULL,
    source TEXT DEFAULT 'Local'
)
""")

students = [
    ("2026-1001", "Jingjing Tan", "BSIT", 2, "A", "Local"),
    ("2026-1002", "Liwei Chen", "BSIT", 2, "B", "Local"),
    ("2026-1003", "Mei Lin Co", "BSCS", 1, "A", "Local"),
    ("2026-1004", "Carlo Uy", "BSCS", 3, "C", "Local"),
    ("2026-1005", "Anna Sy", "BSIT", 1, "B", "Local"),
    ("2026-1006", "Daniel Ong", "BSIS", 3, "A", "Local"),
]

conn.executemany(
    """INSERT INTO students (student_id, name, program, year, section, source)
    VALUES (?, ?, ?, ?, ?, ?)""",
    students,
)

conn.commit()
conn.close()

print("Database created successfully.")
print(f"{len(students)} student records inserted.")
