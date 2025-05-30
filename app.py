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
                  password TEXT NOT NULL,
                  bio TEXT,
                  interests TEXT)''')
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
    c.execute('''CREATE TABLE IF NOT EXISTS messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER,
                  user_id INTEGER,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (group_id) REFERENCES groups(id),
                  FOREIGN KEY (user_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS tags
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL UNIQUE)''')
    c.execute('''CREATE TABLE IF NOT EXISTS group_tags
                 (group_id INTEGER,
                  tag_id INTEGER,
                  FOREIGN KEY (group_id) REFERENCES groups(id),
                  FOREIGN KEY (tag_id) REFERENCES tags(id),
                  PRIMARY KEY (group_id, tag_id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS private_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  sender_id INTEGER,
                  receiver_id INTEGER,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (sender_id) REFERENCES users(id),
                  FOREIGN KEY (receiver_id) REFERENCES users(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS announcements
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  group_id INTEGER,
                  content TEXT NOT NULL,
                  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (group_id) REFERENCES groups(id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS notifications
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  user_id INTEGER,
                  group_id INTEGER,
                  message_id INTEGER,
                  announcement_id INTEGER,
                  type TEXT NOT NULL,
                  read BOOLEAN DEFAULT FALSE,
                  FOREIGN KEY (user_id) REFERENCES users(id),
                  FOREIGN KEY (group_id) REFERENCES groups(id),
                  FOREIGN KEY (message_id) REFERENCES messages(id),
                  FOREIGN KEY (announcement_id) REFERENCES announcements(id))''')
    conn.commit()
    conn.close()

# Migrate existing database
def migrate_db():
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    try:
        c.execute("ALTER TABLE users ADD COLUMN bio TEXT")
        c.execute("ALTER TABLE users ADD COLUMN interests TEXT")
    except sqlite3.OperationalError:
        pass  # Columns already exist
    conn.commit()
    conn.close()

# Prevent caching during development
@app.after_request
def add_header(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "0"
    return response

# Home route
@app.route('/')
def index():
    try:
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session.get('user_id', 0),))
        notification_count = c.fetchone()[0]
        conn.close()
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    return render_template('index.html', notification_count=notification_count)

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
        tags = request.form['tags'].split(',')
        tags = [tag.strip() for tag in tags if tag.strip()]
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        c.execute("INSERT INTO groups (name, subject, description, creator_id) VALUES (?, ?, ?, ?)",
                  (name, subject, description, session['user_id']))
        group_id = c.lastrowid
        c.execute("INSERT OR IGNORE INTO group_members (user_id, group_id) VALUES (?, ?)",
                  (session['user_id'], group_id))
        for tag in tags:
            c.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag,))
            c.execute("SELECT id FROM tags WHERE name = ?", (tag,))
            tag_id = c.fetchone()[0]
            c.execute("INSERT INTO group_tags (group_id, tag_id) VALUES (?, ?)", (group_id, tag_id))
        conn.commit()
        conn.close()
        flash('Group created successfully!', 'success')
        return redirect(url_for('groups'))
    try:
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session.get('user_id', 0),))
        notification_count = c.fetchone()[0]
        conn.close()
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    return render_template('create_group.html', notification_count=notification_count)

# List all groups route
@app.route('/groups')
def groups():
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT groups.id, groups.name, groups.subject, groups.description, users.username "
              "FROM groups JOIN users ON groups.creator_id = users.id")
    groups = c.fetchall()
    tags_dict = {}
    for group in groups:
        c.execute("SELECT tags.name FROM tags JOIN group_tags ON tags.id = group_tags.tag_id WHERE group_tags.group_id = ?", (group[0],))
        tags_dict[group[0]] = c.fetchall()
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session.get('user_id', 0),))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    return render_template('groups.html', groups=groups, tags_dict=tags_dict, notification_count=notification_count)

# Join group route
@app.route('/join_group/<int:group_id>')
def join_group(group_id):
    if 'user_id' not in session:
        flash('Please log in to join a group.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    try:
        c.execute("INSERT INTO group_members (user_id, group_id) VALUES (?, ?)", (session['user_id'], group_id))
        conn.commit()
        flash('Joined group successfully!', 'success')
    except sqlite3.IntegrityError:
        flash('You are already a member of this group.', 'danger')
    conn.close()
    return redirect(url_for('groups'))

# Leave group route
@app.route('/leave_group/<int:group_id>')
def leave_group(group_id):
    if 'user_id' not in session:
        flash('Please log in to leave a group.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    group = c.fetchone()
    if not group:
        flash('Group not found.', 'danger')
        conn.close()
        return redirect(url_for('my_groups'))
    if group[0] == session['user_id']:
        flash('You cannot leave a group you created. Consider deleting it instead.', 'danger')
        conn.close()
        return redirect(url_for('group_details', group_id=group_id))
    c.execute("DELETE FROM group_members WHERE user_id = ? AND group_id = ?", (session['user_id'], group_id))
    if c.rowcount == 0:
        flash('You are not a member of this group.', 'danger')
    else:
        flash('You have left the group.', 'success')
    conn.commit()
    conn.close()
    return redirect(url_for('my_groups'))

# Delete group route
@app.route('/delete_group/<int:group_id>')
def delete_group(group_id):
    if 'user_id' not in session:
        flash('Please log in to delete a group.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    group = c.fetchone()
    if not group:
        flash('Group not found.', 'danger')
        conn.close()
        return redirect(url_for('my_groups'))
    if group[0] != session['user_id']:
        flash('Only the creator can delete this group.', 'danger')
        conn.close()
        return redirect(url_for('group_details', group_id=group_id))
    c.execute("DELETE FROM messages WHERE group_id = ?", (group_id,))
    c.execute("DELETE FROM group_members WHERE group_id = ?", (group_id,))
    c.execute("DELETE FROM group_tags WHERE group_id = ?", (group_id,))
    c.execute("DELETE FROM announcements WHERE group_id = ?", (group_id,))
    c.execute("DELETE FROM notifications WHERE group_id = ?", (group_id,))
    c.execute("DELETE FROM groups WHERE id = ?", (group_id,))
    conn.commit()
    flash('Group deleted successfully.', 'success')
    conn.close()
    return redirect(url_for('my_groups'))

# My groups route
@app.route('/my_groups')
def my_groups():
    if 'user_id' not in session:
        flash('Please log in to view your groups.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT groups.id, groups.name, groups.subject, groups.description, users.username "
              "FROM groups JOIN users ON groups.creator_id = users.id "
              "JOIN group_members ON groups.id = group_members.group_id "
              "WHERE group_members.user_id = ?", (session['user_id'],))
    groups = c.fetchall()
    tags_dict = {}
    for group in groups:
        c.execute("SELECT tags.name FROM tags JOIN group_tags ON tags.id = group_tags.tag_id WHERE group_tags.group_id = ?", (group[0],))
        tags_dict[group[0]] = c.fetchall()
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session['user_id'],))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    return render_template('my_groups.html', groups=groups, tags_dict=tags_dict, notification_count=notification_count)

# Group details and message board route
@app.route('/group/<int:group_id>', methods=['GET', 'POST'])
def group_details(group_id):
    if 'user_id' not in session:
        flash('Please log in to view group details.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    # Check if user is a member of the group
    c.execute("SELECT * FROM group_members WHERE user_id = ? AND group_id = ?",
              (session['user_id'], group_id))
    is_member = c.fetchone()
    if not is_member:
        flash('You must join this group to view details or post messages.', 'danger')
        conn.close()
        return redirect(url_for('groups'))
    # Get group details
    c.execute("SELECT groups.id, groups.name, groups.subject, groups.description, users.username "
              "FROM groups JOIN users ON groups.creator_id = users.id "
              "WHERE groups.id = ?", (group_id,))
    group = c.fetchone()
    if not group:
        flash('Group not found.', 'danger')
        conn.close()
        return redirect(url_for('groups'))
    # Get group members
    c.execute("SELECT users.username FROM users JOIN group_members ON users.id = group_members.user_id "
              "WHERE group_members.group_id = ?", (group_id,))
    members = c.fetchall()
    # Get tags
    c.execute("SELECT tags.name FROM tags JOIN group_tags ON tags.id = group_tags.tag_id "
              "WHERE group_tags.group_id = ?", (group_id,))
    tags = c.fetchall()
    # Get latest announcement
    c.execute("SELECT content, timestamp FROM announcements WHERE group_id = ? ORDER BY timestamp DESC LIMIT 1", (group_id,))
    announcement = c.fetchone()
    # Handle message posting
    if request.method == 'POST':
        content = request.form['content']
        if content:
            c.execute("INSERT INTO messages (group_id, user_id, content) VALUES (?, ?, ?)",
                      (group_id, session['user_id'], content))
            message_id = c.lastrowid
            c.execute("SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?",
                      (group_id, session['user_id']))
            members_to_notify = c.fetchall()
            for member in members_to_notify:
                c.execute("INSERT INTO notifications (user_id, group_id, message_id, type) VALUES (?, ?, ?, ?)",
                          (member[0], group_id, message_id, 'message'))
            conn.commit()
            flash('Message posted!', 'success')
        else:
            flash('Message cannot be empty.', 'danger')
    # Fetch messages after handling POST to include the new message
    c.execute("SELECT messages.content, users.username, messages.timestamp "
              "FROM messages JOIN users ON messages.user_id = users.id "
              "WHERE messages.group_id = ? ORDER BY messages.timestamp", (group_id,))
    messages = c.fetchall()
    # Mark notifications as read
    c.execute("UPDATE notifications SET read = TRUE WHERE user_id = ? AND group_id = ?",
              (session['user_id'], group_id))
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session['user_id'],))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    return render_template('group.html', group=group, members=members, messages=messages, tags=tags, announcement=announcement, notification_count=notification_count)

# Post announcement route
@app.route('/group/<int:group_id>/announcement', methods=['POST'])
def post_announcement(group_id):
    if 'user_id' not in session:
        flash('Please log in.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT creator_id FROM groups WHERE id = ?", (group_id,))
    group = c.fetchone()
    if not group or group[0] != session['user_id']:
        flash('Only the creator can post announcements.', 'danger')
        conn.close()
        return redirect(url_for('group_details', group_id=group_id))
    content = request.form['announcement']
    if content:
        c.execute("INSERT INTO announcements (group_id, content) VALUES (?, ?)", (group_id, content))
        announcement_id = c.lastrowid
        c.execute("SELECT user_id FROM group_members WHERE group_id = ? AND user_id != ?",
                  (group_id, session['user_id']))
        members = c.fetchall()
        for member in members:
            c.execute("INSERT INTO notifications (user_id, group_id, announcement_id, type) VALUES (?, ?, ?, ?)",
                      (member[0], group_id, announcement_id, 'announcement'))
        conn.commit()
        flash('Announcement posted!', 'success')
    else:
        flash('Announcement cannot be empty.', 'danger')
    conn.close()
    return redirect(url_for('group_details', group_id=group_id))

# Search groups route
@app.route('/search_groups', methods=['GET', 'POST'])
def search_groups():
    if request.method == 'POST':
        search_query = request.form['search_query']
        search_query = f"%{search_query}%"
        conn = sqlite3.connect('study_groups.db')
        c = conn.cursor()
        c.execute("SELECT DISTINCT groups.id, groups.name, groups.subject, groups.description, users.username "
                  "FROM groups JOIN users ON groups.creator_id = users.id "
                  "LEFT JOIN group_tags ON groups.id = group_tags.group_id "
                  "LEFT JOIN tags ON group_tags.tag_id = tags.id "
                  "WHERE groups.name LIKE ? OR groups.subject LIKE ? OR tags.name LIKE ?",
                  (search_query, search_query, search_query))
        groups = c.fetchall()
        tags_dict = {}
        for group in groups:
            c.execute("SELECT tags.name FROM tags JOIN group_tags ON tags.id = group_tags.tag_id WHERE group_tags.group_id = ?", (group[0],))
            tags_dict[group[0]] = c.fetchall()
        try:
            c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                      (session.get('user_id', 0),))
            notification_count = c.fetchone()[0]
        except sqlite3.OperationalError:
            init_db()
            notification_count = 0
        conn.close()
        return render_template('groups.html', groups=groups, tags_dict=tags_dict, search_query=search_query[1:-1], notification_count=notification_count)
    return redirect(url_for('groups'))

# Messages route
@app.route('/messages', methods=['GET', 'POST'])
def messages():
    if 'user_id' not in session:
        flash('Please log in to view messages.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    if request.method == 'POST':
        receiver_username = request.form['receiver']
        content = request.form['content']
        c.execute("SELECT id FROM users WHERE username = ?", (receiver_username,))
        receiver = c.fetchone()
        if receiver and content:
            c.execute("INSERT INTO private_messages (sender_id, receiver_id, content) VALUES (?, ?, ?)",
                      (session['user_id'], receiver[0], content))
            conn.commit()
            flash('Message sent!', 'success')
        else:
            flash('Invalid recipient or empty message.', 'danger')
    c.execute("SELECT users.username, private_messages.content, private_messages.timestamp "
              "FROM private_messages JOIN users ON private_messages.sender_id = users.id "
              "WHERE private_messages.receiver_id = ? ORDER BY private_messages.timestamp DESC",
              (session['user_id'],))
    received = c.fetchall()
    c.execute("SELECT users.username, private_messages.content, private_messages.timestamp "
              "FROM private_messages JOIN users ON private_messages.receiver_id = users.id "
              "WHERE private_messages.sender_id = ? ORDER BY private_messages.timestamp DESC",
              (session['user_id'],))
    sent = c.fetchall()
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session['user_id'],))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    return render_template('messages.html', received=received, sent=sent, notification_count=notification_count)

# Profile route
@app.route('/profile', methods=['GET', 'POST'])
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    if request.method == 'POST':
        bio = request.form['bio']
        interests = request.form['interests']
        c.execute("UPDATE users SET bio = ?, interests = ? WHERE id = ?",
                  (bio, interests, session['user_id']))
        conn.commit()
        flash('Profile updated!', 'success')
    c.execute("SELECT username, bio, interests FROM users WHERE id = ?", (session['user_id'],))
    user = c.fetchone()
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session['user_id'],))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    return render_template('profile.html', user=user, notification_count=notification_count)

# View profile route
@app.route('/profile/<username>')
def view_profile(username):
    if 'user_id' not in session:
        flash('Please log in to view profiles.', 'danger')
        return redirect(url_for('login'))
    if username == session.get('username'):
        return redirect(url_for('profile'))  # Redirect to /profile for the logged-in user
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT username, bio, interests FROM users WHERE username = ?", (username,))
    user = c.fetchone()
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session.get('user_id', 0),))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    if not user:
        flash('User not found.', 'danger')
        return redirect(url_for('groups'))
    return render_template('profile.html', user=user, notification_count=notification_count)

# Notifications route
@app.route('/notifications')
def notifications():
    if 'user_id' not in session:
        flash('Please log in to view notifications.', 'danger')
        return redirect(url_for('login'))
    conn = sqlite3.connect('study_groups.db')
    c = conn.cursor()
    c.execute("SELECT notifications.id, groups.name, notifications.type, messages.content, announcements.content, notifications.group_id "
              "FROM notifications "
              "JOIN groups ON notifications.group_id = groups.id "
              "LEFT JOIN messages ON notifications.message_id = messages.id "
              "LEFT JOIN announcements ON notifications.announcement_id = announcements.id "
              "WHERE notifications.user_id = ? AND notifications.read = FALSE "
              "ORDER BY notifications.id DESC",
              (session['user_id'],))
    notifications = c.fetchall()
    try:
        c.execute("SELECT COUNT(*) FROM notifications WHERE user_id = ? AND read = FALSE",
                  (session['user_id'],))
        notification_count = c.fetchone()[0]
    except sqlite3.OperationalError:
        init_db()
        notification_count = 0
    conn.close()
    return render_template('notifications.html', notifications=notifications, notification_count=notification_count)

if __name__ == '__main__':
    init_db()
    migrate_db()
    app.run(host='0.0.0.0', port=5001, debug=True)