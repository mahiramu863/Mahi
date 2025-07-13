from flask import Flask, render_template, request, redirect, url_for, flash, session
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import random
import string
import time
import PyPDF2

app = Flask(__name__)
app.secret_key = os.urandom(24)
app.config['UPLOAD_FOLDER'] = 'uploads'

# In-memory user storage (for demonstration purposes)
users = {}
otps = {}

@app.route('/')
def home():
    return redirect(url_for('signup'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if email in users:
            flash('Email already exists.')
            return redirect(url_for('signup'))

        # In a real app, you would hash the password
        users[email] = {'username': username, 'password': password}
        flash('Signup successful! Please log in.')
        return redirect(url_for('login'))

    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = users.get(email)

        if user and user['password'] == password:
            session['email'] = email
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid credentials.')
            return redirect(url_for('login'))

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

@app.route('/bookstore')
def bookstore():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('bookstore.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if 'email' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'book' not in request.files:
            flash('No file part')
            return redirect(request.url)

        file = request.files['book']

        if file.filename == '':
            flash('No selected file')
            return redirect(request.url)

        if file:
            filename = file.filename
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            text = ""
            with open(filepath, 'rb') as f:
                reader = PyPDF2.PdfReader(f)
                for page in reader.pages:
                    text += page.extract_text()

            return redirect(url_for('book_view', filename=filename))

    return render_template('upload.html')

@app.route('/progress')
def progress():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('progress.html')

@app.route('/track_book')
def track_book():
    if 'email' not in session:
        return redirect(url_for('login'))
    return render_template('track_book.html')

@app.route('/book_view/<filename>')
def book_view(filename):
    if 'email' not in session:
        return redirect(url_for('login'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    text = ""
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()

    return render_template('book_view.html', book_text=text, filename=filename)

@app.route('/generate_mcqs/<filename>', methods=['POST'])
def generate_mcqs(filename):
    if 'email' not in session:
        return redirect(url_for('login'))

    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    text = ""
    with open(filepath, 'rb') as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            text += page.extract_text()

    # Mock AI service
    mcqs = [
        {
            "question": "This is a sample question 1?",
            "options": ["A", "B", "C", "D"],
            "answer": "A"
        },
        {
            "question": "This is a sample question 2?",
            "options": ["A", "B", "C", "D"],
            "answer": "B"
        }
    ]

    return render_template('mcqs.html', mcqs=mcqs)

@app.route('/logout')
def logout():
    session.pop('email', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))

@app.route('/otp_login', methods=['GET', 'POST'])
def otp_login():
    if request.method == 'POST':
        email = request.form['email']
        if email not in users:
            flash('Email not found.')
            return redirect(url_for('otp_login'))

        otp = ''.join(random.choices(string.digits, k=6))
        otps[email] = {'otp': otp, 'timestamp': time.time()}

        # In a real app, you would send this OTP via email
        print(f"OTP for {email}: {otp}")  # Simulate sending OTP

        flash('An OTP has been sent to your email.')
        return redirect(url_for('verify_otp', email=email))

    return render_template('otp_login.html')

@app.route('/verify_otp/<email>', methods=['GET', 'POST'])
def verify_otp(email):
    if request.method == 'POST':
        otp_entered = request.form['otp']
        otp_data = otps.get(email)

        if not otp_data:
            flash('OTP expired or invalid.')
            return redirect(url_for('otp_login'))

        # OTP is valid for 60 seconds
        if time.time() - otp_data['timestamp'] > 60:
            flash('OTP expired.')
            otps.pop(email, None)
            return redirect(url_for('otp_login'))

        if otp_data['otp'] == otp_entered:
            session['email'] = email
            otps.pop(email, None)
            flash('Login successful!')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid OTP.')
            return redirect(url_for('verify_otp', email=email))

    return render_template('verify_otp.html', email=email)

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        if email in users:
            # In a real app, you'd generate a unique token and email a link
            print(f"Password reset link for {email} would be sent here.")
            flash('A password reset link has been sent to your email.')
        else:
            flash('Email not found.')
        return redirect(url_for('forgot_password'))
    return render_template('forgot_password.html')

if __name__ == '__main__':
    app.run(debug=True)
