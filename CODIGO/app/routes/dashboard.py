from flask import Blueprint, render_template, session, redirect, url_for
from app.routes.metabase_embed import make_signed_embed_url
import os

bp_dashboard = Blueprint('dashboard', __name__)

@bp_dashboard.route('/dashboard')
def dashboard():
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))

    embed_url = None
    error = None
    # Try to build signed embed URL if Metabase is configured
    try:
        dashboard_id = os.environ.get('METABASE_DASHBOARD_ID')
        if dashboard_id:
            embed_url = make_signed_embed_url(dashboard_id, params={}, expiry_seconds=60 * 60)
    except Exception as e:
        error = str(e)

    return render_template('dashboard.html', metabase_embed_url=embed_url, metabase_error=error)
