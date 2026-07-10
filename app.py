import os
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, session, redirect
from db import get_connection

app = Flask(__name__)
app.secret_key = "placement_secret_key"
UPLOAD_FOLDER = "uploads"

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/student_register", methods=["GET", "POST"])
def student_register():

    if request.method == "POST":

        full_name = request.form["full_name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        department = request.form["department"]
        phone = request.form["phone"]
        cgpa = request.form["cgpa"]

        # Validation
        if full_name.strip() == "":
            return "<h2>Name cannot be empty.</h2>"

        if "@" not in email:
            return "<h2>Invalid Email Address.</h2>"

        if len(phone) != 10 or not phone.isdigit():
            return "<h2>Phone number must contain exactly 10 digits.</h2>"

        try:
            cgpa = float(cgpa)
            if cgpa < 0 or cgpa > 10:
                return "<h2>CGPA must be between 0 and 10.</h2>"
        except:
            return "<h2>Invalid CGPA.</h2>"

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO students
        (full_name, email, password, department, phone, cgpa)
        VALUES (%s, %s, %s, %s, %s, %s)
        """

        values = (
            full_name,
            email,
            password,
            department,
            phone,
            cgpa
        )

        cursor.execute(sql, values)

        conn.commit()

        cursor.close()
        conn.close()

        return "<h2>Student Registered Successfully!</h2>"

    return render_template("student_register.html")
@app.route("/student_login", methods=["GET", "POST"])
def student_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute(
            "SELECT * FROM students WHERE email=%s",
            (email,)
        )

        student = cursor.fetchone()

        cursor.close()
        conn.close()

        if student and check_password_hash(student["password"], password):

            session["student_id"] = student["id"]
            session["student_name"] = student["full_name"]

            return render_template(
                "student_dashboard.html",
                name=student["full_name"]
            )

        else:
            return "<h2>Invalid Email or Password</h2>"

    return render_template("student_login.html")
@app.route("/student_profile")
def student_profile():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute(
        "SELECT * FROM students WHERE id=%s",
        (session["student_id"],)
    )

    student = cursor.fetchone()

    cursor.close()
    conn.close()

    return render_template(
        "student_profile.html",
        student=student
    )
@app.route("/upload_resume", methods=["GET", "POST"])
def upload_resume():

    if "student_id" not in session:
        return redirect("/student_login")

    if request.method == "POST":

        file = request.files["resume"]

        if file:

            filename = secure_filename(file.filename)

            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            conn = get_connection()
            cursor = conn.cursor()

            cursor.execute(
                "UPDATE students SET resume=%s WHERE id=%s",
                (filename, session["student_id"])
            )

            conn.commit()

            cursor.close()
            conn.close()

            return "<h2>Resume Uploaded Successfully!</h2>"

    return render_template("resume_upload.html")
@app.route("/company_register", methods=["GET", "POST"])
def company_register():

    if request.method == "POST":

        company_name = request.form["company_name"]
        email = request.form["email"]
        password = generate_password_hash(request.form["password"])
        location = request.form["location"]
        website = request.form["website"]

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO companies
        (company_name,email,password,location,website)
        VALUES(%s,%s,%s,%s,%s)
        """

        cursor.execute(sql,
        (company_name,email,password,location,website))

        conn.commit()

        cursor.close()
        conn.close()

        return "<h2>Company Registered Successfully!</h2>"

    return render_template("company_register.html")
@app.route("/company_login", methods=["GET", "POST"])
def company_login():

    if request.method == "POST":

        email = request.form["email"]
        password = request.form["password"]

        conn = get_connection()
        cursor = conn.cursor(dictionary=True)

        # Get company details using email only
        cursor.execute(
            "SELECT * FROM companies WHERE email=%s",
            (email,)
        )

        company = cursor.fetchone()

        cursor.close()
        conn.close()

        # Verify hashed password
        if company and check_password_hash(company["password"], password):

            session["company_id"] = company["id"]
            session["company_name"] = company["company_name"]

            return render_template(
                "company_dashboard.html",
                company=company["company_name"]
            )

        else:
            return "<h2>Invalid Email or Password</h2>"

    return render_template("company_login.html")
@app.route("/post_job", methods=["GET", "POST"])
def post_job():

    if "company_id" not in session:
        return redirect("/company_login")

    if request.method == "POST":

        job_title = request.form["job_title"]
        job_role = request.form["job_role"]
        salary = request.form["salary"]
        location = request.form["location"]
        eligibility = request.form["eligibility"]
        last_date = request.form["last_date"]
        description = request.form["description"]

        conn = get_connection()
        cursor = conn.cursor()

        sql = """
        INSERT INTO jobs
        (company_id,job_title,job_role,salary,location,
        eligibility,last_date,description)
        VALUES(%s,%s,%s,%s,%s,%s,%s,%s)
        """

        values = (
            session["company_id"],
            job_title,
            job_role,
            salary,
            location,
            eligibility,
            last_date,
            description
        )

        cursor.execute(sql, values)

        conn.commit()

        cursor.close()
        conn.close()

        return "<h2>Job Posted Successfully!</h2>"

    return render_template("post_job.html")
@app.route("/view_jobs")
def view_jobs():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT jobs.*, companies.company_name
        FROM jobs
        JOIN companies
        ON jobs.company_id = companies.id
        ORDER BY jobs.created_at DESC
    """)

    jobs = cursor.fetchall()

    cursor.close()
    conn.close()
    print(jobs)

    return render_template(
        "view_jobs.html",
        jobs=jobs
    )
@app.route("/apply_job/<int:job_id>")
def apply_job(job_id):

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    # Check if the student has already applied for this job
    cursor.execute(
        """
        SELECT *
        FROM applications
        WHERE student_id=%s AND job_id=%s
        """,
        (session["student_id"], job_id)
    )

    existing = cursor.fetchone()

    if existing:
        cursor.close()
        conn.close()
        return "<h2>You have already applied for this job.</h2>"

    # Insert new application
    cursor.execute(
        """
        INSERT INTO applications(student_id, job_id)
        VALUES(%s, %s)
        """,
        (session["student_id"], job_id)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return "<h2>Application Submitted Successfully!</h2>"
@app.route("/my_applications")
def my_applications():

    if "student_id" not in session:
        return redirect("/student_login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT
            applications.status,
            jobs.job_title,
            jobs.job_role,
            jobs.salary,
            companies.company_name
        FROM applications
        JOIN jobs
            ON applications.job_id = jobs.id
        JOIN companies
            ON jobs.company_id = companies.id
        WHERE applications.student_id=%s
    """, (session["student_id"],))

    applications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "my_applications.html",
        applications=applications
    )
