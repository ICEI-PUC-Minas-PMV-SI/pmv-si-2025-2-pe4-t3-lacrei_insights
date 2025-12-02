
from flask import Blueprint, jsonify
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from app.db.engine import get_engine
from sqlalchemy import create_engine
import os
from datetime import datetime

bp_staging1 = Blueprint('upload_staging1', __name__)
engine = get_engine()
SOURCE_DATABASE_URL = os.getenv('SOURCE_DATABASE_URL')
SOURCE_SCHEMA = os.getenv('SOURCE_SCHEMA')
source_engine = None
if SOURCE_DATABASE_URL:
    source_engine = create_engine(SOURCE_DATABASE_URL)


def _create_staging01_tables(conn):
    # Cria schema e tabelas de staging_01 com colunas em TEXT (raw/texto)
    conn.execute(text("""
        CREATE SCHEMA IF NOT EXISTS lacreisaude_staging_01;

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacrei_privacydocument (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            privacy_policy TEXT,
            terms_of_use TEXT,
            profile_type TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_appointment (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            date TEXT,
            status TEXT,
            type TEXT,
            professional_id TEXT,
            user_id TEXT,
            agreement_id TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_cancellation (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            reason TEXT,
            appointment_id TEXT,
            created_by_content_type_id TEXT,
            created_by_object_d TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_profile (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            other_ethnic_group TEXT,
            other_gender_identity TEXT,
            other_sexual_orientation TEXT,
            other_pronoun TEXT,
            other_disability_types TEXT,
            other_article TEXT,
            completed TEXT,
            photo TEXT,
            photo_description TEXT,
            ethnic_group_id TEXT,
            gender_identity_id TEXT,
            pronoun_id TEXT,
            sexual_orientation_id TEXT,
            user_id TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_profile_disability_types (
            id TEXT,
            profile_id TEXT,
            disabilitytype_id TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_report (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            feedback TEXT,
            eval TEXT,
            appointment_id TEXT,
            created_by_content_type_id TEXT,
            created_by_object_id TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_user (
            id TEXT,
            password TEXT,
            is_superuser TEXT,
            is_staff TEXT,
            is_active TEXT,
            created_at TEXT,
            updated_at TEXT,
            email TEXT,
            first_name TEXT,
            last_name TEXT,
            birth_date TEXT,
            is_18_years_old_or_more TEXT,
            last_login TEXT,
            email_verified TEXT,
            accepted_privacy_document TEXT,
            newsletter_subscribed TEXT,
            phone TEXT,
            phone_verified TEXT,
            phone_verification_token TEXT,
            phone_verification_token_expires_at TEXT,
            privacy_document_id TEXT,
            logged_as TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreisaude_clinic (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            is_presential_clinic TEXT,
            is_online_clinic TEXT,
            name TEXT,
            zip_code TEXT,
            neighborhood TEXT,
            city TEXT,
            address TEXT,
            addresss_line2 TEXT,
            phone TEXT,
            phone_whatsapp TEXT,
            consult_price TEXT,
            duration_minutes TEXT,
            accepts_insurance_providers TEXT,
            provides_accessibility_standards TEXT,
            online_clinic_phone TEXT,
            online_clinic_phone_whatsapp TEXT,
            online_clinic_consult_price TEXT,
            online_clinic_duration_minutes TEXT,
            online_clinic_accepts_insurance_providers TEXT,
            professional_id TEXT,
            registered_neighborhood_id TEXT,
            state_id TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreisaude_professional (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            other_ethnic_group TEXT,
            other_gender_identity TEXT,
            other_sexual_orientation TEXT,
            other_pronoun TEXT,
            other_disability_types TEXT,
            other_article TEXT,
            full_name TEXT,
            about_me TEXT,
            profile_status TEXT,
            active TEXT,
            published TEXT,
            document_number TEXT,
            board_registration_number TEXT,
            accepted_privacy_document TEXT,
            safety_measures TEXT,
            specialty TEXT,
            specialty_number_rqe TEXT,
            board_certification_selfie TEXT,
            photo TEXT,
            photo_description TEXT,
            ethnic_group_id TEXT,
            gender_identity_id TEXT,
            privacy_document_id TEXT,
            profession_id TEXT,
            pronoun_id TEXT,
            sexual_orientation_id TEXT,
            state_id TEXT,
            user_id TEXT,
            search_synonym TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreisaude_professional_disability_types (
            id TEXT,
            professional_id TEXT,
            disabilitytype_id TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_disabilitytype (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            badge TEXT,
            position_order TEXT,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_sexualorientation (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            bagde TEXT,
            position_order TEXT,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_pronoun (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            bagde TEXT,
            position_order TEXT,
            article TEXT,
            pronoun TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_ethnicgroup (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            bagde TEXT,
            position_order TEXT,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_genderidentity (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            bagde TEXT,
            position_order TEXT,
            name TEXT
        );

        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.address_state (
            id TEXT,
            created_at TEXT,
            updated_at TEXT,
            name TEXT,
            code TEXT,
            ibge_code TEXT,
            active TEXT,
            country_id TEXT
        );
    """))


