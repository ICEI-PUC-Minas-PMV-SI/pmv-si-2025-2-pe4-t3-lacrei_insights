from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from psycopg2.errors import UndefinedTable
from app.db.engine import get_engine
from app.routes.etl.model import _rodar_etl_model
from app.routes.etl.mart import _rodar_etl_mart
from flasgger import swag_from
from app.routes.etl.staging1 import criar_popular_staging1

bp_staging2 = Blueprint('upload_staging', __name__)
engine = get_engine()


def _rodar_etl_privacydocument(conn):
    # 0) Verifica se a tabela fonte existe
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacrei_privacydocument LIMIT 1"))
    except ProgrammingError as e:
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

    # 2) Upsert com limpeza e tipagem
    upsert_sql = """
        WITH src_raw AS (
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
                NULLIF(profile_type,   '')::VARCHAR                                     AS profile_type,
                ROW_NUMBER() OVER (PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER
                                   ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC
                                  ) AS rn
            FROM lacreisaude_staging_01.lacrei_privacydocument
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (
            -- Mantém apenas a última linha por id (rn = 1) para evitar duplicatas no INSERT
            SELECT id, created_at, updated_at, privacy_policy, terms_of_use, profile_type
            FROM src_raw
            WHERE rn = 1
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
    return {
        "ok": True,
        "msg": f"ETL privacydocument: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_appointment(conn):
    """
    Staging_01.lacreiid_appointment  ➜  Staging_02.lacreiid_appointment
    - Renomeia 'date' -> 'appointment_date'
    - Preserva tipos, faz upsert por (id)
    - Cria índices nos campos: appointment_date, professional_id, user_id
    """
    # 0) Verifica se a tabela fonte existe
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_appointment LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_appointment não encontrada."}
        raise

    # 1) Cria schema/tabela/índices de destino conforme seu DDL
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_appointment
        (
            id               VARCHAR PRIMARY KEY,
            created_at       TIMESTAMP WITHOUT TIME ZONE,
            updated_at       TIMESTAMP WITHOUT TIME ZONE,
            appointment_date TIMESTAMP WITHOUT TIME ZONE,
            status           VARCHAR,
            type             VARCHAR,
            professional_id  VARCHAR,
            user_id          VARCHAR,
            agreement_id     VARCHAR
        )
        TABLESPACE pg_default;
    """))

    # Índices (idempotentes)
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_appt2_adate
            ON lacreisaude_staging_02.lacreiid_appointment USING btree
            (appointment_date ASC NULLS LAST)
            TABLESPACE pg_default;

        CREATE INDEX IF NOT EXISTS ix_appt2_prof
            ON lacreisaude_staging_02.lacreiid_appointment USING btree
            (professional_id ASC NULLS LAST)
            TABLESPACE pg_default;

        CREATE INDEX IF NOT EXISTS ix_appt2_user
            ON lacreisaude_staging_02.lacreiid_appointment USING btree
            (user_id ASC NULLS LAST)
            TABLESPACE pg_default;
    """))

    # 2) Upsert
    # Observação: sua staging_01 já está tipada (timestamps/integers), então não aplico TRIM/casts de texto.
    # Se os dados vierem como texto em algum momento, podemos adaptar (como no privacydocument).
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                id::varchar AS id,
                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,
                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,
                CASE
                    WHEN NULLIF(TRIM(date), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(date), '')::timestamptz AT TIME ZONE 'UTC')
                END AS appointment_date,
                status::varchar AS status,
                type::varchar AS type,
                professional_id::varchar AS professional_id,
                user_id::varchar AS user_id,
                agreement_id::varchar AS agreement_id,
                ROW_NUMBER() OVER (PARTITION BY NULLIF(TRIM(id), '')
                                   ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC
                                  ) AS rn
            FROM lacreisaude_staging_01.lacreiid_appointment
            WHERE id IS NOT NULL
        ),
        src AS (
            -- Mantém apenas a última linha por id (rn = 1) para evitar duplicatas
            SELECT id, created_at, updated_at, appointment_date, status, type, professional_id, user_id, agreement_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_appointment
                (id, created_at, updated_at, appointment_date, status, type, professional_id, user_id, agreement_id)
            SELECT
                id, created_at, updated_at, appointment_date, status, type, professional_id, user_id, agreement_id
            FROM src
            ON CONFLICT (id) DO UPDATE SET
                created_at       = EXCLUDED.created_at,
                updated_at       = EXCLUDED.updated_at,
                appointment_date = EXCLUDED.appointment_date,
                status           = EXCLUDED.status,
                type             = EXCLUDED.type,
                professional_id  = EXCLUDED.professional_id,
                user_id          = EXCLUDED.user_id,
                agreement_id     = EXCLUDED.agreement_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL appointment: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_cancellation(conn):
    """
    Staging_01.lacreiid_cancellation  ➜  Staging_02.lacreiid_cancellation

    Renomeações / conversões:
      - id (text) -> cancellation_id (varchar)
      - created_at/updated_at (text) -> timestamp
      - reason (text) -> varchar
      - appointment_id (integer) -> varchar
      - created_by_content_type_id (text) -> integer (quando numérico)
      - created_by_object_d (text) -> created_by_object_id (varchar)
    """
    # 0) Verifica se a tabela fonte existe
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_cancellation LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_cancellation não encontrada."}
        raise

    # 1) Cria schema/tabela de destino (conforme seu DDL)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_cancellation
        (
            cancellation_id           VARCHAR PRIMARY KEY,
            created_at                TIMESTAMP WITHOUT TIME ZONE,
            updated_at                TIMESTAMP WITHOUT TIME ZONE,
            reason                    VARCHAR,
            appointment_id            VARCHAR,
            created_by_content_type_id INTEGER,
            created_by_object_id      VARCHAR
        )
        TABLESPACE pg_default;
    """))

    # 2) Upsert com tipagem/limpeza
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                NULLIF(TRIM(id), '')::varchar AS cancellation_id,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                NULLIF(reason, '')::varchar AS reason,

                -- origem integer, destino varchar
                CASE
                    WHEN appointment_id IS NULL THEN NULL
                    ELSE NULLIF(TRIM(appointment_id::text), '')
                END AS appointment_id,

                CASE
                    WHEN NULLIF(TRIM(created_by_content_type_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(created_by_content_type_id), '')::integer)
                    ELSE NULL
                END AS created_by_content_type_id,

                NULLIF(TRIM(created_by_object_d), '')::varchar AS created_by_object_id,

                ROW_NUMBER() OVER (
                    PARTITION BY NULLIF(TRIM(id), '')
                    ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC
                ) AS rn
            FROM lacreisaude_staging_01.lacreiid_cancellation
            WHERE NULLIF(TRIM(id), '') IS NOT NULL
        ),
        src AS (
            SELECT cancellation_id, created_at, updated_at, reason, appointment_id, created_by_content_type_id, created_by_object_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_cancellation
                (cancellation_id, created_at, updated_at, reason, appointment_id,
                 created_by_content_type_id, created_by_object_id)
            SELECT
                cancellation_id, created_at, updated_at, reason, appointment_id,
                created_by_content_type_id, created_by_object_id
            FROM src
            ON CONFLICT (cancellation_id) DO UPDATE SET
                created_at                = EXCLUDED.created_at,
                updated_at                = EXCLUDED.updated_at,
                reason                    = EXCLUDED.reason,
                appointment_id            = EXCLUDED.appointment_id,
                created_by_content_type_id= EXCLUDED.created_by_content_type_id,
                created_by_object_id      = EXCLUDED.created_by_object_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL cancellation: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_profile(conn):
    """
    Staging_01.lacreiid_profile  ➜  Staging_02.lacreiid_profile

    Mapeamentos / conversões:
      - id (text) -> profile_id (varchar, PK)
      - created_at / updated_at (text) -> timestamp (parse via timestamptz AT TIME ZONE 'UTC')
      - completed (text) -> boolean (true/false com dicionário de valores)
      - *_id (text) -> integer quando numérico (ethnic_group, gender_identity, pronoun, sexual_orientation)
      - user_id (text) -> varchar
      - Demais campos text -> varchar
    """
    # 0) Verifica fonte
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_profile LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_profile não encontrada."}
        raise

    # 1) Cria schema/tabela destino (conforme seu DDL)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_profile
        (
            profile_id           VARCHAR PRIMARY KEY,
            created_at           TIMESTAMP WITHOUT TIME ZONE,
            updated_at           TIMESTAMP WITHOUT TIME ZONE,
            other_ethnic_group   VARCHAR,
            other_gender_identity VARCHAR,
            other_sexual_orientation VARCHAR,
            other_pronoun        VARCHAR,
            other_disability_types VARCHAR,
            other_article        VARCHAR,
            completed            BOOLEAN,
            photo                VARCHAR,
            photo_description    VARCHAR,
            ethnic_group         INTEGER,
            gender_identity      INTEGER,
            pronoun              INTEGER,
            sexual_orientation   INTEGER,
            user_id              VARCHAR
        )
        TABLESPACE pg_default;
    """))

    # 2) Upsert com limpeza/conversões
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                NULLIF(TRIM(id), '')::varchar AS profile_id,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                NULLIF(other_ethnic_group, '')::varchar          AS other_ethnic_group,
                NULLIF(other_gender_identity, '')::varchar       AS other_gender_identity,
                NULLIF(other_sexual_orientation, '')::varchar    AS other_sexual_orientation,
                NULLIF(other_pronoun, '')::varchar               AS other_pronoun,
                NULLIF(other_disability_types, '')::varchar      AS other_disability_types,
                NULLIF(other_article, '')::varchar               AS other_article,

                CASE
                    WHEN NULLIF(LOWER(TRIM(completed)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(completed)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(completed)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS completed,

                NULLIF(photo, '')::varchar                       AS photo,
                NULLIF(photo_description, '')::varchar           AS photo_description,

                CASE
                    WHEN NULLIF(TRIM(ethnic_group_id), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(ethnic_group_id), '')::integer)
                    ELSE NULL
                END AS ethnic_group,

                CASE
                    WHEN NULLIF(TRIM(gender_identity_id), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(gender_identity_id), '')::integer)
                    ELSE NULL
                END AS gender_identity,

                CASE
                    WHEN NULLIF(TRIM(pronoun_id), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(pronoun_id), '')::integer)
                    ELSE NULL
                END AS pronoun,

                CASE
                    WHEN NULLIF(TRIM(sexual_orientation_id), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(sexual_orientation_id), '')::integer)
                    ELSE NULL
                END AS sexual_orientation,

                NULLIF(TRIM(user_id), '')::varchar              AS user_id,

                ROW_NUMBER() OVER (
                    PARTITION BY NULLIF(TRIM(id), '')
                    ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC
                ) AS rn

            FROM lacreisaude_staging_01.lacreiid_profile
            WHERE NULLIF(TRIM(id), '') IS NOT NULL
        ),
        src AS (
            SELECT profile_id, created_at, updated_at, other_ethnic_group, other_gender_identity,
                   other_sexual_orientation, other_pronoun, other_disability_types, other_article,
                   completed, photo, photo_description, ethnic_group, gender_identity, pronoun,
                   sexual_orientation, user_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_profile
                (profile_id, created_at, updated_at, other_ethnic_group, other_gender_identity,
                 other_sexual_orientation, other_pronoun, other_disability_types, other_article,
                 completed, photo, photo_description, ethnic_group, gender_identity, pronoun,
                 sexual_orientation, user_id)
            SELECT
                profile_id, created_at, updated_at, other_ethnic_group, other_gender_identity,
                other_sexual_orientation, other_pronoun, other_disability_types, other_article,
                completed, photo, photo_description, ethnic_group, gender_identity, pronoun,
                sexual_orientation, user_id
            FROM src
            ON CONFLICT (profile_id) DO UPDATE SET
                created_at            = EXCLUDED.created_at,
                updated_at            = EXCLUDED.updated_at,
                other_ethnic_group    = EXCLUDED.other_ethnic_group,
                other_gender_identity = EXCLUDED.other_gender_identity,
                other_sexual_orientation = EXCLUDED.other_sexual_orientation,
                other_pronoun         = EXCLUDED.other_pronoun,
                other_disability_types= EXCLUDED.other_disability_types,
                other_article         = EXCLUDED.other_article,
                completed             = EXCLUDED.completed,
                photo                 = EXCLUDED.photo,
                photo_description     = EXCLUDED.photo_description,
                ethnic_group          = EXCLUDED.ethnic_group,
                gender_identity       = EXCLUDED.gender_identity,
                pronoun               = EXCLUDED.pronoun,
                sexual_orientation    = EXCLUDED.sexual_orientation,
                user_id               = EXCLUDED.user_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL profile: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_profile_disability_types(conn):
    """
    Staging_01.lacreiid_profile_disability_types ➜ Staging_02.lacreiid_profile_disability_types
    """
    # 0) Verifica fonte
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_profile_disability_types LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_profile_disability_types não encontrada."}
        raise
    # 1) Cria schema/tabela destino ANTES de qualquer SELECT
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_profile_disability_types
        (
            id                INTEGER PRIMARY KEY,
            profile_id        VARCHAR,
            disabilitytype_id INTEGER
        )
        TABLESPACE pg_default;

        ALTER TABLE IF EXISTS lacreisaude_staging_02.lacreiid_profile_disability_types
            OWNER TO postgres;
    """))

    # 2) Upsert com limpeza e tipagem
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER                                 AS id,
                NULLIF(TRIM(profile_id), '')::VARCHAR                           AS profile_id,
                CASE
                    WHEN NULLIF(TRIM(disabilitytype_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(disabilitytype_id), '')::INTEGER)
                    ELSE NULL
                END                                                             AS disabilitytype_id,
                ROW_NUMBER() OVER (
                    PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER
                    ORDER BY (CASE WHEN NULLIF(TRIM(id), '') IS NULL THEN to_timestamp(0) ELSE to_timestamp(0) END) -- stable order
                ) AS rn
            FROM lacreisaude_staging_01.lacreiid_profile_disability_types
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'   -- garante PK numérico
        ),
        src AS (
            SELECT id, profile_id, disabilitytype_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_profile_disability_types
                (id, profile_id, disabilitytype_id)
            SELECT id, profile_id, disabilitytype_id
            FROM src
            ON CONFLICT (id) DO UPDATE SET
                profile_id        = EXCLUDED.profile_id,
                disabilitytype_id = EXCLUDED.disabilitytype_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL profile_disability_types: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_report(conn):
    """
    Staging_01.lacreiid_report  ➜  Staging_02.lacreiid_report

    Mapeamentos / conversões:
      - id (text)                       -> report_id (varchar, PK)
      - created_at / updated_at (text)  -> timestamp (parse via timestamptz AT TIME ZONE 'UTC')
      - feedback (text)                 -> varchar
      - eval (text)                     -> integer quando numérico
      - appointment_id (integer)        -> integer
      - created_by_content_type_id (text) -> integer quando numérico
      - created_by_object_id (text)     -> varchar
    """
    # 0) Verifica fonte
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_report LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_report não encontrada."}
        raise

    # 1) Cria schema/tabela destino (DDL corrigido)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_report
        (
            report_id                   VARCHAR PRIMARY KEY,
            created_at                  TIMESTAMP WITHOUT TIME ZONE,
            updated_at                  TIMESTAMP WITHOUT TIME ZONE,
            feedback                    VARCHAR,
            eval                        INTEGER,
            appointment_id              VARCHAR,
            created_by_content_type_id  INTEGER,
            created_by_object_id        VARCHAR
        );
    """))

    # (Opcional) Índices úteis para consultas
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_report_created_at
            ON lacreisaude_staging_02.lacreiid_report (created_at);

        CREATE INDEX IF NOT EXISTS ix_report_appointment
            ON lacreisaude_staging_02.lacreiid_report (appointment_id);
    """))

    # 2) Upsert com limpeza/conversões
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                NULLIF(TRIM(id), '')::varchar AS report_id,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                NULLIF(feedback, '')::varchar AS feedback,

                CASE
                    WHEN NULLIF(TRIM(eval), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(eval), '')::integer)
                    ELSE NULL
                END AS eval,

                appointment_id::varchar AS appointment_id,

                CASE
                    WHEN NULLIF(TRIM(created_by_content_type_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(created_by_content_type_id), '')::integer)
                    ELSE NULL
                END AS created_by_content_type_id,

                NULLIF(TRIM(created_by_object_id), '')::varchar AS created_by_object_id,

                ROW_NUMBER() OVER (
                    PARTITION BY NULLIF(TRIM(id), '')
                    ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC
                ) AS rn

            FROM lacreisaude_staging_01.lacreiid_report
            WHERE NULLIF(TRIM(id), '') IS NOT NULL
        ),
        src AS (
            SELECT report_id, created_at, updated_at, feedback, eval, appointment_id, created_by_content_type_id, created_by_object_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_report
                (report_id, created_at, updated_at, feedback, eval,
                 appointment_id, created_by_content_type_id, created_by_object_id)
            SELECT
                report_id, created_at, updated_at, feedback, eval,
                appointment_id, created_by_content_type_id, created_by_object_id
            FROM src
            ON CONFLICT (report_id) DO UPDATE SET
                created_at                 = EXCLUDED.created_at,
                updated_at                 = EXCLUDED.updated_at,
                feedback                   = EXCLUDED.feedback,
                eval                       = EXCLUDED.eval,
                appointment_id             = EXCLUDED.appointment_id,
                created_by_content_type_id = EXCLUDED.created_by_content_type_id,
                created_by_object_id       = EXCLUDED.created_by_object_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL report: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_user(conn):
    """
    Staging_01.lacreiid_user  ➜  Staging_02.lacreiid_user

    Mapeamentos / conversões:
      - id (text)                    -> user_id (varchar, PK)
      - password (text)              -> password (varchar)
      - is_superuser / is_staff / is_active / email_verified /
        accepted_privacy_document / newsletter_subscribed /
        phone_verified / is_18_years_old_or_more (text) -> boolean
      - created_at / updated_at / last_login / birth_date /
        phone_verification_token_expires_at (text) -> timestamp (parse via timestamptz AT TIME ZONE 'UTC')
      - email / first_name / last_name / phone / phone_verification_token / logged_as (text) -> varchar
      - privacy_document_id (text)   -> integer quando numérico
    """
    # 0) Verifica se a tabela fonte existe
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_user LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_user não encontrada."}
        raise

    # 1) Cria schema/tabela destino (DDL corrigido e válido)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_user
        (
            user_id                              VARCHAR PRIMARY KEY,
            password                             VARCHAR,
            is_superuser                         BOOLEAN,
            is_staff                             BOOLEAN,
            is_active                            BOOLEAN,
            created_at                           TIMESTAMP WITHOUT TIME ZONE,
            updated_at                           TIMESTAMP WITHOUT TIME ZONE,
            email                                VARCHAR,
            first_name                           VARCHAR,
            last_name                            VARCHAR,
            birth_date                           TIMESTAMP WITHOUT TIME ZONE,
            is_18_years_old_or_more             BOOLEAN,
            last_login                           TIMESTAMP WITHOUT TIME ZONE,
            email_verified                       BOOLEAN,
            accepted_privacy_document            BOOLEAN,
            newsletter_subscribed                BOOLEAN,
            phone                                VARCHAR,
            phone_verified                       BOOLEAN,
            phone_verification_token             VARCHAR,
            phone_verification_token_expires_at  TIMESTAMP WITHOUT TIME ZONE,
            privacy_document_id                  INTEGER,
            logged_as                            VARCHAR
        )
        TABLESPACE pg_default;

        ALTER TABLE IF EXISTS lacreisaude_staging_02.lacreiid_user
            OWNER TO postgres;
    """))

    # (Opcional) Índices úteis para consultas
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_user_email
            ON lacreisaude_staging_02.lacreiid_user (email);
        CREATE INDEX IF NOT EXISTS ix_user_last_login
            ON lacreisaude_staging_02.lacreiid_user (last_login);
        CREATE INDEX IF NOT EXISTS ix_user_privdoc
            ON lacreisaude_staging_02.lacreiid_user (privacy_document_id);
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                NULLIF(TRIM(id), '')::varchar AS user_id,
                NULLIF(password, '')::varchar AS password,

                -- Boolean normalizer
                -- aceita: true/false, t/f, 1/0, yes/no, y/n, sim/não, s/n
                -- qualquer outro valor vira NULL
                CASE
                    WHEN NULLIF(LOWER(TRIM(is_superuser)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(is_superuser)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(is_superuser)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS is_superuser,

                CASE
                    WHEN NULLIF(LOWER(TRIM(is_staff)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(is_staff)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(is_staff)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS is_staff,

                CASE
                    WHEN NULLIF(LOWER(TRIM(is_active)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(is_active)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(is_active)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS is_active,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                NULLIF(email, '')::varchar      AS email,
                NULLIF(first_name, '')::varchar AS first_name,
                NULLIF(last_name, '')::varchar  AS last_name,

                CASE
                    WHEN NULLIF(TRIM(birth_date), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(birth_date), '')::timestamptz AT TIME ZONE 'UTC')
                END AS birth_date,

                CASE
                    WHEN NULLIF(LOWER(TRIM(is_18_years_old_or_more)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(is_18_years_old_or_more)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(is_18_years_old_or_more)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS is_18_years_old_or_more,

                CASE
                    WHEN NULLIF(TRIM(last_login), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(last_login), '')::timestamptz AT TIME ZONE 'UTC')
                END AS last_login,

                CASE
                    WHEN NULLIF(LOWER(TRIM(email_verified)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(email_verified)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(email_verified)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS email_verified,

                CASE
                    WHEN NULLIF(LOWER(TRIM(accepted_privacy_document)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(accepted_privacy_document)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(accepted_privacy_document)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS accepted_privacy_document,

                CASE
                    WHEN NULLIF(LOWER(TRIM(newsletter_subscribed)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(newsletter_subscribed)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(newsletter_subscribed)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS newsletter_subscribed,

                NULLIF(phone, '')::varchar AS phone,

                CASE
                    WHEN NULLIF(LOWER(TRIM(phone_verified)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(phone_verified)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(phone_verified)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS phone_verified,

                NULLIF(phone_verification_token, '')::varchar AS phone_verification_token,

                CASE
                    WHEN NULLIF(TRIM(phone_verification_token_expires_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(phone_verification_token_expires_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS phone_verification_token_expires_at,

                CASE
                    WHEN NULLIF(TRIM(privacy_document_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(privacy_document_id), '')::integer)
                    ELSE NULL
                END AS privacy_document_id,

                NULLIF(logged_as, '')::varchar AS logged_as

            FROM lacreisaude_staging_01.lacreiid_user
            WHERE NULLIF(TRIM(id), '') IS NOT NULL
        ),
        src AS (
            -- Keep only the most recent row per user_id
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY COALESCE(updated_at, created_at) DESC NULLS LAST) AS rn
                FROM src_raw
            ) t WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_user
            (
                user_id, password, is_superuser, is_staff, is_active,
                created_at, updated_at, email, first_name, last_name,
                birth_date, is_18_years_old_or_more, last_login, email_verified,
                accepted_privacy_document, newsletter_subscribed, phone, phone_verified,
                phone_verification_token, phone_verification_token_expires_at,
                privacy_document_id, logged_as
            )
            SELECT
                user_id, password, is_superuser, is_staff, is_active,
                created_at, updated_at, email, first_name, last_name,
                birth_date, is_18_years_old_or_more, last_login, email_verified,
                accepted_privacy_document, newsletter_subscribed, phone, phone_verified,
                phone_verification_token, phone_verification_token_expires_at,
                privacy_document_id, logged_as
            FROM src
            ON CONFLICT (user_id) DO UPDATE SET
                password                             = EXCLUDED.password,
                is_superuser                          = EXCLUDED.is_superuser,
                is_staff                              = EXCLUDED.is_staff,
                is_active                             = EXCLUDED.is_active,
                created_at                            = EXCLUDED.created_at,
                updated_at                            = EXCLUDED.updated_at,
                email                                 = EXCLUDED.email,
                first_name                            = EXCLUDED.first_name,
                last_name                             = EXCLUDED.last_name,
                birth_date                            = EXCLUDED.birth_date,
                is_18_years_old_or_more              = EXCLUDED.is_18_years_old_or_more,
                last_login                            = EXCLUDED.last_login,
                email_verified                        = EXCLUDED.email_verified,
                accepted_privacy_document             = EXCLUDED.accepted_privacy_document,
                newsletter_subscribed                 = EXCLUDED.newsletter_subscribed,
                phone                                 = EXCLUDED.phone,
                phone_verified                        = EXCLUDED.phone_verified,
                phone_verification_token              = EXCLUDED.phone_verification_token,
                phone_verification_token_expires_at   = EXCLUDED.phone_verification_token_expires_at,
                privacy_document_id                   = EXCLUDED.privacy_document_id,
                logged_as                             = EXCLUDED.logged_as
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()

    return {
        "ok": True,
        "msg": f"ETL user: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_clinic(conn):
    """
    Staging_01.lacreisaude_clinic  ➜  Staging_02.lacreisaude_clinic

    Mapeamentos / conversões:
      - id (text)                         -> clinic_id (varchar, PK)
      - created_at / updated_at (text)    -> timestamp (parse via timestamptz AT TIME ZONE 'UTC')
      - is_presential_clinic (text)       -> boolean
      - is_online_clinic (text)           -> boolean
      - name / zip_code / neighborhood /
        city / address / addresss_line2 /
        phone / phone_whatsapp            -> varchar  (obs: destino usa address_line2)
      - consult_price (text)              -> numeric(10,2) (normaliza vírgula/ponto e remove símbolos)
      - duration_minutes (text)           -> integer (quando numérico)
      - accepts_insurance_providers (text)-> boolean
      - provides_accessibility_standards  -> boolean
      - online_* (text)                   -> varchar / numeric(10,2) / integer / boolean
      - professional_id / registered_neighborhood_id / state_id (text) -> integer quando numérico
    """
    # 0) Verifica existência da tabela fonte
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreisaude_clinic LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreisaude_clinic não encontrada."}
        raise

    # 1) Cria schema/tabela destino (DDL corrigido)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreisaude_clinic
        (
            clinic_id                           VARCHAR PRIMARY KEY,
            created_at                          TIMESTAMP WITHOUT TIME ZONE,
            updated_at                          TIMESTAMP WITHOUT TIME ZONE,
            is_presential_clinic                BOOLEAN,
            is_online_clinic                    BOOLEAN,
            name                                VARCHAR,
            zip_code                            VARCHAR,
            neighborhood                        VARCHAR,
            city                                VARCHAR,
            address                             VARCHAR,
            address_line2                       VARCHAR,   -- corrige 'addresss_line2'
            phone                               VARCHAR,
            phone_whatsapp                      VARCHAR,
            consult_price                       NUMERIC(10,2),
            duration_minutes                    INTEGER,
            accepts_insurance_providers         BOOLEAN,
            provides_accessibility_standards    BOOLEAN,
            online_clinic_phone                 VARCHAR,
            online_clinic_phone_whatsapp        VARCHAR,
            online_clinic_consult_price         NUMERIC(10,2),
            online_clinic_duration_minutes      INTEGER,
            online_clinic_accepts_insurance_providers BOOLEAN,
            professional_id                     VARCHAR,
            registered_neighborhood_id          INTEGER,
            state_id                            INTEGER
        )
        TABLESPACE pg_default;

        ALTER TABLE IF EXISTS lacreisaude_staging_02.lacreisaude_clinic
            OWNER TO postgres;
    """))

    # Índices úteis para consultas
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_clinic_professional
            ON lacreisaude_staging_02.lacreisaude_clinic (professional_id);
        CREATE INDEX IF NOT EXISTS ix_clinic_city
            ON lacreisaude_staging_02.lacreisaude_clinic (city);
        CREATE INDEX IF NOT EXISTS ix_clinic_state
            ON lacreisaude_staging_02.lacreisaude_clinic (state_id);
    """))

    # 2) Upsert com limpeza/tipagem
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                NULLIF(TRIM(id), '')::varchar AS clinic_id,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                -- boolean helper
                -- aceita: true/false, t/f, 1/0, yes/no, y/n, sim/não, s/n
                CASE
                    WHEN NULLIF(LOWER(TRIM(is_presential_clinic)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(is_presential_clinic)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(is_presential_clinic)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS is_presential_clinic,

                CASE
                    WHEN NULLIF(LOWER(TRIM(is_online_clinic)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(is_online_clinic)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(is_online_clinic)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS is_online_clinic,

                NULLIF(name, '')::varchar          AS name,
                NULLIF(zip_code, '')::varchar      AS zip_code,
                NULLIF(neighborhood, '')::varchar  AS neighborhood,
                NULLIF(city, '')::varchar          AS city,
                NULLIF(address, '')::varchar       AS address,
                NULLIF(addresss_line2, '')::varchar AS address_line2,
                NULLIF(phone, '')::varchar         AS phone,
                NULLIF(phone_whatsapp, '')::varchar AS phone_whatsapp,

                -- preço: remove símbolos, troca vírgula por ponto e converte
                CASE
                    WHEN NULLIF(TRIM(consult_price), '') IS NULL THEN NULL
                    ELSE REPLACE(REGEXP_REPLACE(TRIM(consult_price), '[^0-9,.-]', '', 'g'), ',', '.')::numeric
                END AS consult_price,

                CASE
                    WHEN NULLIF(TRIM(duration_minutes), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(duration_minutes), '')::integer)
                    ELSE NULL
                END AS duration_minutes,

                CASE
                    WHEN NULLIF(LOWER(TRIM(accepts_insurance_providers)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(accepts_insurance_providers)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(accepts_insurance_providers)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS accepts_insurance_providers,

                CASE
                    WHEN NULLIF(LOWER(TRIM(provides_accessibility_standards)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(provides_accessibility_standards)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(provides_accessibility_standards)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS provides_accessibility_standards,

                NULLIF(online_clinic_phone, '')::varchar           AS online_clinic_phone,
                NULLIF(online_clinic_phone_whatsapp, '')::varchar  AS online_clinic_phone_whatsapp,

                CASE
                    WHEN NULLIF(TRIM(online_clinic_consult_price), '') IS NULL THEN NULL
                    ELSE REPLACE(REGEXP_REPLACE(TRIM(online_clinic_consult_price), '[^0-9,.-]', '', 'g'), ',', '.')::numeric
                END AS online_clinic_consult_price,

                CASE
                    WHEN NULLIF(TRIM(online_clinic_duration_minutes), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(online_clinic_duration_minutes), '')::integer)
                    ELSE NULL
                END AS online_clinic_duration_minutes,

                CASE
                    WHEN NULLIF(LOWER(TRIM(online_clinic_accepts_insurance_providers)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(online_clinic_accepts_insurance_providers)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(online_clinic_accepts_insurance_providers)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS online_clinic_accepts_insurance_providers,

                NULLIF(TRIM(professional_id), '')::varchar AS professional_id,

                CASE
                    WHEN NULLIF(TRIM(registered_neighborhood_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(registered_neighborhood_id), '')::integer)
                    ELSE NULL
                END AS registered_neighborhood_id,

                CASE
                    WHEN NULLIF(TRIM(state_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(state_id), '')::integer)
                    ELSE NULL
                END AS state_id

            FROM lacreisaude_staging_01.lacreisaude_clinic
            WHERE NULLIF(TRIM(id), '') IS NOT NULL
        ),
        src AS (
            -- Keep only the most recent row per clinic_id
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY clinic_id ORDER BY COALESCE(updated_at, created_at) DESC NULLS LAST) AS rn
                FROM src_raw
            ) t WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreisaude_clinic
            (
                clinic_id, created_at, updated_at, is_presential_clinic, is_online_clinic,
                name, zip_code, neighborhood, city, address, address_line2, phone, phone_whatsapp,
                consult_price, duration_minutes, accepts_insurance_providers,
                provides_accessibility_standards, online_clinic_phone, online_clinic_phone_whatsapp,
                online_clinic_consult_price, online_clinic_duration_minutes,
                online_clinic_accepts_insurance_providers, professional_id,
                registered_neighborhood_id, state_id
            )
            SELECT
                clinic_id, created_at, updated_at, is_presential_clinic, is_online_clinic,
                name, zip_code, neighborhood, city, address, address_line2, phone, phone_whatsapp,
                consult_price, duration_minutes, accepts_insurance_providers,
                provides_accessibility_standards, online_clinic_phone, online_clinic_phone_whatsapp,
                online_clinic_consult_price, online_clinic_duration_minutes,
                online_clinic_accepts_insurance_providers, professional_id,
                registered_neighborhood_id, state_id
            FROM src
            ON CONFLICT (clinic_id) DO UPDATE SET
                created_at                        = EXCLUDED.created_at,
                updated_at                        = EXCLUDED.updated_at,
                is_presential_clinic              = EXCLUDED.is_presential_clinic,
                is_online_clinic                  = EXCLUDED.is_online_clinic,
                name                              = EXCLUDED.name,
                zip_code                          = EXCLUDED.zip_code,
                neighborhood                      = EXCLUDED.neighborhood,
                city                              = EXCLUDED.city,
                address                           = EXCLUDED.address,
                address_line2                     = EXCLUDED.address_line2,
                phone                             = EXCLUDED.phone,
                phone_whatsapp                    = EXCLUDED.phone_whatsapp,
                consult_price                     = EXCLUDED.consult_price,
                duration_minutes                  = EXCLUDED.duration_minutes,
                accepts_insurance_providers       = EXCLUDED.accepts_insurance_providers,
                provides_accessibility_standards  = EXCLUDED.provides_accessibility_standards,
                online_clinic_phone               = EXCLUDED.online_clinic_phone,
                online_clinic_phone_whatsapp      = EXCLUDED.online_clinic_phone_whatsapp,
                online_clinic_consult_price       = EXCLUDED.online_clinic_consult_price,
                online_clinic_duration_minutes    = EXCLUDED.online_clinic_duration_minutes,
                online_clinic_accepts_insurance_providers = EXCLUDED.online_clinic_accepts_insurance_providers,
                professional_id                   = EXCLUDED.professional_id,
                registered_neighborhood_id        = EXCLUDED.registered_neighborhood_id,
                state_id                          = EXCLUDED.state_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL clinic: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_professional(conn):
    """
    Stg_01.lacreisaude_professional  ➜  Stg_02.lacreisaude_professional

    Mapeamentos:
      - id (text)                     -> professional_id (varchar, PK)
      - created_at/updated_at (text)  -> timestamp (parse via ::timestamptz AT TIME ZONE 'UTC')
      - active/published/accepted_privacy_document (text) -> boolean
      - *_id (text)                   -> integer quando numérico
      - Demais campos text            -> varchar
    """
    # 0) Fonte existe?
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreisaude_professional LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreisaude_professional não encontrada."}
        raise

    # 1) DDL de destino (corrigido e válido)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreisaude_professional
        (
            professional_id              VARCHAR PRIMARY KEY,
            created_at                   TIMESTAMP WITHOUT TIME ZONE,
            updated_at                   TIMESTAMP WITHOUT TIME ZONE,
            other_ethnic_group           VARCHAR,
            other_gender_identity        VARCHAR,
            other_sexual_orientation     VARCHAR,
            other_pronoun                VARCHAR,
            other_disability_types       VARCHAR,
            other_article                VARCHAR,
            full_name                    VARCHAR,
            about_me                     VARCHAR,
            profile_status               VARCHAR,
            active                       BOOLEAN,
            published                    BOOLEAN,
            document_number              VARCHAR,
            board_registration_number    VARCHAR,
            accepted_privacy_document    BOOLEAN,
            safety_measures              VARCHAR,
            specialty                    VARCHAR,
            specialty_number_rqe         VARCHAR,
            board_certification_selfie   VARCHAR,
            photo                        VARCHAR,
            photo_description            VARCHAR,
            ethnic_group                 INTEGER,
            gender_identity              INTEGER,
            privacy_document_id          INTEGER,
            profession_id                INTEGER,
            pronoun                      INTEGER,
            sexual_orientation           INTEGER,
            state_id                     INTEGER,
            user_id                      VARCHAR,
            search_synonym               VARCHAR
        )
        TABLESPACE pg_default;

        ALTER TABLE IF EXISTS lacreisaude_staging_02.lacreisaude_professional
            OWNER TO postgres;
    """))

    # Índices úteis
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_prof_full_name
            ON lacreisaude_staging_02.lacreisaude_professional (full_name);
        CREATE INDEX IF NOT EXISTS ix_prof_profession
            ON lacreisaude_staging_02.lacreisaude_professional (profession_id);
        CREATE INDEX IF NOT EXISTS ix_prof_state
            ON lacreisaude_staging_02.lacreisaude_professional (state_id);
        CREATE INDEX IF NOT EXISTS ix_prof_active_published
            ON lacreisaude_staging_02.lacreisaude_professional (active, published);
    """))

    # 2) Upsert com normalização
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                NULLIF(TRIM(id), '')::varchar AS professional_id,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                NULLIF(other_ethnic_group, '')::varchar        AS other_ethnic_group,
                NULLIF(other_gender_identity, '')::varchar     AS other_gender_identity,
                NULLIF(other_sexual_orientation, '')::varchar  AS other_sexual_orientation,
                NULLIF(other_pronoun, '')::varchar             AS other_pronoun,
                NULLIF(other_disability_types, '')::varchar    AS other_disability_types,
                NULLIF(other_article, '')::varchar             AS other_article,

                NULLIF(full_name, '')::varchar                 AS full_name,
                NULLIF(about_me, '')::varchar                  AS about_me,
                NULLIF(profile_status, '')::varchar            AS profile_status,

                -- boolean helper: true/false, t/f, 1/0, yes/no, y/n, sim/não, s/n
                CASE
                    WHEN NULLIF(LOWER(TRIM(active)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(active)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(active)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS active,

                CASE
                    WHEN NULLIF(LOWER(TRIM(published)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(published)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(published)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS published,

                NULLIF(document_number, '')::varchar           AS document_number,
                NULLIF(board_registration_number, '')::varchar AS board_registration_number,

                CASE
                    WHEN NULLIF(LOWER(TRIM(accepted_privacy_document)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(accepted_privacy_document)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(accepted_privacy_document)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS accepted_privacy_document,

                NULLIF(safety_measures, '')::varchar           AS safety_measures,
                NULLIF(specialty, '')::varchar                 AS specialty,
                NULLIF(specialty_number_rqe, '')::varchar      AS specialty_number_rqe,
                NULLIF(board_certification_selfie, '')::varchar AS board_certification_selfie,
                NULLIF(photo, '')::varchar                     AS photo,
                NULLIF(photo_description, '')::varchar         AS photo_description,

                CASE WHEN NULLIF(TRIM(ethnic_group_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(ethnic_group_id), '')::integer ELSE NULL END AS ethnic_group,
                CASE WHEN NULLIF(TRIM(gender_identity_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(gender_identity_id), '')::integer ELSE NULL END AS gender_identity,
                CASE WHEN NULLIF(TRIM(privacy_document_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(privacy_document_id), '')::integer ELSE NULL END AS privacy_document_id,
                CASE WHEN NULLIF(TRIM(profession_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(profession_id), '')::integer ELSE NULL END AS profession_id,
                CASE WHEN NULLIF(TRIM(pronoun_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(pronoun_id), '')::integer ELSE NULL END AS pronoun,
                CASE WHEN NULLIF(TRIM(sexual_orientation_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(sexual_orientation_id), '')::integer ELSE NULL END AS sexual_orientation,
                CASE WHEN NULLIF(TRIM(state_id), '') ~ '^[0-9]+$' THEN NULLIF(TRIM(state_id), '')::integer ELSE NULL END AS state_id,

                NULLIF(TRIM(user_id), '')::varchar             AS user_id,
                NULLIF(search_synonym, '')::varchar            AS search_synonym

            FROM lacreisaude_staging_01.lacreisaude_professional
            WHERE NULLIF(TRIM(id), '') IS NOT NULL
        ),
        src AS (
            -- Keep only the most recent row per professional_id
            SELECT * FROM (
                SELECT *, ROW_NUMBER() OVER (PARTITION BY professional_id ORDER BY COALESCE(updated_at, created_at) DESC NULLS LAST) AS rn
                FROM src_raw
            ) t WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreisaude_professional
            (
                professional_id, created_at, updated_at,
                other_ethnic_group, other_gender_identity, other_sexual_orientation, other_pronoun,
                other_disability_types, other_article,
                full_name, about_me, profile_status, active, published,
                document_number, board_registration_number, accepted_privacy_document, safety_measures,
                specialty, specialty_number_rqe, board_certification_selfie, photo, photo_description,
                ethnic_group, gender_identity, privacy_document_id, profession_id, pronoun,
                sexual_orientation, state_id, user_id, search_synonym
            )
            SELECT
                professional_id, created_at, updated_at,
                other_ethnic_group, other_gender_identity, other_sexual_orientation, other_pronoun,
                other_disability_types, other_article,
                full_name, about_me, profile_status, active, published,
                document_number, board_registration_number, accepted_privacy_document, safety_measures,
                specialty, specialty_number_rqe, board_certification_selfie, photo, photo_description,
                ethnic_group, gender_identity, privacy_document_id, profession_id, pronoun,
                sexual_orientation, state_id, user_id, search_synonym
            FROM src
            ON CONFLICT (professional_id) DO UPDATE SET
                created_at                 = EXCLUDED.created_at,
                updated_at                 = EXCLUDED.updated_at,
                other_ethnic_group         = EXCLUDED.other_ethnic_group,
                other_gender_identity      = EXCLUDED.other_gender_identity,
                other_sexual_orientation   = EXCLUDED.other_sexual_orientation,
                other_pronoun              = EXCLUDED.other_pronoun,
                other_disability_types     = EXCLUDED.other_disability_types,
                other_article              = EXCLUDED.other_article,
                full_name                  = EXCLUDED.full_name,
                about_me                   = EXCLUDED.about_me,
                profile_status             = EXCLUDED.profile_status,
                active                     = EXCLUDED.active,
                published                  = EXCLUDED.published,
                document_number            = EXCLUDED.document_number,
                board_registration_number  = EXCLUDED.board_registration_number,
                accepted_privacy_document  = EXCLUDED.accepted_privacy_document,
                safety_measures            = EXCLUDED.safety_measures,
                specialty                  = EXCLUDED.specialty,
                specialty_number_rqe       = EXCLUDED.specialty_number_rqe,
                board_certification_selfie = EXCLUDED.board_certification_selfie,
                photo                      = EXCLUDED.photo,
                photo_description          = EXCLUDED.photo_description,
                ethnic_group               = EXCLUDED.ethnic_group,
                gender_identity            = EXCLUDED.gender_identity,
                privacy_document_id        = EXCLUDED.privacy_document_id,
                profession_id              = EXCLUDED.profession_id,
                pronoun                    = EXCLUDED.pronoun,
                sexual_orientation         = EXCLUDED.sexual_orientation,
                state_id                   = EXCLUDED.state_id,
                user_id                    = EXCLUDED.user_id,
                search_synonym             = EXCLUDED.search_synonym
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL professional: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }

def _rodar_etl_professional_disability_types(conn):
    """
    Stg_01.lacreisaude_professional_disability_types ➜ Stg_02.lacreisaude_professional_disability_types

    Mapeamentos:
      - id (text)               -> id (INTEGER, PK)         [somente quando numérico]
      - professional_id (text)  -> professional_id (VARCHAR)
      - disabilitytype_id (text)-> disabilitytype_id (INTEGER quando numérico)
    """
    # 0) Verifica existência da tabela fonte
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreisaude_professional_disability_types LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreisaude_professional_disability_types não encontrada."}
        raise

    # 1) Cria schema/tabela destino (DDL válido)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreisaude_professional_disability_types
        (
            id                INTEGER PRIMARY KEY,
            professional_id   VARCHAR,
            disabilitytype_id INTEGER
        )
        TABLESPACE pg_default;

        ALTER TABLE IF EXISTS lacreisaude_staging_02.lacreisaude_professional_disability_types
            OWNER TO postgres;
    """))

    # Índices úteis (consultas por professional_id / disabilitytype_id)
    conn.execute(text("""
        CREATE INDEX IF NOT EXISTS ix_prof_disab_prof
            ON lacreisaude_staging_02.lacreisaude_professional_disability_types (professional_id);
        CREATE INDEX IF NOT EXISTS ix_prof_disab_type
            ON lacreisaude_staging_02.lacreisaude_professional_disability_types (disabilitytype_id);
    """))

    # 2) Upsert com limpeza e tipagem
    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER                                   AS id,
                NULLIF(TRIM(professional_id), '')::VARCHAR                         AS professional_id,
                CASE
                    WHEN NULLIF(TRIM(disabilitytype_id), '') ~ '^[0-9]+$'
                        THEN (NULLIF(TRIM(disabilitytype_id), '')::INTEGER)
                    ELSE NULL
                END                                                                 AS disabilitytype_id,
                ROW_NUMBER() OVER (
                    PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER
                    ORDER BY (CASE WHEN NULLIF(TRIM(id), '') IS NULL THEN to_timestamp(0) ELSE to_timestamp(0) END)
                ) AS rn
            FROM lacreisaude_staging_01.lacreisaude_professional_disability_types
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'  -- garante PK numérico
        ),
        src AS (
            SELECT id, professional_id, disabilitytype_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreisaude_professional_disability_types
                (id, professional_id, disabilitytype_id)
            SELECT id, professional_id, disabilitytype_id
            FROM src
            ON CONFLICT (id) DO UPDATE SET
                professional_id   = EXCLUDED.professional_id,
                disabilitytype_id = EXCLUDED.disabilitytype_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL professional_disability_types: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }


