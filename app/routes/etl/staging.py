from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from psycopg2.errors import UndefinedTable
from app.db.engine import get_engine
from flasgger import swag_from

bp_staging = Blueprint('uploado_staging', __name__)


def _rodar_etl_privacydocument(conn):
    # 0) Verifica se a tabela fonte existe
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacrei_privacydocument LIMIT 1"))
    except ProgrammingError as e:
        # Tabela fonte não existe
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacrei_privacydocument não encontrada."}
        raise

    # 1) Garante schema e tabela de destino
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacrei_privacydocument
        (
            id             INTEGER PRIMARY KEY,
            created_at     TIMESTAMP WITHOUT TIME ZONE,
            updated_at     TIMESTAMP WITHOUT TIME ZONE,
            privacy_policy VARCHAR,
            terms_of_use   VARCHAR,
            profile_type   VARCHAR
        );
    """))

    upsert_sql = """
        WITH src AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER                                        AS id,
                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END                                                                     AS created_at,
                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END                                                                     AS updated_at,
                NULLIF(privacy_policy, '')::VARCHAR                                     AS privacy_policy,
                NULLIF(terms_of_use,   '')::VARCHAR                                     AS terms_of_use,
                NULLIF(profile_type,   '')::VARCHAR                                     AS profile_type
            FROM lacreisaude_staging_01.lacrei_privacydocument
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacrei_privacydocument
                (id, created_at, updated_at, privacy_policy, terms_of_use, profile_type)
            SELECT id, created_at, updated_at, privacy_policy, terms_of_use, profile_type
            FROM src
            ON CONFLICT (id) DO UPDATE SET
                created_at     = EXCLUDED.created_at,
                updated_at     = EXCLUDED.updated_at,
                privacy_policy = EXCLUDED.privacy_policy,
                terms_of_use   = EXCLUDED.terms_of_use,
                profile_type   = EXCLUDED.profile_type
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    inserted = int(row["inseridos"])
    updated  = int(row["atualizados"])
    source   = int(row["elegiveis"])

    # 3) Mensagem amigável
    # mensagem e dicts
    if source == 0:
        return {
            "ok": True,
            "msg": "Nenhum dado elegível na staging_01 (ids não numéricos/vazios).",
            "inserted": inserted, "updated": updated, "source_rows": source
        }

    return {
        "ok": True,
        "msg": f"ETL concluído com sucesso: {inserted} inseridos, {updated} atualizados (de {source} linhas elegíveis).",
        "inserted": inserted, "updated": updated, "source_rows": source
    }



@bp_staging.route('/upload/staging', methods=['GET'])
@swag_from({
    'tags': ['ETL'],
    'summary': '',
    'responses': {
        200: {'description': 'ETL executado e dados retornados do staging_02'},
        500: {'description': 'Erro no backend (ex: tabela fonte não encontrada ou parse de dados)'}
    }
})
def consultar_indicadores_resumo():
    try:
        engine = get_engine()
        with engine.begin() as conn:
            etl = _rodar_etl_privacydocument(conn)
            if not etl.get("ok"):
                return jsonify({"sucesso": False, "mensagem": etl.get("msg")}), 500

            # Amostra do destino já tipado
            dados = [dict(r) for r in conn.execute(text("""
                SELECT id, created_at, updated_at, privacy_policy, terms_of_use, profile_type
                FROM lacreisaude_staging_02.lacrei_privacydocument
                ORDER BY id DESC
                LIMIT 100
            """)).mappings().all()]

        return jsonify({
            "sucesso": True,
            "mensagem": etl["msg"],
            "resumo": {
                "linhas_elegiveis": etl["source_rows"],
                "inseridos": etl["inserted"],
                "atualizados": etl["updated"]
            },
            "data": dados
        }), 200


    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return jsonify({"sucesso": False, "mensagem": "Tabela fonte não encontrada."}), 500
        return jsonify({"sucesso": False, "mensagem": f"Erro de programação SQL: {str(e)}"}), 500

    except Exception as e:
        # Ex.: erro de parse de datas quando o formato não é ISO-8601
        return jsonify({"sucesso": False, "mensagem": f"Erro inesperado: {str(e)}"}), 500
