from flask import Flask , render_template,request ,redirect, session
from models import init_db, get_db_connection


app = Flask(__name__)
app.secret_key = 'secret123'

init_db()

@app.route('/')
def home():
    return "Tutor Booking System Running 🚀"


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

        cursor.execute('''
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        ''', (name, email, password, role))

        conn.commit()
        conn.close()

        return "User Registered Successfully ✅"

    return render_template('register.html')


# Login Route
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
            # store session
            session['user_id'] = user['id']
            session['role'] = user['role']
            session['name'] = user['name']

            return redirect('/add-slot')
        else:
            return "Invalid Credentials ❌"

    return render_template('login.html')



# Adding Slots
@app.route('/add-slot', methods=['GET', 'POST'])
def add_slot():
    if 'user_id' not in session:
        return redirect('/login')

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

#View Slots (Tutor)
@app.route('/my-slots')
def my_slots():
    if 'user_id' not in session:
        return redirect('/login')

    tutor_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM slots WHERE tutor_id = ?
    ''', (tutor_id,))

    slots = cursor.fetchall()
    conn.close()

    return render_template('view_slots.html', slots=slots)


# All-slots (Student)
@app.route('/all-slots')
def all_slots():
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT * FROM slots WHERE is_booked = 0
    ''')

    slots = cursor.fetchall()
    conn.close()

    return render_template('all_slots.html', slots=slots)

#Slot-Booking
@app.route('/book/<int:slot_id>')
def book_slot(slot_id):
    if 'user_id' not in session:
        return redirect('/login')

    student_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get slot info
    cursor.execute('SELECT * FROM slots WHERE id = ?', (slot_id,))
    slot = cursor.fetchone()

    if slot is None:
        return "Slot not found ❌"

    # Insert into bookings table
    cursor.execute('''
        INSERT INTO bookings (student_id, tutor_id, slot_id, status)
        VALUES (?, ?, ?, ?)
    ''', (student_id, slot['tutor_id'], slot_id, 'booked'))

    # Update slot as booked
    cursor.execute('''
        UPDATE slots SET is_booked = 1 WHERE id = ?
    ''', (slot_id,))

    conn.commit()
    conn.close()

    return "Slot Booked Successfully ✅"

# My bookings
@app.route('/my-bookings')
def my_bookings():
    if 'user_id' not in session:
        return redirect('/login')

    student_id = session['user_id']

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT bookings.*, slots.date, slots.time
        FROM bookings
        JOIN slots ON bookings.slot_id = slots.id
        WHERE bookings.student_id = ?
    ''', (student_id,))

    bookings = cursor.fetchall()
    conn.close()

    return render_template('bookings.html', bookings=bookings)

# Cancel-booking 
@app.route('/cancel/<int:booking_id>')
def cancel_booking(booking_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get slot_id
    cursor.execute('SELECT slot_id FROM bookings WHERE id = ?', (booking_id,))
    booking = cursor.fetchone()

    if booking:
        slot_id = booking['slot_id']

        # Update slot back to available
        cursor.execute('''
            UPDATE slots SET is_booked = 0 WHERE id = ?
        ''', (slot_id,))

        # Update booking status
        cursor.execute('''
            UPDATE bookings SET status = 'cancelled' WHERE id = ?
        ''', (booking_id,))

        conn.commit()

    conn.close()

    return redirect('/my-bookings')


# Dashboard
@app.route('/dashboard')
def dashboard():
    if 'user_id' in session:
        return f"Welcome {session['name']} ({session['role']}) 🎉"
    else:
        return redirect('/login')
    

# logout Route
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')



if __name__ == '__main__':
    app.run(debug=True)