# Lista de colunas usadas nas tabelas de staging_01 (todas em TEXT)
TABLE_COLUMNS = {
    'lacrei_privacydocument': ['id','created_at','updated_at','privacy_policy','terms_of_use','profile_type'],
    'lacreiid_appointment': ['id','created_at','updated_at','date','status','type','professional_id','user_id','agreement_id'],
    'lacreiid_cancellation': ['id','created_at','updated_at','reason','appointment_id','created_by_content_type_id','created_by_object_d'],
    'lacreiid_profile': ['id','created_at','updated_at','other_ethnic_group','other_gender_identity','other_sexual_orientation','other_pronoun','other_disability_types','other_article','completed','photo','photo_description','ethnic_group_id','gender_identity_id','pronoun_id','sexual_orientation_id','user_id'],
    'lacreiid_profile_disability_types': ['id','profile_id','disabilitytype_id'],
    'lacreiid_report': ['id','created_at','updated_at','feedback','eval','appointment_id','created_by_content_type_id','created_by_object_id'],
    'lacreiid_user': ['id','password','is_superuser','is_staff','is_active','created_at','updated_at','email','first_name','last_name','birth_date','is_18_years_old_or_more','last_login','email_verified','accepted_privacy_document','newsletter_subscribed','phone','phone_verified','phone_verification_token','phone_verification_token_expires_at','privacy_document_id','logged_as'],
    'lacreisaude_clinic': ['id','created_at','updated_at','is_presential_clinic','is_online_clinic','name','zip_code','neighborhood','city','address','addresss_line2','phone','phone_whatsapp','consult_price','duration_minutes','accepts_insurance_providers','provides_accessibility_standards','online_clinic_phone','online_clinic_phone_whatsapp','online_clinic_consult_price','online_clinic_duration_minutes','online_clinic_accepts_insurance_providers','professional_id','registered_neighborhood_id','state_id'],
    'lacreisaude_professional': ['id','created_at','updated_at','other_ethnic_group','other_gender_identity','other_sexual_orientation','other_pronoun','other_disability_types','other_article','full_name','about_me','profile_status','active','published','document_number','board_registration_number','accepted_privacy_document','safety_measures','specialty','specialty_number_rqe','board_certification_selfie','photo','photo_description','ethnic_group_id','gender_identity_id','privacy_document_id','profession_id','pronoun_id','sexual_orientation_id','state_id','user_id','search_synonym'],
    'lacreisaude_professional_disability_types': ['id','professional_id','disabilitytype_id']
}

# disability type table (contains name/label of disability types)
TABLE_COLUMNS['lacreiid_disabilitytype'] = ['id','created_at','updated_at','badge','position_order','name']

# lookup tables for names used by profile/professional
TABLE_COLUMNS['lacreiid_sexualorientation'] = ['id','created_at','updated_at','bagde','position_order','name']
TABLE_COLUMNS['lacreiid_pronoun'] = ['id','created_at','updated_at','bagde','position_order','article','pronoun']
TABLE_COLUMNS['lacreiid_ethnicgroup'] = ['id','created_at','updated_at','bagde','position_order','name']
TABLE_COLUMNS['lacreiid_genderidentity'] = ['id','created_at','updated_at','bagde','position_order','name']

# include address_state so we can resolve state names when building the model
TABLE_COLUMNS['address_state'] = ['id','created_at','updated_at','name','code','ibge_code','active','country_id']

# campos que serão sempre nulificados/omitidos no staging (PII sensível)
SENSITIVE_NULL = {
    'password',
    'phone_verification_token',
    'phone_verification_token_expires_at',
    'email',
    'phone',
    'phone_whatsapp',
    'online_clinic_phone',
    'online_clinic_phone_whatsapp',
}


