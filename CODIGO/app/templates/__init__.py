from flask import Flask, redirect, url_for, session
from flask import render_template, request
from flasgger import Swagger
from app.swagger_config import swagger_template

def create_app():
    app = Flask(__name__)
    app.secret_key = 'sua_chave_secreta_segura' 

    Swagger(app, template=swagger_template)

    # Rota principal redireciona para login
    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Rotas de login/logout e proteção do Swagger
    from app.routes.auth.login import bp_auth, proteger_apidocs
    app.register_blueprint(bp_auth)
    proteger_apidocs(app)

    # Rotas: etl
    from app.routes.etl.staging import bp_staging
    app.register_blueprint(bp_staging)

    # Rotas: power bi
    #from app.routes.powerbi.upload_bi import bp_powerbi  
    #app.register_blueprint(bp_powerbi)

    return app
