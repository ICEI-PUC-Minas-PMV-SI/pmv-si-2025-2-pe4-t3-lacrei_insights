# Documentação do Processo ETL — Lacrei Insights

Versão: 1.0
Data: 2025-12-02
Autor: Equipe de Integração (gerado automaticamente)

Resumo
- Objetivo: descrever o pipeline ETL presente em `CODIGO/app/routes/etl/` (staging → model → mart), explicar cada arquivo/função/consulta SQL e listar ajustes necessários para integrar a solução ao banco de dados de um parceiro sem que o parceiro precise alterar sua base.
- Escopo: `staging1.py`, `staging2.py`, `model.py`, `mart.py` (ETL principal). Considerações sobre anonimização, idempotência e validação de métricas.

**Visão Geral da Arquitetura**
- Camadas:
  - **Origem**: tabelas ou exports do sistema parceiro (esperado inicialmente em `lacreisaude_staging_01`).
  - **Staging 02**: `lacreisaude_staging_02` — tabela tipada, limpeza e deduplicação.
  - **Model**: `lacreisaude_model` — dimensões (dim_*) e fato (`fact_lacreisaude_appointments`).
  - **Mart**: `lacreisaude_mart` — tabelas agregadas e métricas consumidas por dashboards.
- Execução: endpoint `/upload/staging` (implementado em `staging2.py`) que orquestra os upserts e chama as funções do model e do mart.

**Observação Importante sobre Mapeamentos e Métricas**
- Muitas métricas dependem de campos cuja semântica pode variar entre bases (ex.: campo `type` em appointments). No código atual o ETL assume que `type` indica modalidade (`Online` ou `Presencial`). Se o sistema do parceiro usar outro valor/coluna para essa informação (ou nomes diferentes), as métricas relacionadas a modalidade — por exemplo `completed_appointments_online`, `cancelled_appointments_presencial`, `cancellation_rate_online`, etc. — NÃO irão funcionar corretamente até que o ETL seja adaptado para mapear os valores reais do parceiro.
- Resumo prático: o parceiro NÃO precisa mudar o seu banco; o ETL deve ser ajustado para acomodar a estrutura e os valores do banco do parceiro. A documentação abaixo indica exatamente onde e como adaptar.

**Instruções Gerais para Integração**
- Passo 1: fornecer amostra (CSV/SQL) com ~20 linhas de cada tabela relevante: appointments, cancellations, users, reports, professionals, clinics, address_state, etc.
- Passo 2: informar nomes exatos das tabelas/colunas no banco parceiro ou autorizar execução de queries de amostra (ex.: `SELECT ... LIMIT 20`).
- Passo 3: validar formatos de data/time, valores possíveis para `status`/`type` e disponibilidade de identificadores (user_id, professional_id, appointment_id).
- Passo 4: revisar política de PII e confirmar quais campos podem ser hash/anonimizados.
- Permissões DB necessárias para o usuário que roda o ETL: `CREATE SCHEMA`, `CREATE TABLE`, `CREATE INDEX`, `SELECT`, `INSERT`, `UPDATE`, `DELETE` (se rodar scripts de limpeza).

**Arquivo: `staging1.py`**
- Propósito: (quando presente) preparar/importar dados raw para `lacreisaude_staging_01`. Em muitos cenários de integração direta o parceiro já fornecerá tabelas; `staging1.py` não é obrigatório.
- Pontos chave:
  - Não aplica cast rígido — armazena raw; normalmente usado em importações a partir de JSON/CSV.
  - Se o parceiro exporta direto para DB, podemos pular `staging1.py` e apontar `staging2.py` para tabelas do parceiro.
- Ajustes típicos:
  - Atualizar nomes da origem clicando nas queries de `staging2.py` para ler da schema do parceiro.