def _rodar_etl_address_state(conn):
    """
    Staging_01.address_state  ➜  Staging_02.address_state

    Tipagem proposta:
      - id (text) -> INTEGER PK quando numérico
      - created_at/updated_at (text) -> TIMESTAMP
      - name/code/ibge_code (text) -> VARCHAR
      - active (text) -> BOOLEAN
      - country_id (text) -> INTEGER quando numérico
    """
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.address_state LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.address_state não encontrada."}
        raise

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.address_state
        (
            id         INTEGER PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            name       VARCHAR,
            code       VARCHAR,
            ibge_code  VARCHAR,
            active     BOOLEAN,
            country_id INTEGER
        )
        TABLESPACE pg_default;
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER AS id,

                CASE
                    WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS created_at,

                CASE
                    WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                    ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC')
                END AS updated_at,

                NULLIF(name, '')::varchar AS name,
                NULLIF(code, '')::varchar AS code,
                NULLIF(ibge_code, '')::varchar AS ibge_code,

                CASE
                    WHEN NULLIF(LOWER(TRIM(active)), '') IS NULL THEN NULL
                    WHEN LOWER(TRIM(active)) IN ('true','t','1','yes','y','sim','s') THEN TRUE
                    WHEN LOWER(TRIM(active)) IN ('false','f','0','no','n','nao','não') THEN FALSE
                    ELSE NULL
                END AS active,

                CASE
                    WHEN NULLIF(TRIM(country_id), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(country_id), '')::INTEGER)
                    ELSE NULL
                END AS country_id,

                ROW_NUMBER() OVER (
                    PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER
                    ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC
                ) AS rn

            FROM lacreisaude_staging_01.address_state
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (
            SELECT id, created_at, updated_at, name, code, ibge_code, active, country_id
            FROM src_raw
            WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.address_state
                (id, created_at, updated_at, name, code, ibge_code, active, country_id)
            SELECT id, created_at, updated_at, name, code, ibge_code, active, country_id
            FROM src
            ON CONFLICT (id) DO UPDATE SET
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                name       = EXCLUDED.name,
                code       = EXCLUDED.code,
                ibge_code  = EXCLUDED.ibge_code,
                active     = EXCLUDED.active,
                country_id = EXCLUDED.country_id
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """

    row = conn.execute(text(upsert_sql)).mappings().one()
    return {
        "ok": True,
        "msg": f"ETL address_state: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).",
        "inserted": int(row["inseridos"]),
        "updated": int(row["atualizados"]),
        "source_rows": int(row["elegiveis"])
    }


def _rodar_etl_disabilitytype(conn):
    """
    Staging_01.lacreiid_disabilitytype  ➜  Staging_02.lacreiid_disabilitytype

    Popula a tabela de tipos de deficiência com id (INTEGER PK) e name (VARCHAR)
    """
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_disabilitytype LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_disabilitytype não encontrada."}
        raise

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_disabilitytype
        (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            badge VARCHAR,
            position_order INTEGER,
            name VARCHAR
        )
        TABLESPACE pg_default;
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER AS id,
                CASE WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC') END AS created_at,
                CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END AS updated_at,
                NULLIF(badge, '')::varchar AS badge,
                CASE WHEN NULLIF(TRIM(position_order), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(position_order), '')::INTEGER) ELSE NULL END AS position_order,
                NULLIF(name, '')::varchar AS name,
                ROW_NUMBER() OVER (PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC) AS rn

            FROM lacreisaude_staging_01.lacreiid_disabilitytype
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (
            SELECT id, created_at, updated_at, badge, position_order, name
            FROM src_raw WHERE rn = 1
        ),
        
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_disabilitytype
                (id, created_at, updated_at, badge, position_order, name)
            SELECT id, created_at, updated_at, badge, position_order, name FROM src
            ON CONFLICT (id) DO UPDATE SET
                created_at = EXCLUDED.created_at,
                updated_at = EXCLUDED.updated_at,
                badge = EXCLUDED.badge,
                position_order = EXCLUDED.position_order,
                name = EXCLUDED.name
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT
            COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END), 0) AS inseridos,
            COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END), 0) AS atualizados,
            (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """

    row = conn.execute(text(upsert_sql)).mappings().one()
    return {"ok": True, "msg": f"ETL disabilitytype: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).", "inserted": int(row['inseridos']), "updated": int(row['atualizados']), "source_rows": int(row['elegiveis'])}


def _rodar_etl_sexualorientation(conn):
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_sexualorientation LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_sexualorientation não encontrada."}
        raise

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_sexualorientation
        (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            bagde VARCHAR,
            position_order INTEGER,
            name VARCHAR
        )
        TABLESPACE pg_default;
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER AS id,
                CASE WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC') END AS created_at,
                CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END AS updated_at,
                NULLIF(bagde, '')::varchar AS bagde,
                CASE WHEN NULLIF(TRIM(position_order), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(position_order), '')::INTEGER) ELSE NULL END AS position_order,
                NULLIF(name, '')::varchar AS name,
                ROW_NUMBER() OVER (PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC) AS rn
        
            FROM lacreisaude_staging_01.lacreiid_sexualorientation
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (SELECT id, created_at, updated_at, bagde, position_order, name FROM src_raw WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_sexualorientation (id, created_at, updated_at, bagde, position_order, name)
            SELECT id, created_at, updated_at, bagde, position_order, name FROM src
            ON CONFLICT (id) DO UPDATE SET created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at, bagde = EXCLUDED.bagde, position_order = EXCLUDED.position_order, name = EXCLUDED.name
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END),0) AS inseridos,
               COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END),0) AS atualizados,
               (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """

    row = conn.execute(text(upsert_sql)).mappings().one()
    return {"ok": True, "msg": f"ETL sexualorientation: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).", "inserted": int(row['inseridos']), "updated": int(row['atualizados']), "source_rows": int(row['elegiveis'])}


def _rodar_etl_pronoun(conn):
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_pronoun LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_pronoun não encontrada."}
        raise

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_pronoun
        (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            bagde VARCHAR,
            position_order INTEGER,
            article VARCHAR,
            pronoun VARCHAR
        )
        TABLESPACE pg_default;
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER AS id,
                CASE WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC') END AS created_at,
                CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END AS updated_at,
                NULLIF(bagde, '')::varchar AS bagde,
                CASE WHEN NULLIF(TRIM(position_order), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(position_order), '')::INTEGER) ELSE NULL END AS position_order,
                NULLIF(article, '')::varchar AS article,
                NULLIF(pronoun, '')::varchar AS pronoun,
                ROW_NUMBER() OVER (PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC) AS rn
                
            FROM lacreisaude_staging_01.lacreiid_pronoun
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (SELECT id, created_at, updated_at, bagde, position_order, article, pronoun FROM src_raw WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_pronoun (id, created_at, updated_at, bagde, position_order, article, pronoun)
            SELECT id, created_at, updated_at, bagde, position_order, article, pronoun FROM src
            ON CONFLICT (id) DO UPDATE SET created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at, bagde = EXCLUDED.bagde, position_order = EXCLUDED.position_order, article = EXCLUDED.article, pronoun = EXCLUDED.pronoun
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END),0) AS inseridos,
               COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END),0) AS atualizados,
               (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """

    row = conn.execute(text(upsert_sql)).mappings().one()
    return {"ok": True, "msg": f"ETL pronoun: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).", "inserted": int(row['inseridos']), "updated": int(row['atualizados']), "source_rows": int(row['elegiveis'])}


def _rodar_etl_ethnicgroup(conn):
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_ethnicgroup LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_ethnicgroup não encontrada."}
        raise

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_ethnicgroup
        (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            bagde VARCHAR,
            position_order INTEGER,
            name VARCHAR
        )
        TABLESPACE pg_default;
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER AS id,
                CASE WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC') END AS created_at,
                CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END AS updated_at,
                NULLIF(bagde, '')::varchar AS bagde,
                CASE WHEN NULLIF(TRIM(position_order), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(position_order), '')::INTEGER) ELSE NULL END AS position_order,
                NULLIF(name, '')::varchar AS name,
                ROW_NUMBER() OVER (PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC) AS rn
                
            FROM lacreisaude_staging_01.lacreiid_ethnicgroup
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (SELECT id, created_at, updated_at, bagde, position_order, name FROM src_raw WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_ethnicgroup (id, created_at, updated_at, bagde, position_order, name)
            SELECT id, created_at, updated_at, bagde, position_order, name FROM src
            ON CONFLICT (id) DO UPDATE SET created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at, bagde = EXCLUDED.bagde, position_order = EXCLUDED.position_order, name = EXCLUDED.name
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END),0) AS inseridos,
               COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END),0) AS atualizados,
               (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """

    row = conn.execute(text(upsert_sql)).mappings().one()
    return {"ok": True, "msg": f"ETL ethnicgroup: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).", "inserted": int(row['inseridos']), "updated": int(row['atualizados']), "source_rows": int(row['elegiveis'])}


def _rodar_etl_genderidentity(conn):
    try:
        conn.execute(text("SELECT 1 FROM lacreisaude_staging_01.lacreiid_genderidentity LIMIT 1"))
    except ProgrammingError as e:
        if isinstance(e.orig, UndefinedTable):
            return {"ok": False, "msg": "Tabela fonte lacreisaude_staging_01.lacreiid_genderidentity não encontrada."}
        raise

    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_02;
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_genderidentity
        (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP WITHOUT TIME ZONE,
            updated_at TIMESTAMP WITHOUT TIME ZONE,
            bagde VARCHAR,
            position_order INTEGER,
            name VARCHAR
        )
        TABLESPACE pg_default;
    """))

    upsert_sql = """
        WITH src_raw AS (
            SELECT
                (NULLIF(TRIM(id), ''))::INTEGER AS id,
                CASE WHEN NULLIF(TRIM(created_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(created_at), '')::timestamptz AT TIME ZONE 'UTC') END AS created_at,
                CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN NULL
                     ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END AS updated_at,
                NULLIF(bagde, '')::varchar AS bagde,
                CASE WHEN NULLIF(TRIM(position_order), '') ~ '^[0-9]+$' THEN (NULLIF(TRIM(position_order), '')::INTEGER) ELSE NULL END AS position_order,
                NULLIF(name, '')::varchar AS name,
                ROW_NUMBER() OVER (PARTITION BY (NULLIF(TRIM(id), ''))::INTEGER ORDER BY (CASE WHEN NULLIF(TRIM(updated_at), '') IS NULL THEN to_timestamp(0) ELSE (NULLIF(TRIM(updated_at), '')::timestamptz AT TIME ZONE 'UTC') END) DESC) AS rn
                
            FROM lacreisaude_staging_01.lacreiid_genderidentity
            WHERE NULLIF(TRIM(id), '') ~ '^[0-9]+$'
        ),
        src AS (SELECT id, created_at, updated_at, bagde, position_order, name FROM src_raw WHERE rn = 1
        ),
        upsert AS (
            INSERT INTO lacreisaude_staging_02.lacreiid_genderidentity (id, created_at, updated_at, bagde, position_order, name)
            SELECT id, created_at, updated_at, bagde, position_order, name FROM src
            ON CONFLICT (id) DO UPDATE SET created_at = EXCLUDED.created_at, updated_at = EXCLUDED.updated_at, bagde = EXCLUDED.bagde, position_order = EXCLUDED.position_order, name = EXCLUDED.name
            RETURNING (xmax = 0) AS inserted_flag
        )
        SELECT COALESCE(SUM(CASE WHEN inserted_flag THEN 1 ELSE 0 END),0) AS inseridos,
               COALESCE(SUM(CASE WHEN NOT inserted_flag THEN 1 ELSE 0 END),0) AS atualizados,
               (SELECT COUNT(*) FROM src) AS elegiveis
        FROM upsert;
    """

    row = conn.execute(text(upsert_sql)).mappings().one()
    return {"ok": True, "msg": f"ETL genderidentity: {int(row['inseridos'])} inseridos, {int(row['atualizados'])} atualizados (de {int(row['elegiveis'])} elegíveis).", "inserted": int(row['inseridos']), "updated": int(row['atualizados']), "source_rows": int(row['elegiveis'])}

