from flask import Flask, render_template, request, redirect, url_for, session
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
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            return render_template('register.html', error="Username already taken")
        finally:
            conn.close()
    return render_template('register.html')

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5001, debug=True)