**Arquivo: `staging2.py`**
- Propósito: harmonização. Para cada entidade (privacydocument, appointment, cancellation, profile, user, clinic, professional, etc.) há uma função `_rodar_etl_<nome>(conn)` que:
  - Verifica existência da tabela fonte.
  - Cria schema `lacreisaude_staging_02` e tabela destino com tipos controlados.
  - Lê a fonte, aplica limpeza (NULLIF/TRIM), normaliza timestamps e executa um upsert idempotente usando `ON CONFLICT` e/ou estratégia com `ROW_NUMBER()` para dedupe antes do INSERT.
  - Retorna um dicionário com: `ok`, `msg`, `inserted`, `updated`, `source_rows`.
- Exemplo de técnicas usadas:
  - Dedup via `ROW_NUMBER() OVER (PARTITION BY <natural_key> ORDER BY updated_at DESC)` e `WHERE rn = 1`.
  - Casts defensivos: `CASE WHEN col ~ '^[0-9]+$' THEN col::integer ELSE NULL END`.
  - Timestamp parse: `NULLIF(TRIM(ts), '')::timestamptz AT TIME ZONE 'UTC'`.
- Ajustes que o parceiro deve fornecer/validar:
  - Nome das tabelas/colunas na base dele — atualizar os `SELECT FROM lacreisaude_staging_01.<tabela>` para `partner_schema.<tabela_real>`.
  - Formato das datas (se epoch, ajustar para `TO_TIMESTAMP(epoch/1000.0)` ou similar).
  - Se natural keys divergem (ex.: `appointment` não tem `id` diretamente), alterar `PARTITION BY` nos CTEs de dedupe.

**Arquivo: `model.py`**
- Propósito: construir o schema `lacreisaude_model` com dimensões e fato.
- Dimensões criadas (resumo):
  - `dim_lacreisaude_date` — date dimension populada incrementalmente com `generate_series` entre min/max de dados de staging.
  - `dim_lacreisaude_report` — unique index por `(created_at, feedback, evaluation)`.
  - `dim_lacreisaude_clinic` — unique index por `(name, city, state)`.
  - `dim_lacreisaude_professional` — unique index por `(full_name, state)`.
  - `dim_lacreisaude_patient` — unique index por `patient_key` (md5 de first|last|birth_date, por padrão).
- Fato: `fact_lacreisaude_appointments`
  - Estrutura: contém `appointment_fingerprint` (novo), `created_date_id`, `date_id`, `status`, `type`, `waiting_time`, `professional_id`, `patient_id`, `clinic_id`, `report_id`, `cancellation_*`.
  - Deduplicação/Idempotência: o ETL gera um fingerprint determinístico por appointment (MD5 de `src_appointment_id` + `date_id` por padrão) e faz `INSERT ... ON CONFLICT (appointment_fingerprint) DO UPDATE ...`. Isso evita duplicação nos re-runs do ETL.
  - Anonimização: após o join, `dim_lacreisaude_patient.first_name` e `.last_name` são setados para NULL para não persistir PII.
- Pontos a validar com o parceiro:
  - Se a base do parceiro não tem `first_name/last_name/birth_date`, precisamos indicar outra coluna para `patient_key` (ex.: `cpf`, `email` ou um `user_id`). O partner deve fornecer esse campo ou o ETL será ajustado para usar fingerprint baseado em outros atributos.
  - `dim_lacreisaude_professional` atualmente confia em `full_name + state` como natural key; se isso não for único, usar `professional_id` como base para fingerprint (hash) mas sem persistir o id original assim como fazemos para appointment.
  - Joins que associam `report` e `cancellation` estão baseados em heurísticas (matching por timestamps e conteúdo) — se o parceiro tiver `report_id`/`cancellation.appointment_id` consistentes, mapeie diretamente para eliminar heurísticas.

**Arquivo: `mart.py`**
- Propósito: gerar agregações e métricas finais em `lacreisaude_mart`.
- Tabelas de mart implementadas:
  - `patients` — métricas por faixa etária/gênero/sexual_orientation/ethnic_group, com porcentagens e crescimento.
  - `patient_disability` — métricas por tipo de deficiência.
  - `professionals` — perfil agregado por professional (total_appointments, avg_feedback_rating).
  - `professional_appointments` — agregações mensais por professional/specialty com: `total_appointments`, `completed_appointments`, `completed_appointments_online`, `completed_appointments_presencial`, `cancelled_appointments_online`, `cancelled_appointments_presencial`, `completion_rate`, `cancellation_rate_online`, `cancellation_rate_presencial`, `avg_waiting_time`.
