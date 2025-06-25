from flask import Flask, render_template, request, redirect, flash, session
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
import os
from functools import wraps

# Flask App Init
app = Flask(__name__)
app.secret_key = 'dipesh_secret_123'

# SQLite Database Connection
conn = sqlite3.connect('studentmanagementsystem.db', check_same_thread=False)
cursor = conn.cursor()

#00 Folder to save uploaded profile pictures
UPLOAD_FOLDER = 'static/uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Decorator for admin login required
def admin_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_id'):
            flash('Please login as admin first.', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# Decorator for student login required
def student_login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('student_id'):
            flash('Please login first.', 'danger')
            return redirect('/')
        return f(*args, **kwargs)
    return decorated_function

# Helper function to fetch all rows as list of dicts
def fetch_all_dicts(query, params=None):
    cursor.execute(query, params or ())
    columns = [desc[0] for desc in cursor.description]
    results = cursor.fetchall()
    return [dict(zip(columns, row)) for row in results]

# Helper function to fetch one row as dict
def fetch_one_dict(query, params=None):
    cursor.execute(query, params or ())
    row = cursor.fetchone()
    if not row:
        return None
    columns = [desc[0] for desc in cursor.description]
    return dict(zip(columns, row))

#  Index Page
@app.route('/')
def home():
    return render_template('index.html')

# Manage Subjects Page
@app.route('/manage_subjects')
@admin_login_required
def manage_subjects():
    subjects = fetch_all_dicts("SELECT subject_id, subject_name FROM subjects")
    return render_template('manage_subjects.html', subjects=subjects)

# Add Subject Page
@app.route('/add_subject', methods=['GET', 'POST'])
@admin_login_required
def add_subject():
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        cursor.execute("INSERT INTO subjects (subject_name) VALUES (?)", (subject_name,))
        conn.commit()
        flash('Subject added successfully!', 'success')
        return redirect('/manage_subjects')
    return render_template('add_subject.html')

# Edit Subject Page
@app.route('/edit_subject/<int:subject_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_subject(subject_id):
    if request.method == 'POST':
        subject_name = request.form['subject_name']
        cursor.execute("UPDATE subjects SET subject_name = ? WHERE subject_id = ?", (subject_name, subject_id))
        conn.commit()
        flash('Subject updated successfully!', 'success')
        return redirect('/manage_subjects')
    subject = fetch_one_dict("SELECT subject_id, subject_name FROM subjects WHERE subject_id = ?", (subject_id,))
    if not subject:
        flash('Subject not found.', 'danger')
        return redirect('/manage_subjects')
    return render_template('edit_subject.html', subject=subject)

# Delete Subject Page
@app.route('/delete_subject/<int:subject_id>')
@admin_login_required
def delete_subject(subject_id):
    cursor.execute("DELETE FROM subjects WHERE subject_id = ?", (subject_id,))
    conn.commit()
    flash('Subject deleted successfully!', 'success')
    return redirect('/manage_subjects')

# Manage Students Page
@app.route('/manage_students')
@admin_login_required
def manage_students():
    students = fetch_all_dicts("SELECT student_id, name, course, Email_Id, mobile FROM student")
    return render_template('manage_students.html', students=students)

# Add Student Page
@app.route('/add_student', methods=['GET', 'POST'])
@admin_login_required
def add_student():
    if request.method == 'POST':
        student_id = request.form['student_id']
        name = request.form['name']
        course = request.form['course']
        Email_Id = request.form['Email_Id']
        mobile = request.form['mobile']
        password = request.form['password']
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        address = request.form.get('address')
        hashed_password = generate_password_hash(password)

        cursor.execute("SELECT * FROM student WHERE student_id = ?", (student_id,))
        if cursor.fetchone():
            flash('Student ID already exists!', 'danger')
            return redirect('/add_student')

        import uuid
        profile_picture = request.files.get('profile_picture')
        profile_picture_url = None
        if profile_picture and profile_picture.filename != '':
            import logging
            import uuid
            ext = os.path.splitext(profile_picture.filename)[1]
            unique_filename = str(uuid.uuid4()) + ext
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            logging.info(f"Saving profile picture to: {filepath}")
            profile_picture.save(filepath)
            profile_picture_url = os.path.join('uploads', unique_filename).replace('\\', '/')
            logging.info(f"Profile picture URL set to: {profile_picture_url}")

        cursor.execute("""INSERT INTO student 
            (student_id, name, course, Email_Id, mobile, password, date_of_birth, gender, address, profile_picture_url) 
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (student_id, name, course, Email_Id, mobile, hashed_password, date_of_birth, gender, address, profile_picture_url))
        conn.commit()
        flash('Student added successfully!', 'success')
        return redirect('/manage_students')

    return render_template('add_student.html')

# Edit Student Page
@app.route('/edit_student/<student_id>', methods=['GET', 'POST'])
@admin_login_required
def edit_student(student_id):
    if request.method == 'POST':
        name = request.form['name']
        course = request.form['course']
        Email_Id = request.form['Email_Id']
        mobile = request.form['mobile']
        password = request.form.get('password')
        date_of_birth = request.form.get('date_of_birth')
        gender = request.form.get('gender')
        address = request.form.get('address')

        profile_picture = request.files.get('profile_picture')
        profile_picture_url = None
        print(f"DEBUG: profile_picture object: {profile_picture}")
        if profile_picture and profile_picture.filename != '':
            print(f"DEBUG: profile_picture filename: {profile_picture.filename}")
            import uuid
            ext = os.path.splitext(profile_picture.filename)[1]
            unique_filename = str(uuid.uuid4()) + ext
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            profile_picture.save(filepath)
            profile_picture_url = os.path.join('uploads', unique_filename).replace('\\', '/')
            print(f"DEBUG: profile_picture_url set to: {profile_picture_url}")

        if password:
            hashed_password = generate_password_hash(password)
            if profile_picture_url:
                cursor.execute("""UPDATE student SET name=?, course=?, Email_Id=?, mobile=?, password=?, date_of_birth=?, gender=?, address=?, profile_picture_url=? WHERE student_id=?""",
                               (name, course, Email_Id, mobile, hashed_password, date_of_birth, gender, address, profile_picture_url, student_id))
            else:
                cursor.execute("""UPDATE student SET name=?, course=?, Email_Id=?, mobile=?, password=?, date_of_birth=?, gender=?, address=? WHERE student_id=?""",
                               (name, course, Email_Id, mobile, hashed_password, date_of_birth, gender, address, student_id))
        else:
            if profile_picture_url:
                cursor.execute("""UPDATE student SET name=?, course=?, Email_Id=?, mobile=?, date_of_birth=?, gender=?, address=?, profile_picture_url=? WHERE student_id=?""",
                               (name, course, Email_Id, mobile, date_of_birth, gender, address, profile_picture_url, student_id))
            else:
                cursor.execute("""UPDATE student SET name=?, course=?, Email_Id=?, mobile=?, date_of_birth=?, gender=?, address=? WHERE student_id=?""",
                               (name, course, Email_Id, mobile, date_of_birth, gender, address, student_id))
        conn.commit()
        flash('Student updated successfully!', 'success')
        return redirect('/manage_students')

    student = fetch_one_dict("SELECT student_id, name, course, Email_Id, mobile, date_of_birth, gender, address, profile_picture_url FROM student WHERE student_id = ?", (student_id,))
    if not student:
        flash('Student not found.', 'danger')
        return redirect('/manage_students')
    return render_template('edit_student.html', student=student)

# Delete Student Page
@app.route('/delete_student/<student_id>')
@admin_login_required
def delete_student(student_id):
    cursor.execute("DELETE FROM student WHERE student_id = ?", (student_id,))
    conn.commit()
    flash('Student deleted successfully!', 'success')
    return redirect('/manage_students')

# Signup Page
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        role = request.form['role']
        name = request.form['name']
        mobile = request.form['mobile']
        password = request.form['password']
        hashed_password = generate_password_hash(password)

        if role == 'admin':
            admin_id = request.form['admin_id']
            department = request.form['department']

            profile_picture = request.files.get('profile_picture')
            profile_picture_url = None
            print(f"DEBUG SIGNUP: profile_picture object: {profile_picture}")
            if profile_picture and profile_picture.filename != '':
                print(f"DEBUG SIGNUP: profile_picture filename: {profile_picture.filename}")
                import uuid
                ext = os.path.splitext(profile_picture.filename)[1]
                unique_filename = str(uuid.uuid4()) + ext
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                profile_picture.save(filepath)
                profile_picture_url = os.path.join('uploads', unique_filename).replace('\\', '/')
                print(f"DEBUG SIGNUP: profile_picture_url set to: {profile_picture_url}")

            cursor.execute("SELECT * FROM admin WHERE admin_id = ?", (admin_id,))
            if cursor.fetchone():
                flash('Admin ID already exists!', 'danger')
                return redirect('/signup')

            cursor.execute("INSERT INTO admin (admin_id, department, name, mobile, password, profile_picture_url) VALUES (?, ?, ?, ?, ?, ?)",
                           (admin_id, department, name, mobile, hashed_password, profile_picture_url))
            conn.commit()
            flash('Admin registered successfully!', 'success')
            return redirect('/')

        elif role == 'student':
            student_id = request.form['student_id']
            course = request.form['course']
            Email_Id = request.form['Email_Id']
            date_of_birth = request.form.get('date_of_birth')
            gender = request.form.get('gender')
            address = request.form.get('address')

        profile_picture = request.files.get('profile_picture')
        profile_picture_url = None
        if profile_picture and profile_picture.filename != '':
            import uuid
            ext = os.path.splitext(profile_picture.filename)[1]
            unique_filename = str(uuid.uuid4()) + ext
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
            try:
                profile_picture.save(filepath)
                profile_picture_url = os.path.join('uploads', unique_filename).replace('\\', '/')
            except Exception as e:
                print(f"Error saving profile picture: {e}")

            cursor.execute("SELECT * FROM student WHERE student_id = ?", (student_id,))
            if cursor.fetchone():
                flash('Student ID already exists!', 'danger')
                return redirect('/signup')

            cursor.execute("""INSERT INTO student 
                (student_id, course, Email_Id, name, mobile, password, date_of_birth, gender, address, profile_picture_url) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (student_id, course, Email_Id, name, mobile, hashed_password, date_of_birth, gender, address, profile_picture_url))
            conn.commit()
            flash('Student registered successfully!', 'success')
            session['student_id'] = student_id
            return redirect('/student_dashboard')

        else:
            flash('Please select a valid role.', 'danger')

    return render_template('signup.html')

# Login Route
@app.route('/login', methods=['POST'])
def login():
    user_type = request.form['user_type']
    username = request.form['username']
    password = request.form['password']

    if user_type == 'admin':
        cursor.execute("SELECT password FROM admin WHERE admin_id = ?", (username,))
        result = cursor.fetchone()
        print(f"Admin login attempt for {username}, fetched hash: {result}")
        if result and check_password_hash(result[0], password):
            print("Admin password verified")
            session['admin_id'] = username
            flash('Admin login successful!', 'success')
            return redirect('/admin_dashboard')
        else:
            print("Admin login failed")
            flash('Invalid admin credentials', 'danger')
            return redirect('/')

    if user_type == 'student':
        cursor.execute("SELECT password FROM student WHERE student_id = ?", (username,))
        result = cursor.fetchone()
        print(f"Student login attempt for {username}, fetched hash: {result}")
        if result and check_password_hash(result[0], password):
            print("Student password verified")
            session['student_id'] = username
            flash('Student login successful!', 'success')
            return redirect('/student_dashboard')
        else:
            print("Student login failed")
            flash('Invalid student credentials', 'danger')
            return redirect('/')

    else:
        flash('Invalid user type', 'danger')
        return redirect('/')

# Student Dashboard Route
@app.route('/student_dashboard')
@student_login_required
def student_dashboard():
    student_id = session.get('student_id')
    student = fetch_one_dict("SELECT name, profile_picture_url FROM student WHERE student_id = ?", (student_id,))
    name = student['name'] if student else 'Student'
    profile_picture_url = student['profile_picture_url'] if student else None

    notices = fetch_all_dicts("SELECT title, content FROM notices ORDER BY id DESC")

    return render_template('student_dashboard.html', name=name, profile_picture_url=profile_picture_url, notices=notices)

# My Courses Page
@app.route('/my_courses')
@student_login_required
def my_courses():
    student_id = session.get('student_id')
    courses = fetch_all_dicts("""
        SELECT s.subject_name
        FROM subjects s
        JOIN student_subjects ss ON s.subject_id = ss.subject_id
        WHERE ss.student_id = ?
    """, (student_id,))
    return render_template('my_courses.html', courses=courses)

# Admin Dashboard Route
@app.route('/admin_dashboard')
@admin_login_required
def admin_dashboard():
    admin_id = session.get('admin_id')
    admin = fetch_one_dict("SELECT name, profile_picture_url FROM admin WHERE admin_id = ?", (admin_id,))
    admin_name = admin['name'] if admin else 'Admin'
    profile_picture_url = admin['profile_picture_url'] if admin else None
    return render_template('admin_dashboard.html', admin_name=admin_name, profile_picture_url=profile_picture_url)

# Profile Route
@app.route('/profile')
@student_login_required
def profile():
    student_id = session.get('student_id')
    student = fetch_one_dict("SELECT student_id, name, mobile, course, Email_Id as email, date_of_birth, gender, address, profile_picture_url FROM student WHERE student_id = ?", (student_id,))
    if not student:
        flash('Student not found.', 'danger')
        return redirect('/student_dashboard')
    return render_template('profile.html', student=student)

# Logout Route
@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect('/')

# Post Notice Page
@app.route('/post_notice', methods=['GET', 'POST'])
@admin_login_required
def post_notice():
    if request.method == 'POST':
        title = request.form['title']
        content = request.form['content']
        cursor.execute("INSERT INTO notices (title, content) VALUES (?, ?)", (title, content))
        conn.commit()
        flash('Notice posted successfully!', 'success')
        return redirect('/admin_dashboard')
    return render_template('post_notice.html')

# Reports Page
@app.route('/reports')
@admin_login_required
def reports():
    # Placeholder for future reports data fetching and processing
    return render_template('reports.html')

# Manage Attendance Page
@app.route('/manage_attendance')
@admin_login_required
def manage_attendance():
    # Placeholder for attendance data fetching and processing
    return render_template('manage_attendance.html')

# Run Server
if __name__ == '__main__':
    app.run(debug=True)
