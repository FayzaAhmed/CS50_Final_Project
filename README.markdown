# Study Group Finder

## Short Description
Study Group Finder is a lightweight web application designed to help students connect and collaborate by creating and joining study groups. With features like group creation, announcements, messaging, and profile customization, it fosters an interactive learning environment tailored to various subjects and interests.

## Overview
Study Group Finder is a web-based application built with Flask that allows users to create, join, and manage study groups. Users can create groups with specific subjects and tags, post announcements, send private messages, edit their profiles, and receive notifications about group activities.

## Features
- **User Authentication**: Register and log in to access personalized features.
- **Group Management**: Create groups with subjects, descriptions, and tags; join or leave groups; delete groups (by creators only).
- **Announcements**: Group creators can post announcements visible to all members.
- **Message Board**: Members can post messages in group message boards, with real-time updates.
- **Private Messaging**: Send private messages to other users.
- **Profile Management**: Edit bio and interests in user profiles.
- **Notifications**: Receive and view notifications for new messages and announcements, with a badge count in the navbar.
- **Search Functionality**: Search for groups by name, subject, or tags.

## Installation

### Prerequisites
- Python 3.x
- Flask
- SQLite3
- Bootstrap 5 (via CDN)

### Setup
1. Clone the repository:
   ```bash
   git clone https://github.com/FayzaAhmed/CS50_Final_Project 
   cd study_group_finder
   ```
2. Install dependencies:
   ```bash
   pip install flask
   ```
3. Initialize the database:
   - The application creates and migrates the SQLite database (`study_groups.db`) automatically on the first run.
4. Run the application:
   ```bash
   python app.py
   ```
5. Open a web browser and go to `http://0.0.0.0:5001`.

## Usage
- **Register**: Create a new account on the `/register` page.
- **Login**: Log in with your credentials on the `/login` page.
- **Create a Group**: Navigate to `/create_group`, fill in the details, and add tags (comma-separated).
- **Join a Group**: View groups on `/groups`, click "Join Group" for any group, then "View Details".
- **Post an Announcement**: As a group creator, go to a group page and use the "Post Announcement" form.
- **Send a Private Message**: Go to `/messages`, enter a recipient username, and send a message.
- **Edit Profile**: Navigate to `/profile` and update your bio or interests.
- **View Notifications**: Click "Notifications" in the navbar to see unread notifications.

## Project Structure
- `app.py`: Main Flask application file with routes and database logic.
- `templates/`: HTML templates for different pages (e.g., `index.html`, `group.html`).
- `static/styles.css`: Custom CSS for styling.
- `study_groups.db`: SQLite database file (created automatically).

## Contributing
1. Fork the repository.
2. Create a new branch: `git checkout -b feature-branch`.
3. Make changes and commit: `git commit -m "description"`.
4. Push to the branch: `git push origin feature-branch`.
5. Submit a pull request.

## Acknowledgments
- Built with [Flask](https://flask.palletsprojects.com/).
- Styled with [Bootstrap 5](https://getbootstrap.com/).
- Inspired by the need for collaborative study environments.