- Pontos críticos sobre `type` e métricas de modalidade:
  - O ETL do mart considera `type = 'Online'` e `type = 'Presencial'` para separar as métricas por modalidade. Se o sistema do parceiro não usa esses literais (ex.: usa `MODE=TELEMED`, `channel='video'`, `is_remote=true`, etc.), então os cálculos `completed_appointments_online`, `cancelled_appointments_presencial` e as taxas associadas estarão incorretos.
  - A recomendação: criar uma etapa de normalização no `staging2.py` ou no `model.py` que converta os valores reais do parceiro para a taxonomia esperada (`Online` / `Presencial` / `Outro`). Exemplo de mapeamento:
    ```sql
    CASE
      WHEN LOWER(type) IN ('online','telemed','teleconsulta','remote','remoto','video') THEN 'Online'
      WHEN LOWER(type) IN ('presencial','clinic','local','face-to-face') THEN 'Presencial'
      ELSE 'Outro'
    END AS type
    ```
  - Sem esse mapeamento, as métricas de cancelamento por modalidade não são confiáveis.

**Ajustes e Parametrizações Recomendadas**
- Criar arquivo de configuração de mapeamento (exemplo `CODIGO/config/field_map.example.yml`) contendo:
  - Tabela de origem por entidade (appointments, cancellations, users...)
  - Colunas de id, date, status, type, professional_id, user_id
  - Mapas de valores para `status` e `type` (lista de equivalências)
  - Campos PII a anonimizar
- Parametrizar parsing de datas (UTC vs local vs epoch) no mesmo arquivo de config.
- Permitir injeção de funções de transformação (por exemplo, small python functions que normalizam `type`), para facilitar o mapeamento sem editar SQL bruto.

**Validações / Queries de QA (exemplos que o parceiro deve rodar)**
- Verificar amostras:
  ```sql
  SELECT * FROM lacreisaude_staging_02.lacreiid_appointment LIMIT 20;
  ```
- Conferir counts por execução (1ª vs 2ª execução): o campo `inserted` deve ser >0 na 1ª execução e tipicamente 0 na 2ª (se nenhum registro novo chegou):
  - Use o endpoint `/upload/staging` — revisar `etls` e `resumo` no JSON de resposta.
- Verificar duplicados por fingerprint no fato:
  ```sql
  SELECT appointment_fingerprint, COUNT(*) cnt
  FROM lacreisaude_model.fact_lacreisaude_appointments
  GROUP BY appointment_fingerprint
  HAVING COUNT(*) > 1;
  ```
- Conferir métricas do mart (ex.: total de completed):
  ```sql
  SELECT SUM(completed_appointments) FROM lacreisaude_mart.professional_appointments;
  SELECT COUNT(*) FROM lacreisaude_model.fact_lacreisaude_appointments WHERE LOWER(status) = 'completed';
  ```
  Os dois números devem ser coerentes por período, considerando que `mart` agrupa por mês.

**Script de dedupe / backfill sugerido (descrição)**
- Objetivo: popular `appointment_fingerprint` para dados existentes e deduplicar registros antigos.
- Recomendações:
  - Fazer backup do DB antes de rodar.
  - Popular `appointment_fingerprint` com MD5 de um conjunto de campos estáveis (ex.: `src_id||'|'||date_id||'|'||professional_id`).
  - Detectar fingerprints com `COUNT > 1` e deletar duplicados mantendo o registro mais recente (ou com `MIN(id_fact_appointment)`).
- Posso gerar um script SQL pronto (me peça se quiser que eu o crie em `CODIGO/scripts/dedupe_fact_appointments.sql`).


**Observações finais e próximos passos**
- Importante: adaptação do ETL é esperada e recomendada — o código atual contém heurísticas razoáveis, mas precisa ser parametrizado para produção com base nos dados reais do parceiro.

