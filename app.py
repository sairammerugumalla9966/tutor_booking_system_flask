from flask import Flask, render_template, request, redirect, session,flash
from models import init_db, get_db_connection

app = Flask(__name__)
app.secret_key = 'secret123'

init_db()


# Home Route
@app.route('/')
def home():
    return redirect('/login')


# ✅ Register Route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        role = request.form['role']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO users (name, email, password, role)
                VALUES (?, ?, ?, ?)
            ''', (name, email, password, role))

            conn.commit()

            # ✅ Flash success message
            flash("Registration successful! Please login ✅")

            return redirect('/login')

        except:
            flash("Email already exists ❌")
            return redirect('/register')

        finally:
            conn.close()

    return render_template('register.html')


# Admin/View Users dashboard
@app.route('/admin/users')
def view_users():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()

    conn.close()

    return render_template('view_users.html', users=users)

# Admin/View tutors dashboard
@app.route('/admin/tutors')
def view_tutors():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM users 
        WHERE role = 'tutor' AND is_approved = 0
    ''')

    tutors = cursor.fetchall()
    conn.close()

    return render_template('approve_tutors.html', tutors=tutors)

# Admin-tutors-approval
@app.route('/admin/approve/<int:user_id>')
def approve_tutor(user_id):
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'admin':
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE users SET is_approved = 1 WHERE id = ?
    ''', (user_id,))

    conn.commit()
    conn.close()

    return redirect('/admin/tutors')


# ✅ Login Route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            SELECT * FROM users WHERE email = ? AND password = ?
        ''', (email, password))

        user = cursor.fetchone()
        conn.close()

        if user:
            # ✅ Tutor approval check
            if user['role'] == 'tutor' and user['is_approved'] == 0:
                return "Waiting for Admin Approval ⏳"

            # ✅ Store session
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']

            return redirect('/dashboard')

        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')


# ✅ Dashboard (Role-Based)
@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect('/login')

    role = session['role']

    if role == 'student':
        return render_template('student_dashboard.html')

    elif role == 'tutor':
        return render_template('tutor_dashboard.html')

    elif role == 'admin':
        return render_template('admin_dashboard.html')

    else:
        return "Invalid Role ❌"


# ✅ Add Slot (ONLY Tutor)
@app.route('/add-slot', methods=['GET', 'POST'])
def add_slot():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'tutor':
        return "Access Denied ❌"

    if request.method == 'POST':
        date = request.form['date']
        time = request.form['time']
        tutor_id = session['user_id']

        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute('''
            INSERT INTO slots (tutor_id, date, time)
            VALUES (?, ?, ?)
        ''', (tutor_id, date, time))

        conn.commit()
        conn.close()

        return "Slot Added Successfully ✅"

    return render_template('add_slot.html')


# ✅ View Tutor Slots
@app.route('/my-slots')
def my_slots():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'tutor':
        return "Access Denied ❌"

    tutor_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM slots WHERE tutor_id = ?
    ''', (tutor_id,))

    slots = cursor.fetchall()
    conn.close()

    return render_template('view_slots.html', slots=slots)


# ✅ View All Available Slots (ONLY Student)
@app.route('/all-slots')
def all_slots():
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] not in ['student', 'admin']:
        return "Access Denied ❌"

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM slots WHERE is_booked = 0
    ''')

    slots = cursor.fetchall()
    conn.close()

    return render_template('all_slots.html', slots=slots)


# ✅ Book Slot (ONLY Student)
@app.route('/book/<int:slot_id>')
def book_slot(slot_id):
    if 'user_id' not in session:
        return redirect('/login')

    if session['role'] != 'student':
        return "Access Denied ❌"

    student_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Check slot availability
    cursor.execute('SELECT * FROM slots WHERE id = ? AND is_booked = 0', (slot_id,))
    slot = cursor.fetchone()

    if slot is None:
        return "Slot not available ❌"

    # Insert booking
    cursor.execute('''
        INSERT INTO bookings (student_id, tutor_id, slot_id, status)
        VALUES (?, ?, ?, ?)
    ''', (student_id, slot['tutor_id'], slot_id, 'booked'))

    # Mark slot booked
    cursor.execute('''
        UPDATE slots SET is_booked = 1 WHERE id = ?
    ''', (slot_id,))

    conn.commit()
    conn.close()

    return "Slot Booked Successfully ✅"


# ✅ My Bookings (ONLY Student)
@app.route('/my-bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    # ✅ If admin → show all bookings
    if session['role'] == 'admin':
        cursor.execute('''
            SELECT bookings.*, slots.date, slots.time
            FROM bookings
            JOIN slots ON bookings.slot_id = slots.id
        ''')

    # ✅ If student → show only their bookings
    elif session['role'] == 'student':
        student_id = session['user_id']
        cursor.execute('''
            SELECT bookings.*, slots.date, slots.time
            FROM bookings
            JOIN slots ON bookings.slot_id = slots.id
            WHERE bookings.student_id = ?
        ''', (student_id,))

    else:
        return "Access Denied ❌"

    bookings = cursor.fetchall()
    conn.close()

    return render_template('bookings.html', bookings=bookings)

# ✅ Cancel Booking
@app.route('/cancel/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT slot_id FROM bookings WHERE id = ?', (booking_id,))
    booking = cursor.fetchone()

    if booking:
        slot_id = booking['slot_id']

        cursor.execute('UPDATE slots SET is_booked = 0 WHERE id = ?', (slot_id,))
        cursor.execute('UPDATE bookings SET status = "cancelled" WHERE id = ?', (booking_id,))

        conn.commit()

    conn.close()

    return redirect('/my-bookings')


# ✅ Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


if __name__ == '__main__':
    app.run(debug=True)