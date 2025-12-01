from flask import Blueprint, render_template, jsonify
import os
import time
from urllib.parse import quote_plus
import jwt

bp_metabase = Blueprint('metabase', __name__)


def make_signed_embed_url(dashboard_id, params=None, expiry_seconds=60 * 60, fragment=None):
    site_url = os.environ.get('METABASE_SITE_URL')
    secret = os.environ.get('METABASE_SECRET_KEY')
    if site_url is None or secret is None:
        raise RuntimeError('METABASE_SITE_URL and METABASE_SECRET_KEY must be set in environment')
    site_url = site_url.rstrip('/')

    payload = {
        "resource": {"dashboard": int(dashboard_id)},
        "params": params or {},
        "exp": int(time.time()) + int(expiry_seconds)
    }
    token = jwt.encode(payload, secret, algorithm="HS256")
    if isinstance(token, bytes):
        token = token.decode('utf-8')
    # Use raw token as in Metabase examples (no URL-encoding) and allow optional fragment
    frag = fragment or os.environ.get('METABASE_EMBED_FRAGMENT', '') or ''
    embed_url = f"{site_url}/embed/dashboard/{token}{frag}"
    return embed_url


@bp_metabase.route('/metabase/embed')
def metabase_embed_api():
    """Return a short-lived signed embed URL (JSON) for the configured dashboard."""
    dashboard_id = os.environ.get('METABASE_DASHBOARD_ID')
    if not dashboard_id:
        return jsonify({'error': 'METABASE_DASHBOARD_ID not configured'}), 400
    try:
        # short expiry (10 minutes)
        url = make_signed_embed_url(dashboard_id, params={}, expiry_seconds=10 * 60)
        return jsonify({'embed_url': url}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500
