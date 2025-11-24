# Documentação do Processo ETL

Este documento detalha o pipeline ETL do projeto, explicando cada etapa, função e operação dos principais arquivos Python.

## Sumário
- [Extração (Staging 1)](#extração-staging-1)
- [Transformação (Staging 2)](#transformação-staging-2)
- [Models](#models)
- [Marts](#marts)
- [Carga](#carga)

---

## Extração (Staging 1)

Arquivo: `app/routes/etl/staging1.py`

O Staging 1 é responsável por extrair dados do banco relacional de origem e popular o schema `lacreisaude_staging_01`.

### Funções Principais

#### `def _rodar_etl_staging1(conn)`
Executa todos os jobs de extração para staging 1.

```python
@bp_staging1.route('/upload/staging1', methods=['GET'])
def upload_staging1():
    ...
    result = _rodar_etl_staging1(conn)
    ...
```

#### Funções de Extração por Tabela
Cada tabela tem uma função dedicada, por exemplo:

```python
def _etl_lacreiid_appointment(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_01.lacreiid_appointment (...)
    """))
    ...
    # Extração dos dados do banco de origem
    ...
```

Essas funções:
- Garantem a existência da tabela destino
- Extraem dados do banco de origem
- Inserem no staging 1

---

## Transformação (Staging 2)

Arquivo: `app/routes/etl/staging2.py`

O Staging 2 transforma e normaliza os dados do Staging 1, aplicando regras de negócio e tipagem.

### Funções Principais

#### `def _rodar_etl_staging2(conn)`
Executa todos os jobs de transformação para staging 2.

#### Funções de Transformação por Tabela
Exemplo:

```python
def _rodar_etl_appointment(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_staging_02.lacreiid_appointment (...)
    """))
    ...
    upsert_sql = """
        WITH src_raw AS (...)
        ...
        INSERT INTO lacreisaude_staging_02.lacreiid_appointment ...
        ON CONFLICT (id) DO UPDATE ...
    """
    row = conn.execute(text(upsert_sql)).mappings().one()
    return {...}
```

Essas funções:
- Criam tabelas de destino no `staging_02`
- Transformam e limpam os dados (tipagem, normalização, deduplicação)
- Fazem upsert (insert/update) dos dados transformados

Outras funções seguem o mesmo padrão para cada tabela: `_rodar_etl_profile`, `_rodar_etl_user`, `_rodar_etl_clinic`, etc.

---

## Models

Arquivo: `app/routes/etl/model.py`

Responsável por consolidar e modelar os dados para uso analítico, criando tabelas de fatos e dimensões.

### Funções Principais

#### `def _rodar_etl_model(conn)`
Executa todos os jobs de modelagem.

```python
def _rodar_etl_model(conn):
    ...
    # Criação de dimensões
    _etl_dim_professional(conn)
    _etl_dim_patient(conn)
    ...
    # Criação de fatos
    _etl_fact_lacreisaude_appointments(conn)
    ...
```

#### Funções de Modelagem
Exemplo:

```python
def _etl_dim_professional(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_model.dim_professional (...)
    """))
    ...
    # Popula a dimensão com dados do staging_02
    ...
```

Cada dimensão e fato tem uma função dedicada, que:
- Cria a tabela de destino
- Realiza joins e agregações necessárias
- Popula a tabela modelada

---

## Marts

Arquivo: `app/routes/etl/mart.py`

Responsável por criar data marts otimizados para consumo por dashboards e BI.

### Funções Principais

#### `def _rodar_etl_mart(conn)`
Executa todos os jobs de criação de marts.

```python
def _rodar_etl_mart(conn):
    ...
    _etl_mart_appointments(conn)
    _etl_mart_feedback(conn)
    ...
```

#### Funções de Mart
Exemplo:

```python
def _etl_mart_appointments(conn):
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS lacreisaude_mart.mart_appointments (...)
    """))
    ...
    # Agrega e popula o mart
    ...
```

Cada mart é alimentado a partir das tabelas modeladas, com agregações e cálculos específicos para análise.

---

## Carga

A carga é realizada ao final de cada etapa, com as funções de upsert (insert/update) garantindo que os dados estejam sempre atualizados e sem duplicidade.

- O staging 1 carrega do banco relacional para staging_01
- O staging 2 transforma e carrega para staging_02
- O model.py carrega para tabelas de fatos e dimensões
- O mart.py carrega para data marts

---

## Observações
- Todas as funções são idempotentes: podem ser executadas múltiplas vezes sem causar duplicidade.
- O uso de `ON CONFLICT DO UPDATE` garante atualização incremental.
- O pipeline é modular: cada etapa pode ser executada isoladamente via endpoints Flask.

---


