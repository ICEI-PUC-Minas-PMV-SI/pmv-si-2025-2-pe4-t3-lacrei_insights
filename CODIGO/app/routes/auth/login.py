from flask import Blueprint, session, redirect, request, render_template, url_for
from datetime import datetime, timedelta

bp_auth = Blueprint('auth', __name__)

SESSION_TIMEOUT_MINUTES = 60

@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    session.clear()

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == 'admin' and password == '123456':
            session['logged_in'] = True
            session['username'] = username
            session['login_time'] = datetime.utcnow().isoformat()
            return redirect('/apidocs/')
        else:
            return render_template('login.html', error='Usuário ou senha inválidos.')
    
    return render_template('login.html')

@bp_auth.route('/logout')
def logout():
    session.clear()
    return redirect('/login')


# Middleware: Protege /apidocs/
def proteger_apidocs(app):
    @app.before_request
    def verificar_apidocs():
        caminho = request.path

        if request.path == '/':
            return redirect('/login')

        # libera rotas públicas
        if caminho.startswith('/static') or caminho in ['/login', '/logout']:
            return

        if caminho.startswith('/apidocs'):
            if not session.get('logged_in'):
                return redirect('/login')

            # verifica timeout
            login_time_str = session.get('login_time')
            if login_time_str:
                login_time = datetime.fromisoformat(login_time_str)
                if datetime.utcnow() - login_time > timedelta(minutes=SESSION_TIMEOUT_MINUTES):
                    session.clear()
                    return redirect('/login')
                
    @app.after_request
    def adicionar_cabecalhos_cache(response):
        if request.path.startswith('/apidocs') or request.path.startswith('/login'):
            response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
            response.headers['Pragma'] = 'no-cache'
            response.headers['Expires'] = '-1'
        return response
