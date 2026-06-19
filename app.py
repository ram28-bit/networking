from flask import Flask, render_template, request, session, redirect, url_for
import sqlite3
import subprocess
import os
import psutil
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your-secret-key-here"

from ping3 import ping

def check_host(host):
    try:
        return ping(host) is not None
    except:
        return False


@app.route('/')
def home():
    return render_template('login.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    # If already logged in, go straight to dashboard
    if 'user' in session:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect('users.db')
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        )
        user = cursor.fetchone()

        if user:
            session['user'] = username

            cursor.execute(
                "INSERT INTO login_logs (username, login_time) VALUES (?, ?)",
                (username, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
            )
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

        conn.close()
        return render_template('login.html', error="Invalid username or password")

    return render_template('login.html')

@app.route('/dashboard')
def dashboard():
    # If not logged in, send back to login
    if 'user' not in session:
        return redirect(url_for('login'))

    google = "UP" if check_host("8.8.8.8") else "DOWN"
    cloudflare = "UP" if check_host("1.1.1.1") else "DOWN"

    cpu_usage = psutil.cpu_percent(interval=1)
    memory_usage = psutil.virtual_memory().percent

    alerts = []
    if google == "DOWN":
        alerts.append("Google DNS is DOWN")
    if cloudflare == "DOWN":
        alerts.append("Cloudflare DNS is DOWN")
    if cpu_usage > 80:
        alerts.append("High CPU Usage")
    if memory_usage > 80:
        alerts.append("High Memory Usage")

    return render_template(
        "dashboard.html",
        google=google,
        cloudflare=cloudflare,
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        alerts=alerts
    )

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('login'))

import os

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    from ping3 import ping
print(ping("8.8.8.8"))