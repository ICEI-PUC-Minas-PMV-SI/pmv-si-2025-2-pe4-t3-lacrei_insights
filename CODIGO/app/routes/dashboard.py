from flask import Blueprint, render_template, session, redirect, url_for

bp_dashboard = Blueprint('dashboard', __name__)

@bp_dashboard.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')
