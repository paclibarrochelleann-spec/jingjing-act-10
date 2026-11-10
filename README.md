# jingjing-act-9 — Laboratory Activities 7, 8 and 9

Flask + SQLite student app.

- **Lab 7:** `init_db.py` creates `students.db`; `/students`, `/students/<id>`, and `/students/filter?program=|year=|section=` read from the database; the page lists them ("Older Activities" tab).
- **Lab 8:** CRUD on `/api/students`, My Records and Classmate's (Partner) Records as separate sources, search and View details.
- **Lab 9:** `/partner-records`, `/import-student`, `/send-record`, the `source` column, and the Integration Dashboard.

## Run locally
    pip install -r requirements.txt
    python init_db.py
    python app.py

## Render
Build: `pip install -r requirements.txt`   Start: `gunicorn app:app`

Use fictional data only.

## Laboratory Activity 10 (AWS Lightsail)
See `LAB10_AWS_GUIDE.md` and the `deploy/` folder. The partner box now accepts an AWS Static IP or domain ending in `/api/students`.
