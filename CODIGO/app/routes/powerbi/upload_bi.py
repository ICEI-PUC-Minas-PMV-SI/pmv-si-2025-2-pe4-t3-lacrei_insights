# app/routes/etl/upload_bi.py
import json
from flask import Blueprint, jsonify, render_template
from sqlalchemy import text
from app.db.engine import get_engine
from flasgger import swag_from

bp_upload_bi = Blueprint("upload_bi", __name__)
engine = get_engine()

@bp_upload_bi.route("/upload/bi", methods=["POST"])
@swag_from({
    "tags": ["ETL", "BI"],
    "summary": "Confirmação de pipeline BI (sem Power BI) — agora usamos graficos.html",
    "responses": {200: {"description": "OK"}}
})
def upload_bi():
    # Mantém a rota de POST que você pediu; agora só confirma sucesso.
    return jsonify({"sucesso": True, "mensagem": "Pipeline BI ativo. Use GET /bi/graficos para ver os gráficos."}), 200


@bp_upload_bi.route("/bi/graficos", methods=["GET"])
@swag_from({
    "tags": ["ETL", "BI"],
    "summary": "Renderiza o dashboard HTML com gráficos da camada MART",
    "responses": {200: {"description": "OK"}}
})
def bi_graficos():
    """
    Lê o schema lacreisaude_mart e prepara dados para o template graficos.html (Chart.js).
    Gráficos:
      - Pacientes por mês (total) e % ativos
      - Pacientes por faixa etária (mês mais recente)
      - Pacientes por tipo de deficiência (mês mais recente, top 10)
      - Profissionais: top 10 especialidades por atendimentos
      - Série mensal de atendimentos e taxa de conclusão
    """
    with engine.begin() as conn:
        # 1) patients – série mensal
        q_patients_month = """
            SELECT period_month::date AS month,
                   SUM(total_patients) AS total_patients,
                   ROUND(AVG(active_percentage), 2) AS avg_active_pct
            FROM lacreisaude_mart.patients
            GROUP BY 1
            ORDER BY 1
        """
        patients_month = [dict(r) for r in conn.execute(text(q_patients_month)).mappings().all()]

        # 2) patients – distribuição por faixa etária no mês mais recente
        q_last_month = "SELECT MAX(period_month)::date AS last_month FROM lacreisaude_mart.patients"
        last_month = conn.execute(text(q_last_month)).scalar()
        patients_age = []
        if last_month:
            q_age = """
                SELECT age_group,
                       SUM(total_patients) AS total_patients,
                       ROUND(AVG(active_percentage), 2) AS avg_active_pct
                FROM lacreisaude_mart.patients
                WHERE period_month = :m
                GROUP BY 1
                ORDER BY 2 DESC
            """
            patients_age = [dict(r) for r in conn.execute(text(q_age), {"m": last_month}).mappings().all()]

        # 3) patient_disability – top 10 no mês mais recente
        disability = []
        if last_month:
            q_disab = """
                SELECT disability_type, total_patients
                FROM lacreisaude_mart.patient_disability
                WHERE period_month = :m
                ORDER BY total_patients DESC NULLS LAST
                LIMIT 10
            """
            disability = [dict(r) for r in conn.execute(text(q_disab), {"m": last_month}).mappings().all()]

        # 4) professionals – top 10 especialidades por número de atendimentos
        q_prof_spec = """
            SELECT COALESCE(specialty, 'Não informada') AS specialty,
                   SUM(total_appointments) AS total_appointments,
                   ROUND(AVG(avg_feedback_rating), 2) AS avg_rating
            FROM lacreisaude_mart.professionals
            GROUP BY 1
            ORDER BY 2 DESC NULLS LAST
            LIMIT 10
        """
        prof_spec = [dict(r) for r in conn.execute(text(q_prof_spec)).mappings().all()]

        # 5) professional_appointments – série mensal (total e taxa de conclusão média)
        q_prof_series = """
            SELECT appointment_period::date AS month,
                   SUM(total_appointments) AS total_appointments,
                   ROUND(AVG(completion_rate), 2) AS avg_completion_rate
            FROM lacreisaude_mart.professional_appointments
            GROUP BY 1
            ORDER BY 1
        """
        prof_series = [dict(r) for r in conn.execute(text(q_prof_series)).mappings().all()]

    # Empacota para o template (Chart.js usa arrays simples)
    data = {
        "patients_month": {
            "labels": [str(r["month"]) for r in patients_month],
            "totals": [int(r["total_patients"] or 0) for r in patients_month],
            "active_pct": [float(r["avg_active_pct"] or 0) for r in patients_month],
        },
        "patients_age": {
            "labels": [r["age_group"] for r in patients_age],
            "totals": [int(r["total_patients"] or 0) for r in patients_age],
            "active_pct": [float(r["avg_active_pct"] or 0) for r in patients_age],
            "last_month": str(last_month) if last_month else None
        },
        "disability": {
            "labels": [r["disability_type"] for r in disability],
            "totals": [int(r["total_patients"] or 0) for r in disability],
            "last_month": str(last_month) if last_month else None
        },
        "prof_spec": {
            "labels": [r["specialty"] for r in prof_spec],
            "totals": [int(r["total_appointments"] or 0) for r in prof_spec],
            "avg_rating": [float(r["avg_rating"] or 0) for r in prof_spec],
        },
        "prof_series": {
            "labels": [str(r["month"]) for r in prof_series],
            "totals": [int(r["total_appointments"] or 0) for r in prof_series],
            "completion": [float(r["avg_completion_rate"] or 0) for r in prof_series],
        }
    }

    return render_template("graficos.html", datasets=data)  # NÃO usar json.dumps aqui
