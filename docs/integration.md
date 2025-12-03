# 🔄 Documentação do Processo ETL - Lacrei Insights

Este documento detalha o pipeline ETL (Extract, Transform, Load) do projeto Lacrei Insights, explicando cada etapa, função e operação dos principais arquivos Python.

---

## 📑 Sumário

1. [Visão Geral](#visão-geral)
2. [Extração (Staging 1)](#extração-staging-1)
3. [Transformação (Staging 2)](#transformação-staging-2)
4. [Modelagem (Models)](#modelagem-models)
5. [Agregação (Marts)](#agregação-marts)
6. [Carga](#carga)
7. [Fluxo Completo](#fluxo-completo)
8. [Execução](#execução)

---

## 🎯 Visão Geral

O pipeline ETL do projeto Lacrei Insights é composto por **4 camadas principais**:

```
Banco Origem (PostgreSQL)
        ↓
[STAGING 1] - Extração
        ↓
[STAGING 2] - Transformação
        ↓
[MODEL] - Modelagem Dimensional
        ↓
[MART] - Agregações para BI
        ↓
Metabase (Dashboards)
```

### Características do Pipeline

- ✅ **Idempotente:** Pode ser executado múltiplas vezes sem duplicar dados
- ✅ **Incremental:** Usa `ON CONFLICT DO UPDATE` para atualizar registros existentes
- ✅ **Modular:** Cada etapa pode ser executada independentemente
- ✅ **Automatizado:** Disparo via portal web ou endpoints Flask
- ✅ **Documentado:** Logs de execução para auditoria

---

## 📥 Extração (Staging 1)

**Arquivo:** `app/routes/etl/staging1.py`  
**Schema:** `lacreisaude_staging_01`

### Objetivo
Extrair dados brutos do banco de dados relacional de origem (PostgreSQL da Lacrei Saúde) e carregar no schema de staging 1, sem transformações.

### Função Principal

```python
def _rodar_etl_staging1(conn):
    """
    Executa todos os jobs de extração do banco relacional 
    para o schema lacreisaude_staging_01.
    """
    results = []
    
    # Extrai cada tabela
    results.append(_etl_lacreiid_appointment(conn))
    results.append(_etl_lacreiid_user(conn))
    results.append(_etl_lacreiid_profile(conn))
    results.append(_etl_lacreiid_clinic(conn))
    results.append(_etl_lacreiid_report(conn))
    results.append(_etl_lacreiid_cancellation(conn))
    # ... outras tabelas
    
    return results
```

### Endpoint Flask

```python
@bp_staging1.route('/upload/staging1', methods=['GET'])
def upload_staging1():
    """Endpoint para executar staging 1"""
    try:
        conn = get_db_connection()
        result = _rodar_etl_staging1(conn)
        conn.commit()
        return jsonify({"status": "success", "results": result})
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
```

### Funções de Extração por Tabela

Cada tabela fonte tem uma função dedicada que:
1. Cria a tabela de destino no staging 1 (se não existir)
2. Extrai os dados do banco de origem
3. Insere os dados no staging 1

**Exemplo:**

```python
def _etl_lacreiid_appointment(conn):
    """
    Extrai dados da tabela lacreiid_appointment do banco origem
    e carrega em lacreisaude_staging_01.lacreiid_appointment
    """
    # 1. Criar tabela destino
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_appointment (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP,
            updated_at TIMESTAMP,
            appointment_date TIMESTAMP,
            patient_id INTEGER,
            professional_id INTEGER,
            clinic_id INTEGER,
            status VARCHAR(50),
            -- ... outros campos
        )
    """))
    
    # 2. Extrair dados
    extract_sql = """
        SELECT 
            id, created_at, updated_at, appointment_date,
            patient_id, professional_id, clinic_id, status
        FROM lacreiid_appointment
        WHERE deleted_at IS NULL
    """
    
    # 3. Inserir no staging 1
    insert_sql = """
        INSERT INTO lacreisaude_staging_01.lacreiid_appointment
        SELECT * FROM ({extract_sql}) AS source
        ON CONFLICT (id) DO UPDATE SET
            updated_at = EXCLUDED.updated_at,
            -- ... outros campos
    """
    
    result = conn.execute(text(insert_sql))
    return {"table": "lacreiid_appointment", "rows": result.rowcount}
```

### Tabelas Extraídas

- `lacreiid_appointment` - Agendamentos
- `lacreiid_user` - Usuários (pacientes)
- `lacreiid_profile` - Perfis (profissionais)
- `lacreiid_clinic` - Clínicas
- `lacreiid_report` - Avaliações/Feedbacks
- `lacreiid_cancellation` - Cancelamentos
- Outras tabelas auxiliares

---

## 🔄 Transformação (Staging 2)

**Arquivo:** `app/routes/etl/staging2.py`  
**Schema:** `lacreisaude_staging_02`

### Objetivo
Transformar e normalizar os dados do Staging 1, aplicando:
- Tipagem correta (datas, booleanos, inteiros)
- Limpeza de dados inconsistentes
- Deduplicação
- Normalização de campos
- **Anonimização de dados sensíveis (LGPD)**

### Função Principal

```python
def _rodar_etl_staging2(conn):
    """
    Executa todas as transformações e carrega em staging_02
    """
    results = []
    
    results.append(_rodar_etl_appointment(conn))
    results.append(_rodar_etl_user(conn))
    results.append(_rodar_etl_profile(conn))
    results.append(_rodar_etl_clinic(conn))
    # ... outras transformações
    
    return results
```

### Funções de Transformação por Tabela

**Exemplo - Transformação de Appointments:**

```python
def _rodar_etl_appointment(conn):
    """
    Transforma dados de appointments do staging_01 para staging_02
    Aplica: tipagem, limpeza, normalização
    """
    # 1. Criar tabela destino
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_appointment (
            id INTEGER PRIMARY KEY,
            created_at TIMESTAMP NOT NULL,
            updated_at TIMESTAMP,
            appointment_date TIMESTAMP,
            patient_id INTEGER NOT NULL,
            professional_id INTEGER NOT NULL,
            clinic_id INTEGER,
            status VARCHAR(50),
            is_cancelled BOOLEAN DEFAULT FALSE,
            waiting_time_days INTEGER
        )
    """))
    
    # 2. Transformar e fazer upsert
    upsert_sql = """
        WITH src_raw AS (
            SELECT 
                id,
                CAST(created_at AS TIMESTAMP) AS created_at,
                CAST(updated_at AS TIMESTAMP) AS updated_at,
                CAST(appointment_date AS TIMESTAMP) AS appointment_date,
                patient_id,
                professional_id,
                clinic_id,
                UPPER(TRIM(status)) AS status,
                CASE 
                    WHEN status IN ('cancelled', 'canceled') THEN TRUE 
                    ELSE FALSE 
                END AS is_cancelled,
                EXTRACT(DAY FROM (appointment_date - created_at)) AS waiting_time_days
            FROM lacreisaude_staging_01.lacreiid_appointment
            WHERE patient_id IS NOT NULL 
              AND professional_id IS NOT NULL
        )
        INSERT INTO lacreisaude_staging_02.lacreiid_appointment
        SELECT * FROM src_raw
        ON CONFLICT (id) DO UPDATE SET
            updated_at = EXCLUDED.updated_at,
            appointment_date = EXCLUDED.appointment_date,
            status = EXCLUDED.status,
            is_cancelled = EXCLUDED.is_cancelled,
            waiting_time_days = EXCLUDED.waiting_time_days
    """
    
    result = conn.execute(text(upsert_sql))
    return {"table": "lacreiid_appointment", "rows": result.rowcount}
```

### Transformações Aplicadas

#### Tipagem
- Conversão de strings para TIMESTAMP, INTEGER, BOOLEAN
- Padronização de formatos de data

#### Limpeza
- Remoção de espaços em branco (`TRIM`)
- Padronização de case (`UPPER`, `LOWER`)
- Tratamento de valores nulos

#### Normalização
- Estados: São Paulo → SP
- Status: cancelled/canceled → cancelled
- Especialidades: padronização de nomes

#### Anonimização (LGPD) 🔒
```python
# Exemplo: Anonimização de dados pessoais
def _rodar_etl_user(conn):
    upsert_sql = """
        WITH src_raw AS (
            SELECT 
                id,
                NULL AS first_name,  -- ANONIMIZADO
                NULL AS last_name,   -- ANONIMIZADO
                created_at,
                is_active,
                -- Dados agregados mantidos
                ethnic_group,
                gender_identity,
                pronoun,
                sexual_orientation
            FROM lacreisaude_staging_01.lacreiid_user
        )
        ...
    """
```

#### Cálculos Derivados
- `waiting_time_days` = appointment_date - created_at
- `age` = EXTRACT(YEAR FROM CURRENT_DATE) - EXTRACT(YEAR FROM birth_date)
- `age_group` = CASE WHEN age < 18 THEN '< 18' WHEN age < 25 THEN '18-24' ...

---

## 🏗️ Modelagem (Models)

**Arquivo:** `app/routes/etl/model.py`  
**Schema:** `lacreisaude_model`

### Objetivo
Criar o Data Warehouse com modelagem dimensional (Star Schema), consolidando dados em tabelas de fatos e dimensões otimizadas para análises.

### Função Principal

```python
def _rodar_etl_model(conn):
    """
    Popula/atualiza o schema lacreisaude_model a partir da staging_02.
    - Usa chaves naturais com UNIQUE INDEX para garantir idempotência
    - Todos os INSERTs usam ON CONFLICT ... DO UPDATE
    - Cria Star Schema (1 fato + N dimensões)
    """
    
    # 0) Schema
    conn.execute(text("CREATE SCHEMA IF NOT EXISTS lacreisaude_model;"))
    
    # 1) Dimensão Data
    _create_dim_date(conn)
    
    # 2) Dimensão Paciente
    _create_dim_patient(conn)
    
    # 3) Dimensão Profissional
    _create_dim_professional(conn)
    
    # 4) Dimensão Clínica
    _create_dim_clinic(conn)
    
    # 5) Dimensão Report (Feedback)
    _create_dim_report(conn)
    
    # 6) Dimensão Cancelamento
    _create_dim_cancellation(conn)
    
    # 7) Tabela Fato - Appointments
    _create_fact_appointments(conn)
```

### Estrutura do Star Schema

```
           dim_date
               ↓
    ┌──────────────────────┐
    │  fact_appointments   │ ← Tabela Fato
    └──────────────────────┘
      ↓    ↓    ↓    ↓    ↓
    dim  dim  dim  dim  dim
   patient prof clinic report cancel
```

### Exemplo - Dimensão Data

```python
def _create_dim_date(conn):
    """Cria e popula dim_lacreisaude_date"""
    
    # Criar tabela
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_model.dim_lacreisaude_date (
            date_id INTEGER GENERATED BY DEFAULT AS IDENTITY PRIMARY KEY,
            calendar_date DATE NOT NULL UNIQUE,
            day INTEGER NOT NULL,
            month INTEGER NOT NULL,
            year INTEGER NOT NULL,
            week INTEGER NOT NULL,
            quarter INTEGER NOT NULL
        )
    """))
    
    # Popular com datas
    conn.execute(text("""
        INSERT INTO lacreisaude_model.dim_lacreisaude_date 
            (calendar_date, day, month, year, week, quarter)
        SELECT 
            dt AS calendar_date,
            EXTRACT(DAY FROM dt) AS day,
            EXTRACT(MONTH FROM dt) AS month,
            EXTRACT(YEAR FROM dt) AS year,
            EXTRACT(WEEK FROM dt) AS week,
            EXTRACT(QUARTER FROM dt) AS quarter
        FROM generate_series('2020-01-01'::DATE, '2030-12-31'::DATE, '1 day') AS dt
        ON CONFLICT (calendar_date) DO NOTHING
    """))
```

### Exemplo - Dimensão Paciente

```python
def _create_dim_patient(conn):
    """Cria e popula dim_lacreisaude_patient"""
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_model.dim_lacreisaude_patient (
            patient_id INTEGER PRIMARY KEY,
            created_at TIMESTAMP,
            first_name VARCHAR(100),      -- NULL (anonimizado)
            last_name VARCHAR(100),       -- NULL (anonimizado)
            is_active BOOLEAN,
            profile_type VARCHAR(50),
            ethnic_group VARCHAR(100),
            gender_identity VARCHAR(100),
            pronoun VARCHAR(50),
            sexual_orientation VARCHAR(100),
            disability_type TEXT,
            birth_date DATE,
            age INTEGER,
            age_group VARCHAR(20)
        )
    """))
    
    conn.execute(text("""
        INSERT INTO lacreisaude_model.dim_lacreisaude_patient
        SELECT 
            u.id AS patient_id,
            u.created_at,
            NULL AS first_name,          -- ANONIMIZADO
            NULL AS last_name,           -- ANONIMIZADO
            u.is_active,
            p.profile_type,
            p.ethnic_group,
            p.gender_identity,
            p.pronoun,
            p.sexual_orientation,
            p.disability_type,
            u.birth_date,
            EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.birth_date)) AS age,
            CASE 
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.birth_date)) < 18 THEN '< 18'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.birth_date)) < 25 THEN '18-24'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.birth_date)) < 35 THEN '25-34'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.birth_date)) < 45 THEN '35-44'
                WHEN EXTRACT(YEAR FROM AGE(CURRENT_DATE, u.birth_date)) < 55 THEN '45-54'
                ELSE '55+'
            END AS age_group
        FROM lacreisaude_staging_02.lacreiid_user u
        LEFT JOIN lacreisaude_staging_02.lacreiid_profile p ON u.id = p.user_id
        WHERE p.profile_type = 'patient'
        ON CONFLICT (patient_id) DO UPDATE SET
            is_active = EXCLUDED.is_active,
            age = EXCLUDED.age,
            age_group = EXCLUDED.age_group
    """))
```

### Exemplo - Tabela Fato Appointments

```python
def _create_fact_appointments(conn):
    """Cria e popula fact_lacreisaude_appointments"""
    
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_model.fact_lacreisaude_appointments (
            appointment_id INTEGER PRIMARY KEY,
            patient_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_patient(patient_id),
            professional_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_professional(professional_id),
            clinic_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_clinic(clinic_id),
            report_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_report(report_id),
            cancellation_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_cancellation(cancellation_id),
            created_date_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_date(date_id),
            appointment_date_id INTEGER REFERENCES lacreisaude_model.dim_lacreisaude_date(date_id),
            waiting_time_days INTEGER,
            is_cancelled BOOLEAN,
            is_completed BOOLEAN,
            created_at TIMESTAMP,
            appointment_date TIMESTAMP
        )
    """))
    
    conn.execute(text("""
        INSERT INTO lacreisaude_model.fact_lacreisaude_appointments
        SELECT 
            a.id AS appointment_id,
            a.patient_id,
            a.professional_id,
            a.clinic_id,
            r.id AS report_id,
            c.id AS cancellation_id,
            d1.date_id AS created_date_id,
            d2.date_id AS appointment_date_id,
            a.waiting_time_days,
            a.is_cancelled,
            (a.status = 'completed') AS is_completed,
            a.created_at,
            a.appointment_date
        FROM lacreisaude_staging_02.lacreiid_appointment a
        LEFT JOIN lacreisaude_model.dim_lacreisaude_date d1 
            ON CAST(a.created_at AS DATE) = d1.calendar_date
        LEFT JOIN lacreisaude_model.dim_lacreisaude_date d2 
            ON CAST(a.appointment_date AS DATE) = d2.calendar_date
        LEFT JOIN lacreisaude_model.dim_lacreisaude_report r 
            ON a.id = r.appointment_id
        LEFT JOIN lacreisaude_model.dim_lacreisaude_cancellation c 
            ON a.id = c.appointment_id
        ON CONFLICT (appointment_id) DO UPDATE SET
            is_cancelled = EXCLUDED.is_cancelled,
            is_completed = EXCLUDED.is_completed,
            waiting_time_days = EXCLUDED.waiting_time_days
    """))
```

---

## 📊 Agregação (Marts)

**Arquivo:** `app/routes/etl/mart.py`  
**Schema:** `lacreisaude_mart`

### Objetivo
Criar Data Marts otimizados para consumo pelos dashboards do Metabase, com dados pré-agregados e métricas calculadas.

### Função Principal

```python
def _rodar_etl_mart(conn):
    """
    Constrói/atualiza as tabelas de Data Mart a partir das tabelas MODEL
    - Tabelas: patients, patient_disability, professionals, professional_appointments
    - Idempotente: usa ON CONFLICT (PK) DO UPDATE
    """
    
    MART_SCHEMA = "lacreisaude_mart"
    
    # 0) Schema da MART
    conn.execute(text(f"CREATE SCHEMA IF NOT EXISTS {MART_SCHEMA};"))
    
    # 1) MART: patients
    _create_mart_patients(conn, MART_SCHEMA)
    
    # 2) MART: patient_disability
    _create_mart_patient_disability(conn, MART_SCHEMA)
    
    # 3) MART: professionals
    _create_mart_professionals(conn, MART_SCHEMA)
    
    # 4) MART: professional_appointments
    _create_mart_professional_appointments(conn, MART_SCHEMA)
```

### Exemplo - Mart Patients

```python
def _create_mart_patients(conn, schema):
    """
    Cria mart agregado de pacientes por período mensal e grupos demográficos
    PK: (period_month, age_group, gender_identity, sexual_orientation, pronoun)
    """
    
    # Criar tabela
    conn.execute(text(f"""
        CREATE TABLE IF NOT EXISTS {schema}.patients (
            period_month DATE NOT NULL,
            age_group VARCHAR(50),
            pronoun VARCHAR(50),
            gender_identity VARCHAR(100),
            sexual_orientation VARCHAR(100),
            total_patients INT,
            active_patients INT,
            inactive_patients INT,
            active_percentage NUMERIC(5,2),
            growth_rate NUMERIC(5,2),
            CONSTRAINT mart_patient_pk
                PRIMARY KEY (period_month, age_group, gender_identity, sexual_orientation, pronoun)
        )
    """))
    
    # Popular com dados agregados
    conn.execute(text(f"""
        WITH monthly_data AS (
            SELECT 
                DATE_TRUNC('month', p.created_at) AS period_month,
                p.age_group,
                p.pronoun,
                p.gender_identity,
                p.sexual_orientation,
                COUNT(DISTINCT p.patient_id) AS total_patients,
                COUNT(DISTINCT CASE WHEN p.is_active THEN p.patient_id END) AS active_patients,
                COUNT(DISTINCT CASE WHEN NOT p.is_active THEN p.patient_id END) AS inactive_patients
            FROM lacreisaude_model.dim_lacreisaude_patient p
            GROUP BY 1,2,3,4,5
        ),
        with_percentages AS (
            SELECT 
                *,
                CASE 
                    WHEN total_patients > 0 
                    THEN ROUND((active_patients::NUMERIC / total_patients) * 100, 2)
                    ELSE 0 
                END AS active_percentage,
                LAG(total_patients) OVER (
                    PARTITION BY age_group, pronoun, gender_identity, sexual_orientation 
                    ORDER BY period_month
                ) AS prev_month_total
            FROM monthly_data
        )
        INSERT INTO {schema}.patients
        SELECT 
            period_month,
            age_group,
            pronoun,
            gender_identity,
            sexual_orientation,
            total_patients,
            active_patients,
            inactive_patients,
            active_percentage,
            CASE 
                WHEN prev_month_total > 0 
                THEN ROUND(((total_patients - prev_month_total)::NUMERIC / prev_month_total) * 100, 2)
                ELSE 0 
            END AS growth_rate
        FROM with_percentages
        ON CONFLICT (period_month, age_group, gender_identity, sexual_orientation, pronoun) 
        DO UPDATE SET
            total_patients = EXCLUDED.total_patients,
            active_patients = EXCLUDED.active_patients,
            inactive_patients = EXCLUDED.inactive_patients,
            active_percentage = EXCLUDED.active_percentage,
            growth_rate = EXCLUDED.growth_rate
    """))
```

### Data Marts Criados

#### 1. **patients**
- **Agregação:** Mensal + grupo demográfico
- **Métricas:**
  - Total de pacientes
  - Pacientes ativos/inativos
  - Percentual de ativação
  - Taxa de crescimento mês a mês
- **Dimensões:** período, faixa etária, gênero, orientação, pronome

#### 2. **patient_disability**
- **Agregação:** Mensal + tipo de deficiência
- **Métricas:**
  - Total de pacientes por tipo de deficiência
  - Pacientes ativos/inativos com deficiência

#### 3. **professionals**
- **Agregação:** Por profissional
- **Métricas:**
  - Total de atendimentos concluídos
  - Média de avaliação recebida
- **Dimensões:** especialidade, estado, perfil

#### 4. **professional_appointments**
- **Agregação:** Mensal + profissional
- **Métricas:**
  - Total de atendimentos
  - Taxa de conclusão
  - Taxa de cancelamento
  - Tempo médio de espera
- **Dimensões:** período, especialidade, profissional

---

## 💾 Carga

A carga é realizada ao final de cada etapa, utilizando a estratégia **UPSERT** (INSERT + UPDATE):

```sql
INSERT INTO table_name (columns...)
VALUES (...)
ON CONFLICT (primary_key) DO UPDATE SET
    column1 = EXCLUDED.column1,
    column2 = EXCLUDED.column2,
    ...
```

### Fluxo de Carga

```
[Banco Origem] 
    ↓ INSERT/UPDATE
[Staging 1] 
    ↓ UPSERT
[Staging 2]
    ↓ UPSERT
[Model]
    ↓ UPSERT
[Mart]
```

### Garantias

- ✅ **Idempotência:** Executar múltiplas vezes não duplica dados
- ✅ **Atomicidade:** Usa transações para garantir consistência
- ✅ **Incrementalidade:** Apenas dados novos/modificados são processados

---

## 🔄 Fluxo Completo

### 1. Execução Manual via Portal

```
Usuário clica "Atualizar Dados" no portal
    ↓
POST /api/etl/run
    ↓
_rodar_etl_staging1(conn)  [Extração]
    ↓
_rodar_etl_staging2(conn)  [Transformação]
    ↓
_rodar_etl_model(conn)     [Modelagem]
    ↓
_rodar_etl_mart(conn)      [Agregação]
    ↓
commit()
    ↓
Dashboards atualizados no Metabase
```

### 2. Tempo de Execução Estimado

| Etapa | Tempo Médio | Volume de Dados |
|-------|-------------|-----------------|
| Staging 1 | ~30s | ~10.000 registros |
| Staging 2 | ~45s | ~10.000 registros |
| Model | ~60s | 1 fato + 6 dimensões |
| Mart | ~30s | 4 tabelas agregadas |
| **TOTAL** | **~2-3 min** | - |

---

## ⚙️ Execução

### Via Portal Web

1. Acessar: http://18.212.222.62/
2. Fazer login
3. Clicar em "Atualizar Dados"
4. Aguardar conclusão do pipeline

### Via API (Endpoints Flask)

```bash
# Executar pipeline completo
curl -X POST http://44.197.116.219/api/etl/run

# Executar apenas Staging 1
curl -X GET http://44.197.116.219/upload/staging1

# Executar apenas Staging 2
curl -X GET http://44.197.116.219/upload/staging2

# Executar apenas Model
curl -X GET http://44.197.116.219/upload/model

# Executar apenas Mart
curl -X GET http://44.197.116.219/upload/mart
```

### Resposta de Sucesso

```json
{
    "status": "success",
    "message": "ETL pipeline executado com sucesso",
    "timestamp": "2025-12-02T10:30:00",
    "results": {
        "staging1": {"rows": 10234},
        "staging2": {"rows": 10234},
        "model": {"tables": 7},
        "mart": {"tables": 4}
    }
}
```

---

## 🔍 Observações Importantes

### Idempotência
O uso de `ON CONFLICT DO UPDATE` garante que o pipeline pode ser executado múltiplas vezes sem duplicar dados ou causar erros.

### Modularidade
Cada etapa pode ser executada isoladamente via endpoints Flask, permitindo:
- Debugging facilitado
- Reprocessamento de etapas específicas
- Testes unitários por camada

### LGPD Compliance
Dados sensíveis são **anonimizados** no Staging 2:
- `first_name` → NULL
- `last_name` → NULL
- Apenas dados agregados são mantidos

### Logs e Auditoria
Todas as execuções geram logs para:
- Troubleshooting
- Auditoria de conformidade
- Monitoramento de performance

### Performance
- Índices otimizados nas chaves primárias
- Uso de CTEs (Common Table Expressions) para queries complexas
- Tabelas marts pré-agregadas para consultas rápidas

---

## 📚 Referências

- [PostgreSQL UPSERT Documentation](https://www.postgresql.org/docs/current/sql-insert.html)
- [Kimball Dimensional Modeling](https://www.kimballgroup.com/)
- [Flask Documentation](https://flask.palletsprojects.com/)