def _to_text(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.isoformat()
    return str(v)


def _copy_table_from_source(conn, source_engine, source_schema, table_name, staging_cols):
    """Copia linhas da tabela source_schema.table_name no source_engine para a tabela
    lacreisaude_staging_01.table_name (colunas em texto). Retorna número de linhas inseridas."""
    if source_engine is None:
        return 0

    # Consulta todas as linhas da tabela fonte
    # Protege nomes com aspas (schema pode ter hífen)
    sel = text(f'SELECT * FROM "{source_schema}"."{table_name}"')
    inserted = 0
    try:
        with source_engine.connect() as src_conn:
            rows = src_conn.execute(sel).mappings().all()
            for r in rows:
                params = {}
                cols_to_insert = []
                for c in staging_cols:
                    # alguns nomes de colunas do staging podem não existir na fonte; só copia os que existirem
                    if c in r:
                        cols_to_insert.append(c)
                        # nulifica campos sensíveis para não trazer PII
                        if c in SENSITIVE_NULL:
                            params[c] = None
                        else:
                            params[c] = _to_text(r[c])

                if not cols_to_insert:
                    continue

                col_list = ','.join([f'"{c}"' for c in cols_to_insert])
                param_list = ','.join([f':{c}' for c in cols_to_insert])
                insert_sql = f'INSERT INTO lacreisaude_staging_01."{table_name}" ({col_list}) VALUES ({param_list})'
                conn.execute(text(insert_sql), params)
                inserted += 1
    except Exception:
        # se tabela não existir na fonte ou erro, apenas retorna 0
        return 0

    return inserted


# @bp_staging1.route('/upload/staging1', methods=['GET'])
def criar_popular_staging1():
    resumo = []
    try:
        with engine.begin() as conn:
            _create_staging01_tables(conn)

            tables = [
                'lacrei_privacydocument', 'lacreiid_appointment', 'lacreiid_cancellation',
                'lacreiid_profile', 'lacreiid_profile_disability_types', 'lacreiid_report',
                # lookup/reference tables
                'lacreiid_sexualorientation', 'lacreiid_pronoun', 'lacreiid_ethnicgroup', 'lacreiid_genderidentity',
                'lacreiid_user', 'lacreisaude_clinic', 'lacreisaude_professional',
                'lacreisaude_professional_disability_types', 'lacreiid_disabilitytype', 'address_state'
            ]

            for t in tables:
                # Tenta copiar da fonte relacional quando configurada
                loaded = 0
                if source_engine:
                    cols = TABLE_COLUMNS.get(t, [])
                    loaded = _copy_table_from_source(conn, source_engine, SOURCE_SCHEMA, t, cols)

                # conta linhas após tentativa de cópia
                row_count = conn.execute(text(f'SELECT COUNT(*) AS c FROM lacreisaude_staging_01.{t}')).mappings().one()['c']
                if row_count == 0:
                    # insere uma linha de amostra básica com poucos campos (tudo como texto)
                    # tenta preencher colunas mais importantes quando fizer sentido
                    if t == 'lacrei_privacydocument':
                        conn.execute(text("INSERT INTO lacreisaude_staging_01.lacrei_privacydocument (id, created_at, updated_at, privacy_policy, terms_of_use, profile_type) VALUES ('1','2020-01-01T00:00:00Z','2020-01-01T00:00:00Z','policy','terms','patient')"))
                    elif t == 'lacreiid_appointment':
                        conn.execute(text("INSERT INTO lacreisaude_staging_01.lacreiid_appointment (id,date,status,professional_id,user_id) VALUES ('1','2020-01-01T09:00:00Z','scheduled','10','100')"))
                    elif t == 'lacreiid_user':
                        conn.execute(text("INSERT INTO lacreisaude_staging_01.lacreiid_user (id,email,is_active) VALUES ('u1','user@example.com','true')"))
                    else:
                        # inserção genérica: tenta inserir a string 'sample' em primeira coluna
                        conn.execute(text(f"INSERT INTO lacreisaude_staging_01.{t} DEFAULT VALUES"))
                    inserted = 1
                else:
                    inserted = 0

                resumo.append({'tabela': t, 'rows_copied_from_source': loaded, 'rows_in_staging': row_count, 'sample_inserted': inserted})

        return jsonify({'ok': True, 'resumo': resumo}), 200

    except Exception as e:
        return jsonify({'ok': False, 'mensagem': str(e)}), 500