def _safe_run(name, func, conn):
    try:
        res = func(conn)
        if not res.get("ok"):
            return {"name": name, "ok": False, "msg": res.get("msg"), "inserted": 0, "updated": 0, "source_rows": 0}
        return {"name": name, "ok": True, **res}
    except Exception as e:
        return {"name": name, "ok": False, "msg": str(e), "inserted": 0, "updated": 0, "source_rows": 0}

@bp_staging2.route('/upload/staging', methods=['GET'])
@swag_from({
    'tags': ['ETL'],
    'summary': 'Roda TODOS os ETLs de staging_01 ➜ staging_02 e depois popula o MODEL',
    'responses': {200: {'description': 'OK'}, 500: {'description': 'Erro'}}
})
def consultar_indicadores_resumo():
    try:
        criar_popular_staging1()
        with engine.begin() as conn:
            # 1) Rode TODOS os ETLs aqui
            runs = []
            runs.append(_safe_run("privacydocument", _rodar_etl_privacydocument, conn))
            runs.append(_safe_run("appointment",     _rodar_etl_appointment, conn))
            runs.append(_safe_run("cancellation",    _rodar_etl_cancellation, conn))
            runs.append(_safe_run("profile",         _rodar_etl_profile, conn))
            runs.append(_safe_run("profile_disability_types", _rodar_etl_profile_disability_types, conn))
            runs.append(_safe_run("report",          _rodar_etl_report, conn))
            runs.append(_safe_run("user",            _rodar_etl_user, conn))
            runs.append(_safe_run("address_state",   _rodar_etl_address_state, conn))
            runs.append(_safe_run("disabilitytype", _rodar_etl_disabilitytype, conn))
            runs.append(_safe_run("sexualorientation", _rodar_etl_sexualorientation, conn))
            runs.append(_safe_run("pronoun", _rodar_etl_pronoun, conn))
            runs.append(_safe_run("ethnicgroup", _rodar_etl_ethnicgroup, conn))
            runs.append(_safe_run("genderidentity", _rodar_etl_genderidentity, conn))
            runs.append(_safe_run("clinic",          _rodar_etl_clinic, conn))
            runs.append(_safe_run("professional",    _rodar_etl_professional, conn))
            runs.append(_safe_run("professional_disability_types", _rodar_etl_professional_disability_types, conn))

            # DEBUG: Adiciona retorno detalhado dos runs para diagnóstico
            # Se algum ETL falhar, retorna imediatamente com o erro detalhado
            # for r in runs:
            #     if not r["ok"]:
            #         return jsonify({
            #             "sucesso": False,
            #             "mensagem": f"Erro no ETL '{r['name']}': {r.get('msg')}",
            #             "etls": runs
            #         }), 500

            # 2) Amostras (ainda DENTRO do with)
            amostras = {}
            amostras["lacrei_privacydocument"] = [dict(r) for r in conn.execute(text("""
                SELECT id, created_at, updated_at, profile_type
                FROM lacreisaude_staging_02.lacrei_privacydocument
                ORDER BY id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreiid_appointment"] = [dict(r) for r in conn.execute(text("""
                SELECT id, appointment_date, status, professional_id, user_id
                FROM lacreisaude_staging_02.lacreiid_appointment
                ORDER BY appointment_date DESC NULLS LAST, id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreiid_cancellation"] = [dict(r) for r in conn.execute(text("""
                SELECT cancellation_id, created_at, reason, appointment_id
                FROM lacreisaude_staging_02.lacreiid_cancellation
                ORDER BY created_at DESC NULLS LAST, cancellation_id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreiid_profile"] = [dict(r) for r in conn.execute(text("""
                SELECT profile_id, created_at, completed, user_id,
                       ethnic_group, gender_identity, pronoun, sexual_orientation
                FROM lacreisaude_staging_02.lacreiid_profile
                ORDER BY updated_at DESC NULLS LAST, profile_id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreiid_profile_disability_types"] = [dict(r) for r in conn.execute(text("""
                SELECT id, profile_id, disabilitytype_id
                FROM lacreisaude_staging_02.lacreiid_profile_disability_types
                ORDER BY id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreiid_report"] = [dict(r) for r in conn.execute(text("""
                SELECT report_id, created_at, eval, appointment_id
                FROM lacreisaude_staging_02.lacreiid_report
                ORDER BY created_at DESC NULLS LAST, report_id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreiid_user"] = [dict(r) for r in conn.execute(text("""
                SELECT user_id, email, is_active, is_staff, is_superuser,
                       last_login, privacy_document_id
                FROM lacreisaude_staging_02.lacreiid_user
                ORDER BY updated_at DESC NULLS LAST, user_id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreisaude_clinic"] = [dict(r) for r in conn.execute(text("""
                SELECT clinic_id, name, city, state_id, consult_price,
                       is_presential_clinic, is_online_clinic
                FROM lacreisaude_staging_02.lacreisaude_clinic
                ORDER BY updated_at DESC NULLS LAST, clinic_id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreisaude_professional"] = [dict(r) for r in conn.execute(text("""
                SELECT professional_id, full_name, profile_status,
                       active, published, profession_id, state_id
                FROM lacreisaude_staging_02.lacreisaude_professional
                ORDER BY updated_at DESC NULLS LAST, professional_id DESC
                LIMIT 20
            """)).mappings().all()]
            amostras["lacreisaude_professional_disability_types"] = [dict(r) for r in conn.execute(text("""
                SELECT id, professional_id, disabilitytype_id
                FROM lacreisaude_staging_02.lacreisaude_professional_disability_types
                ORDER BY id DESC
                LIMIT 20
            """)).mappings().all()]

            # 3) Resumo ainda DENTRO do with
            resumo = [{
                "tabela": r["name"],
                "ok": r["ok"],
                "mensagem": r.get("msg"),
                "linhas_elegiveis": r.get("source_rows", 0),
                "inseridos": r.get("inserted", 0),
                "atualizados": r.get("updated", 0)
            } for r in runs]

            model_res = _rodar_etl_model(conn)
            mart_res = _rodar_etl_mart(conn)

            sucesso = all(r["ok"] for r in runs) and model_res.get("ok", False) and mart_res.get("ok", False)
            resposta = {
                "sucesso": sucesso,
                "resumo": (
                    resumo
                    + [{"tabela": "MODEL", "ok": model_res.get("ok", False), "mensagem": model_res.get("msg")}]
                    + [{"tabela": "MART",  "ok": mart_res.get("ok",  False), "mensagem": mart_res.get("msg")}]
                ),
                "amostras": amostras,
                # "etls": runs # DEBUG: Retorna detalhes dos ETLs para diagnóstico
            }
        return jsonify(resposta), 200
    except Exception as e:
        return jsonify({"sucesso": False, "mensagem": f"Erro inesperado: {str(e)}"}), 500