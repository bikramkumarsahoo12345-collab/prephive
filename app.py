import os
import sqlite3
from datetime import datetime
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from werkzeug.utils import secure_filename
from werkzeug.security import generate_password_hash, check_password_hash
from config import (
    DATABASE_PATH,
    ADMIN_EMAIL,
    ADMIN_PASSWORD,
    UPLOAD_FOLDER,
    ALLOWED_EXTENSIONS,
)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "replace-with-a-secure-secret")
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

DEPARTMENT_PAGES = {
    "cse": "Information Science & Telecommunication",
    "ece": "Computer Applications",
    "mech": "Information Technology Management",
    "civil": "Data Science Management",
    "ee": "Computer Science",
    "it": "Mathematics",
}


def get_db():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    try:
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL UNIQUE,
                mobile TEXT,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS papers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                subject TEXT,
                semester TEXT,
                department TEXT,
                year TEXT,
                filename TEXT NOT NULL,
                uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            """
        )
        conn.commit()
        print("✓ Database initialized successfully")
    except Exception as e:
        print("Database initialization error:", e)
    finally:
        try:
            conn.close()
        except Exception:
            pass


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def query_papers(filters=None):
    filters = filters or {}
    query = "SELECT id, title, subject, semester, department, year, filename FROM papers WHERE 1=1"
    params = []

    if filters.get("department"):
        query += " AND department = ?"
        params.append(filters["department"])
    if filters.get("semester"):
        query += " AND semester = ?"
        params.append(filters["semester"])
    if filters.get("year"):
        query += " AND year = ?"
        params.append(filters["year"])
    if filters.get("search"):
        query += " AND (title LIKE ? OR subject LIKE ?)"
        params.append(f"%{filters['search']}%")
        params.append(f"%{filters['search']}%")

    query += " ORDER BY uploaded_at DESC"

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(query, params)
    papers = [dict(row) for row in cursor.fetchall()]
    cursor.close()
    conn.close()
    return papers


def get_paper(paper_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM papers WHERE id = ?", (paper_id,))
    paper = cursor.fetchone()
    cursor.close()
    conn.close()
    return paper


def delete_uploaded_file(filename):
    if not filename:
        return
    file_path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
    except OSError:
        pass


@app.route("/")
def index():
    return redirect(url_for("home"))


@app.route("/1.html")
def home():
    return render_template("1.html")


@app.route("/login.html", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE email = ?", (email,))
        student = cursor.fetchone()
        cursor.close()
        conn.close()

        if student and check_password_hash(student["password_hash"], password):
            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]
            return redirect(url_for("papers"))
        error = "Invalid email or password."

    return render_template("login.html", error=error)


@app.route("/signup.html", methods=["GET", "POST"])
def signup():
    message = None
    error = None
    if request.method == "POST":
        full_name = request.form.get("full_name")
        email = request.form.get("email")
        mobile = request.form.get("mobile")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

        if password != confirm_password:
            error = "Passwords do not match."
        else:
            conn = get_db()
            cursor = conn.cursor()
            try:
                password_hash = generate_password_hash(password)
                cursor.execute(
                    "INSERT INTO students (full_name, email, mobile, password_hash) VALUES (?, ?, ?, ?)",
                    (full_name, email, mobile, password_hash),
                )
                conn.commit()
                message = "Registration successful. You can now log in."
            except sqlite3.IntegrityError:
                error = "An account with that email already exists."
            finally:
                cursor.close()
                conn.close()

    return render_template("signup.html", message=message, error=error)


@app.route("/contact.html", methods=["GET", "POST"])
def contact():
    message = None
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        subject = request.form.get("subject")
        message_text = request.form.get("message")
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
        message = "Thank you for your message. We will get back to you soon."
        print(f"Contact form submitted: {timestamp} | {name} | {email} | {subject} | {message_text}")

    return render_template("contact.html", message=message)


@app.route("/department.html")
def department():
    return render_template("department.html")


@app.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if email == ADMIN_EMAIL and password == ADMIN_PASSWORD:
            session["admin_logged_in"] = True
            return redirect(url_for("admin_dashboard"))
        error = "Invalid admin credentials."
    return render_template("admin_login.html", error=error)


@app.route("/admin/dashboard")
def admin_dashboard():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))
    papers = query_papers()
    message = request.args.get("message")
    return render_template("admin_dashboard.html", papers=papers, message=message)


@app.route("/admin/upload", methods=["GET", "POST"])
def admin_upload():
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    message = None
    error = None
    if request.method == "POST":
        title = request.form.get("title")
        subject = request.form.get("subject")
        semester = request.form.get("semester")
        department = request.form.get("department")
        year = request.form.get("year")
        file = request.files.get("pdf_file")

        if not file or file.filename == "":
            error = "Please upload a PDF file."
        elif not allowed_file(file.filename):
            error = "Only PDF files are allowed."
        else:
            filename = secure_filename(file.filename)
            timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
            stored_name = f"{timestamp}_{filename}"
            file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
            file.save(file_path)

            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO papers (title, subject, semester, department, year, filename) VALUES (?, ?, ?, ?, ?, ?)",
                (title, subject, semester, department, year, stored_name),
            )
            conn.commit()
            cursor.close()
            conn.close()
            message = "Paper uploaded successfully."

    return render_template(
        "upload_paper.html",
        message=message,
        error=error,
        form_action=url_for("admin_upload"),
        is_edit=False,
    )


@app.route("/admin/edit/<int:paper_id>", methods=["GET", "POST"])
def admin_edit(paper_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    paper_row = get_paper(paper_id)
    if not paper_row:
        return "Paper not found", 404

    paper = dict(paper_row)
    message = None
    error = None

    if request.method == "POST":
        title = request.form.get("title")
        subject = request.form.get("subject")
        semester = request.form.get("semester")
        department = request.form.get("department")
        year = request.form.get("year")
        file = request.files.get("pdf_file")
        filename = paper["filename"]

        if file and file.filename != "":
            if not allowed_file(file.filename):
                error = "Only PDF files are allowed."
            else:
                new_filename = secure_filename(file.filename)
                timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
                stored_name = f"{timestamp}_{new_filename}"
                file_path = os.path.join(app.config["UPLOAD_FOLDER"], stored_name)
                file.save(file_path)
                delete_uploaded_file(filename)
                filename = stored_name

        if not error:
            conn = get_db()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE papers SET title = ?, subject = ?, semester = ?, department = ?, year = ?, filename = ? WHERE id = ?",
                (title, subject, semester, department, year, filename, paper_id),
            )
            conn.commit()
            cursor.close()
            conn.close()
            return redirect(url_for("admin_dashboard", message="Paper updated successfully."))

    return render_template(
        "upload_paper.html",
        paper=paper,
        message=message,
        error=error,
        form_action=url_for("admin_edit", paper_id=paper_id),
        is_edit=True,
    )


@app.route("/admin/delete/<int:paper_id>", methods=["POST"])
def admin_delete(paper_id):
    if not session.get("admin_logged_in"):
        return redirect(url_for("admin_login"))

    paper_row = get_paper(paper_id)
    if not paper_row:
        return "Paper not found", 404

    delete_uploaded_file(paper_row["filename"])
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM papers WHERE id = ?", (paper_id,))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(url_for("admin_dashboard", message="Paper deleted successfully."))


@app.route("/papers")
def papers():
    if not session.get("student_id"):
        return redirect(url_for("login"))

    filters = {
        "department": request.args.get("department"),
        "semester": request.args.get("semester"),
        "year": request.args.get("year"),
        "search": request.args.get("search"),
    }
    papers_list = query_papers(filters)
    return render_template("papers.html", papers=papers_list, filters=filters)


@app.route("/download/<int:paper_id>")
def download(paper_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT filename FROM papers WHERE id = ?", (paper_id,))
    row = cursor.fetchone()
    cursor.close()
    conn.close()
    if not row:
        return "Paper not found", 404
    return send_from_directory(app.config["UPLOAD_FOLDER"], row["filename"], as_attachment=True)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/<page>.html")
def dynamic_page(page):
    if page in DEPARTMENT_PAGES:
        department_name = DEPARTMENT_PAGES[page]
        papers_list = query_papers({"department": department_name})
        return render_template("department_detail.html", department=department_name, papers=papers_list)
    return "Page not found", 404


if __name__ == "__main__":
    init_db()
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "false").lower() == "true"
    app.run(host=host, port=port, debug=debug_mode)
