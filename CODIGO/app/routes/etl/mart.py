from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError

# Ajuste aqui se quiser outro schema de saída
MART_SCHEMA = "lacreisaude_mart"

def _rodar_etl_mart(conn):
    """
    Constrói/atualiza as tabelas de Data Mart a partir das tabelas da camada MODEL (schema: lacreisaude_model).
    - Tabelas: patients, patient_disability, professionals, professional_appointments
    - Idempotente: usa ON CONFLICT (PK) DO UPDATE
    - Assume que a MODEL (dim_*/fact_*) já foi populada no mesmo 'conn'
    """

    # ---------------------------------------------------------------------
    # 0) Schema da MART
    # ---------------------------------------------------------------------
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {MART_SCHEMA};"))

    # ---------------------------------------------------------------------
    # 1) MART: patients
    #     PK: (period_month, age_group, gender_identity, sexual_orientation)
    # ---------------------------------------------------------------------
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {MART_SCHEMA}.patients (
            period_month DATE NOT NULL,
            age_group VARCHAR(50),
            gender_identity VARCHAR(100),
            sexual_orientation VARCHAR(100),
            ethnic_group VARCHAR(255),
            total_patients INT,
            active_patients INT,
            inactive_patients INT,
            active_percentage NUMERIC(5,2),
            growth_rate NUMERIC(5,2),
            CONSTRAINT mart_patient_pk
            PRIMARY KEY (period_month, age_group, gender_identity, sexual_orientation, ethnic_group)
        );
    """))

    conn.execute(text(f"""
        WITH patient_base AS (
            SELECT
                p.patient_id                                    AS patient_sk,
                DATE_TRUNC('month', p.created_at)::date         AS period_month,
                CASE
                    WHEN p.birth_date IS NULL THEN 'N/I'
                    ELSE CASE
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 18 AND 25 THEN '18-25'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 26 AND 35 THEN '26-35'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 36 AND 45 THEN '36-45'
                        WHEN EXTRACT(YEAR FROM AGE(p.birth_date)) BETWEEN 46 AND 60 THEN '46-60'
                        ELSE '60+'
                    END
                END                                             AS age_group,
                COALESCE(p.gender_identity, 'N/I')              AS gender_identity,
                COALESCE(p.sexual_orientation, 'N/I')           AS sexual_orientation,
                COALESCE(p.ethnic_group, 'N/I')                     AS ethnic_group,
                COALESCE(p.is_active, false)                    AS is_active
            FROM lacreisaude_model.dim_lacreisaude_patient p
        ),
        aggregated AS (
            SELECT
                period_month,
                age_group,
                gender_identity,
                sexual_orientation,
                ethnic_group,
                COUNT(*) FILTER (WHERE patient_sk IS NOT NULL)                AS total_patients,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END)                    AS active_patients,
                SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END)                AS inactive_patients
            FROM patient_base
            GROUP BY 1,2,3,4,5
        ),
        monthly_totals AS (
            SELECT
                period_month,
                SUM(total_patients) AS month_total
            FROM aggregated
            GROUP BY period_month
        ),
        growth_calc AS (
            SELECT
                period_month,
                month_total,
                LAG(month_total) OVER (ORDER BY period_month) AS prev_month_total
            FROM monthly_totals
        ),
        joined AS (
            SELECT
                a.period_month,
                a.age_group,
                a.gender_identity,
                a.sexual_orientation,
                a.ethnic_group,
                a.total_patients,
                a.active_patients,
                a.inactive_patients,
                ROUND(a.active_patients::numeric / NULLIF(a.total_patients,0) * 100, 2) AS active_percentage,
                CASE
                    WHEN gc.prev_month_total IS NOT NULL AND gc.prev_month_total > 0
                        THEN ROUND(((gc.month_total - gc.prev_month_total)::numeric / gc.prev_month_total) * 100, 2)
                    ELSE NULL
                END AS growth_rate
            FROM aggregated a
            JOIN growth_calc gc USING (period_month)
        )
        INSERT INTO {MART_SCHEMA}.patients
        (
            period_month, age_group, gender_identity, sexual_orientation, ethnic_group,
            total_patients, active_patients, inactive_patients, active_percentage, growth_rate
        )
        SELECT
            period_month, age_group, gender_identity, sexual_orientation, ethnic_group,
            total_patients, active_patients, inactive_patients, active_percentage, growth_rate
        FROM joined
        ON CONFLICT (period_month, age_group, gender_identity, sexual_orientation, ethnic_group) DO UPDATE SET
            total_patients    = EXCLUDED.total_patients,
            active_patients   = EXCLUDED.active_patients,
            inactive_patients = EXCLUDED.inactive_patients,
            active_percentage = EXCLUDED.active_percentage,
            growth_rate       = EXCLUDED.growth_rate;
    """))

    # ---------------------------------------------------------------------
    # 2) MART: patient_disability
    #     PK: (period_month, disability_type)
    # ---------------------------------------------------------------------
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {MART_SCHEMA}.patient_disability (
            period_month DATE NOT NULL,
            disability_type VARCHAR(255) NOT NULL,
            total_patients INT,
            active_patients INT,
            inactive_patients INT,
            CONSTRAINT mart_patient_disability_pk
                PRIMARY KEY (period_month, disability_type)
        );
    """))

    conn.execute(text(f"""
        WITH expanded AS (
            SELECT
                DATE_TRUNC('month', p.created_at)::date           AS period_month,
                TRIM(UNNEST(COALESCE(p.disability_type, ARRAY[]::text[]))) AS disability_type,
                COALESCE(p.is_active, false)                      AS is_active
            FROM lacreisaude_model.dim_lacreisaude_patient p
            WHERE p.disability_type IS NOT NULL
        ),
        aggregated AS (
            SELECT
                period_month,
                disability_type,
                COUNT(*)                                           AS total_patients,
                SUM(CASE WHEN is_active THEN 1 ELSE 0 END)         AS active_patients,
                SUM(CASE WHEN NOT is_active THEN 1 ELSE 0 END)     AS inactive_patients
            FROM expanded
            GROUP BY 1,2
        )
        INSERT INTO {MART_SCHEMA}.patient_disability
        (
            period_month, disability_type, total_patients, active_patients, inactive_patients
        )
        SELECT period_month, disability_type, total_patients, active_patients, inactive_patients
        FROM aggregated
        ON CONFLICT (period_month, disability_type) DO UPDATE SET
            total_patients   = EXCLUDED.total_patients,
            active_patients  = EXCLUDED.active_patients,
            inactive_patients= EXCLUDED.inactive_patients;
    """))

    # ---------------------------------------------------------------------
    # 3) MART: professionals
    #     PK: professional_sk
    # ---------------------------------------------------------------------
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {MART_SCHEMA}.professionals (
            professional_sk INTEGER PRIMARY KEY,
            sexual_orientation VARCHAR(255),
            ethnic_group VARCHAR(255),
            gender_identity VARCHAR(255),
            specialty VARCHAR(255),
            state VARCHAR(255),
            profile_status VARCHAR(255),
            active BOOLEAN,
            total_appointments INTEGER,
            avg_feedback_rating NUMERIC(4,2)
        );
    """))

    conn.execute(text(f"""
        WITH professional AS (
            SELECT
                p.professional_id                  AS professional_sk,
                p.profile_status,
                p.active,
                p.state,
                p.sexual_orientation,
                p.ethnic_group,
                p.gender_identity,
                p.specialty
            FROM lacreisaude_model.dim_lacreisaude_professional p
        ),
        appointments AS (
            SELECT
                f.professional_id   AS professional_sk,
                COUNT(*) FILTER (WHERE LOWER(COALESCE(f.status, '')) = 'completed') AS total_appointments
            FROM lacreisaude_model.fact_lacreisaude_appointments f
            GROUP BY f.professional_id
        ),
        feedbacks AS (
            SELECT
                f.professional_id   AS professional_sk,
                AVG(dr.evaluation::numeric)        AS avg_feedback_rating
            FROM lacreisaude_model.fact_lacreisaude_appointments f
            JOIN lacreisaude_model.dim_lacreisaude_report dr
              ON dr.report_id = f.report_id
            GROUP BY f.professional_id
        )
        INSERT INTO {MART_SCHEMA}.professionals
        (
            professional_sk, sexual_orientation, ethnic_group, gender_identity, specialty, state,
            profile_status, active, total_appointments, avg_feedback_rating
        )
        SELECT
            p.professional_sk,
            p.sexual_orientation,
            p.ethnic_group,
            p.gender_identity,
            p.specialty,
            p.state,
            p.profile_status,
            p.active,
            COALESCE(a.total_appointments, 0)                         AS total_appointments,
            ROUND(COALESCE(f.avg_feedback_rating, 0), 2)              AS avg_feedback_rating
        FROM professional p
        LEFT JOIN appointments a USING (professional_sk)
        LEFT JOIN feedbacks   f USING (professional_sk)
        ON CONFLICT (professional_sk) DO UPDATE SET
            sexual_orientation   = EXCLUDED.sexual_orientation,
            ethnic_group         = EXCLUDED.ethnic_group,
            gender_identity      = EXCLUDED.gender_identity,
            specialty            = EXCLUDED.specialty,
            state                = EXCLUDED.state,
            profile_status       = EXCLUDED.profile_status,
            active               = EXCLUDED.active,
            total_appointments   = EXCLUDED.total_appointments,
            avg_feedback_rating  = EXCLUDED.avg_feedback_rating;
    """))

    # ---------------------------------------------------------------------
    # 4) MART: professional_appointments
    #     PK: (professional_sk, appointment_period, specialty)
    # ---------------------------------------------------------------------
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {MART_SCHEMA}.professional_appointments (
            professional_sk INT NOT NULL,
            appointment_period DATE NOT NULL,
            specialty VARCHAR(255),
            total_appointments INT,
            completed_appointments INT,
            completed_appointments_online INT,
            completed_appointments_presencial INT,
            cancelled_appointments_online INT,
            cancelled_appointments_presencial INT,
            completion_rate NUMERIC(5,2),
            cancellation_rate_online NUMERIC(5,2),
            cancellation_rate_presencial NUMERIC(5,2),
            avg_waiting_time NUMERIC(10,2),
            created_at DATE,
            CONSTRAINT mart_professional_appointments_pk
                PRIMARY KEY (professional_sk, appointment_period, specialty)
        );
    """))

    conn.execute(text(f"""
        WITH base AS (
            SELECT
                f.professional_id                                            AS professional_sk,
                DATE_TRUNC('month', d_ap.calendar_date)::date                AS appointment_period,
                d_cr.calendar_date                                           AS created_at,
                COALESCE(dp.specialty, 'Não informada')                      AS specialty,
                LOWER(COALESCE(f.status, ''))                                AS status,
                COALESCE(f.type, '')                                         AS type,
                f.waiting_time
            FROM lacreisaude_model.fact_lacreisaude_appointments f
            JOIN lacreisaude_model.dim_lacreisaude_date d_ap
              ON d_ap.date_id = f.date_id
            LEFT JOIN lacreisaude_model.dim_lacreisaude_date d_cr
              ON d_cr.date_id = f.created_date_id
            LEFT JOIN lacreisaude_model.dim_lacreisaude_professional dp
              ON dp.professional_id = f.professional_id
            WHERE f.professional_id IS NOT NULL
        ),
        agg AS (
            SELECT
                professional_sk,
                appointment_period,
                specialty,
                COUNT(*)                                           AS total_appointments,
                SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END)  AS completed_appointments,
                SUM(CASE WHEN status = 'completed' AND type = 'Online' THEN 1 ELSE 0 END)  AS completed_appointments_online,
                SUM(CASE WHEN status = 'completed' AND type = 'Presencial' THEN 1 ELSE 0 END)  AS completed_appointments_presencial,
                SUM(CASE WHEN status = 'cancelled' AND type = 'Online' THEN 1 ELSE 0 END)  AS cancelled_appointments_online,
                SUM(CASE WHEN status = 'cancelled' AND type = 'Presencial' THEN 1 ELSE 0 END)  AS cancelled_appointments_presencial,
                ROUND(AVG(NULLIF(waiting_time, 0))::numeric, 2)    AS avg_waiting_time,
                MAX(created_at)                                    AS created_at
            FROM base
            GROUP BY 1,2,3
        )
        INSERT INTO {MART_SCHEMA}.professional_appointments
        (
            professional_sk, appointment_period, specialty,
            total_appointments, completed_appointments,  completed_appointments_online, completed_appointments_presencial, cancelled_appointments_online, cancelled_appointments_presencial,
            completion_rate, cancellation_rate_online, cancellation_rate_presencial, avg_waiting_time, created_at
        )
        SELECT
            professional_sk,
            appointment_period,
            specialty,
            total_appointments,
            completed_appointments,
            completed_appointments_online,
            completed_appointments_presencial,
            cancelled_appointments_online,
            cancelled_appointments_presencial,
            ROUND((completed_appointments::numeric / NULLIF(total_appointments,0)) * 100, 2) AS completion_rate,
            ROUND((cancelled_appointments_online::numeric / NULLIF(total_appointments,0)) * 100, 2) AS cancellation_rate_online,
            ROUND((cancelled_appointments_presencial::numeric / NULLIF(total_appointments,0)) * 100, 2) AS cancellation_rate_presencial,
            avg_waiting_time,
            created_at
        FROM agg
        ON CONFLICT (professional_sk, appointment_period, specialty) DO UPDATE SET
            total_appointments      = EXCLUDED.total_appointments,
            completed_appointments  = EXCLUDED.completed_appointments,
            completed_appointments_online = EXCLUDED.completed_appointments_online,
            completed_appointments_presencial = EXCLUDED.completed_appointments_presencial,
            cancelled_appointments_online = EXCLUDED.cancelled_appointments_online,
            cancelled_appointments_presencial = EXCLUDED.cancelled_appointments_presencial,
            cancellation_rate_online = EXCLUDED.cancellation_rate_online,
            cancellation_rate_presencial = EXCLUDED.cancellation_rate_presencial,
            completion_rate         = EXCLUDED.completion_rate,
            avg_waiting_time        = EXCLUDED.avg_waiting_time,
            created_at              = EXCLUDED.created_at;
    """))

    # Retorna um resumo indicando que o ETL da MART foi executado com sucesso
    return {
        "ok": True,
        "msg": "MART ETL concluído com sucesso."
    }

