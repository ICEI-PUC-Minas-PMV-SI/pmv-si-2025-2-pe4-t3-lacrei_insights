from flask import Blueprint, render_template, session, redirect, url_for, jsonify
from sqlalchemy import text
from app.db.engine import get_engine

bp_dashboard = Blueprint('dashboard', __name__)

@bp_dashboard.route('/dashboard')
def dashboard():
    """Renderiza a página do dashboard"""
    if not session.get('logged_in'):
        return redirect(url_for('auth.login'))
    return render_template('dashboard.html')

@bp_dashboard.route('/api/dados-grafico', methods=['GET'])
def obter_dados_grafico():
    """Obtém dados para exibir no gráfico (sem executar ETL)"""
    if not session.get('logged_in'):
        return jsonify({"sucesso": False, "mensagem": "Não autenticado"}), 401
    
    try:
        engine = get_engine()
        with engine.connect() as conn:
            # Busca dados do staging_02 (já processados)
            dados = [dict(r) for r in conn.execute(text("""
                SELECT 
                    id, 
                    created_at, 
                    updated_at, 
                    privacy_policy, 
                    terms_of_use, 
                    profile_type
                FROM lacreisaude_staging_02.lacrei_privacydocument
                ORDER BY id DESC
                LIMIT 100
            """)).mappings().all()]
            
            # Estatísticas para o gráfico
            stats = [dict(r) for r in conn.execute(text("""
                SELECT 
                    profile_type,
                    COUNT(*) as quantidade
                FROM lacreisaude_staging_02.lacrei_privacydocument
                WHERE profile_type IS NOT NULL
                GROUP BY profile_type
                ORDER BY quantidade DESC
            """)).mappings().all()]

        return jsonify({
            "sucesso": True,
            "data": dados,
            "estatisticas": stats
        }), 200

    except Exception as e:
        return jsonify({
            "sucesso": False, 
            "mensagem": f"Erro ao obter dados: {str(e)}"
        }), 500

