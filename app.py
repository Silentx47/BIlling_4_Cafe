from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_mysqldb import MySQL
import bcrypt
from flask import send_from_directory


app = Flask(__name__)
app.secret_key = 'cafe_secret_key_123'

# MySQL config — update these with your details
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'   # ← must be root, not test
app.config['MYSQL_PASSWORD'] = 'ezra4427'   # ← leave empty if no password
app.config['MYSQL_DB'] = 'cafe_db'

mysql = MySQL(app)

@app.route('/coffee-shop.jpg')
def background():
    return send_from_directory('.', 'coffee-shop.jpg')

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password'].encode('utf-8')

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.checkpw(password, user[2].encode('utf-8')):
            session['username'] = username
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password')

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html', username=session['username'])

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)