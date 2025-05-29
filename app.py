from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # Replace with a random string

# Initialize SQLite database
def init_db():
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS groups
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  subject TEXT NOT NULL,
                  description TEXT,
                  creator_id INTEGER,
                  FOREIGN KEY (creator_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_members
                 (user_id INTEGER, group_id INTEGER,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (group_id) REFERENCES groups(id),
                  PRIMARY KEY (user_id, group_id))''')
    conn.commit()
    conn.close()

# Home route
@app.route('/')
def index():
    return render_template('index.html')

# Registration route
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
            conn.commit()
            flash('Registration successful! Please log in.', 'success')
            return redirect(url_for('login'))
        except sqlite3.IntegrityError:
            flash('Username already taken.', 'danger')
        finally:
            conn.close()
    return render_template('register.html')

# Login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user = c.fetchone()
        conn.close()
        if user:
            session['user_id'] = user[0]
            session['username'] = user[1]
            flash('Logged in successfully!', 'success')
            return redirect(url_for('index'))
        flash('Invalid credentials.', 'danger')
    return render_template('login.html')

# Logout route
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    flash('Logged out successfully.', 'success')
    return redirect(url_for('index'))

# Create group route
@app.route('/create_group', methods=['GET', 'POST'])
def create_group():
    if 'user_id' not in session:
        flash('Please log in to create a group.', 'danger')
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        subject = request.form['subject']
        description = request.form['description']
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        c.execute("INSERT INTO groups (name, subject, description, creator_id) VALUES (?, ?, ?, ?)",
                  (name, subject, description, session['user_id']))
        conn.commit()
        conn.close()
        flash('Group created successfully!', 'success')
        return redirect(url_for('groups'))
    return render_template('create_group.html')

# List groups route
@app.route('/groups')
def groups():
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT groups.id, groups.name, groups.subject, groups.description, users.username "
              "FROM groups JOIN users ON groups.creator_id = users.id")
    groups = c.fetchall()
    conn.close()
    return render_template('groups.html', groups=groups)

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)