@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "admin123":

            session["admin"] = True
            return redirect("/admin_dashboard")

        return "<h2>Invalid Admin Credentials</h2>"

    return render_template("admin_login.html")


@app.route("/admin_dashboard")
def admin_dashboard():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT COUNT(*) AS total FROM students")
    students = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM companies")
    companies = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM jobs")
    jobs = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) AS total FROM applications")
    applications = cursor.fetchone()["total"]

    cursor.close()
    conn.close()

    return render_template(
        "admin_dashboard.html",
        students=students,
        companies=companies,
        jobs=jobs,
        applications=applications
    )
@app.route("/admin_students")
def admin_students():

    if "admin" not in session:
        return redirect("/admin_login")

    search = request.args.get("search", "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        cursor.execute("""
            SELECT *
            FROM students
            WHERE full_name LIKE %s
            ORDER BY id
        """, ("%" + search + "%",))

    else:

        cursor.execute("""
            SELECT *
            FROM students
            ORDER BY id
        """)

    students = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_students.html",
        students=students,
        search=search
    )
@app.route("/admin_companies")
def admin_companies():

    if "admin" not in session:
        return redirect("/admin_login")

    search = request.args.get("search", "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        cursor.execute("""
            SELECT *
            FROM companies
            WHERE company_name LIKE %s
            ORDER BY id
        """, ("%" + search + "%",))

    else:

        cursor.execute("""
            SELECT *
            FROM companies
            ORDER BY id
        """)

    companies = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_companies.html",
        companies=companies,
        search=search
    )
@app.route("/admin_jobs")
def admin_jobs():

    if "admin" not in session:
        return redirect("/admin_login")

    search = request.args.get("search", "")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    if search:

        cursor.execute("""
            SELECT
                jobs.id,
                jobs.job_title,
                jobs.job_role,
                jobs.salary,
                jobs.location,
                jobs.eligibility,
                jobs.last_date,
                companies.company_name
            FROM jobs
            JOIN companies
            ON jobs.company_id = companies.id
            WHERE jobs.job_title LIKE %s
            ORDER BY jobs.created_at DESC
        """, ("%" + search + "%",))

    else:

        cursor.execute("""
            SELECT
                jobs.id,
                jobs.job_title,
                jobs.job_role,
                jobs.salary,
                jobs.location,
                jobs.eligibility,
                jobs.last_date,
                companies.company_name
            FROM jobs
            JOIN companies
            ON jobs.company_id = companies.id
            ORDER BY jobs.created_at DESC
        """)

    jobs = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_jobs.html",
        jobs=jobs,
        search=search
    )
@app.route("/admin_applications")
def admin_applications():

    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_connection()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
    SELECT
        applications.id,
        students.full_name,
        companies.company_name,
        jobs.job_title,
        applications.status

    FROM applications

    JOIN students
    ON applications.student_id = students.id

    JOIN jobs
    ON applications.job_id = jobs.id

    JOIN companies
    ON jobs.company_id = companies.id

    ORDER BY applications.id DESC
    """)

    applications = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template(
        "admin_applications.html",
        applications=applications
    )
@app.route("/shortlist/<int:id>")
def shortlist(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE applications
        SET status='Shortlisted'
        WHERE id=%s
        """,
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_applications")
@app.route("/reject/<int:id>")
def reject(id):

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        """
        UPDATE applications
        SET status='Rejected'
        WHERE id=%s
        """,
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_applications")
@app.route("/delete_student/<int:id>")
def delete_student(id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_connection()
    cursor = conn.cursor()

    # Delete all applications of the student first
    cursor.execute(
        "DELETE FROM applications WHERE student_id=%s",
        (id,)
    )

    # Then delete the student
    cursor.execute(
        "DELETE FROM students WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_students")
@app.route("/delete_company/<int:id>")
def delete_company(id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM companies WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_companies")
@app.route("/delete_job/<int:id>")
def delete_job(id):

    if "admin" not in session:
        return redirect("/admin_login")

    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM jobs WHERE id=%s",
        (id,)
    )

    conn.commit()

    cursor.close()
    conn.close()

    return redirect("/admin_jobs")
@app.route("/student_logout")
def student_logout():

    session.clear()

    return redirect("/student_login")
@app.route("/company_logout")
def company_logout():

    session.clear()

    return redirect("/company_login")
@app.route("/admin_logout")
def admin_logout():

    session.clear()

    return redirect("/admin_login")
if __name__ == "__main__":
    app.run(debug=True)
   
