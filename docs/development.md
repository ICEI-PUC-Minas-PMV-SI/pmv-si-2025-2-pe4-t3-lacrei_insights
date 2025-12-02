## Programação de Funcionalidades

Este documento descreve a implementação do sistema por meio dos requisitos funcionais e não funcionais. Relaciona os requisitos atendidos aos artefatos criados (código fonte), além das estruturas de dados utilizadas e as instruções para acesso e verificação da implementação funcional no ambiente de hospedagem.

Para cada requisito funcional, pode ser entregue um artefato desse tipo.

---

## 📋 Requisitos Atendidos

As tabelas a seguir apresentam os requisitos funcionais e não-funcionais que relacionam o escopo do projeto com os artefatos criados:

### Requisitos Funcionais

| ID | Descrição do Requisito | Prioridade | Status | Artefato/Componente |
|----|------------------------|------------|--------|---------------------|
| RF-01 | Extrair dados da plataforma (pacientes, profissionais, atendimentos e feedbacks) | ALTA | ✅ Implementado | `etl/staging1/` |
| RF-02 | Executar processo de ETL em Python (padronização, limpeza e anonimização de dados sensíveis) | ALTA | ✅ Implementado | `etl/staging2/`, `etl/transformations/` |
| RF-03 | Armazenar os dados tratados em um Data Warehouse centralizado | ALTA | ✅ Implementado | `etl/model/`, Schema `lacreisaude_model` |
| RF-04 | Disponibilizar dashboards interativos no Metabase, acessíveis via portal web | ALTA | ✅ Implementado | Portal Web + Metabase Integration |
| RF-05 | Oferecer visualizações de KPIs (cadastros, atendimentos, feedbacks e distribuições) | ALTA | ✅ Implementado | Dashboards: Visão Geral, Profissionais, Pacientes |
| RF-06 | Permitir atualização periódica dos dados (semanal/mensal ou quase em tempo real) | MÉDIA | ✅ Implementado | Botão "Atualizar Dados" no portal |
| RF-07 | Gerar relatórios exportáveis (PDF/Excel) para gestores | MÉDIA | ⏳ Planejado | Funcionalidade do Metabase |
| RF-08 | Disponibilizar indicadores comparativos (ex.: evolução de cadastros mês a mês, crescimento de atendimentos por especialidade) | BAIXA | ✅ Implementado | Dashboards com métricas temporais |
| RF-10 | Disponibilizar portal web com autenticação (login) para acesso aos recursos analíticos | ALTA | ✅ Implementado | `app/frontend/`, `app/backend/auth/` |
| RF-11 | Oferecer ação "Atualizar dados" para disparo manual do pipeline ETL diretamente no portal | ALTA | ✅ Implementado | Endpoint `/api/etl/run` |
| RF-12 | Oferecer ação "Ver gráficos" que navega para a página de dashboards alimentada pela camada mart | ALTA | ✅ Implementado | Botão de navegação para Metabase |

### Requisitos Não Funcionais

| ID | Descrição do Requisito | Prioridade | Status | Implementação |
|----|------------------------|------------|--------|---------------|
| RNF-01 | Garantir anonimização e proteção de dados sensíveis em conformidade com a LGPD | ALTA | ✅ Implementado | Campos `first_name`, `last_name` = NULL; dados agregados apenas |
| RNF-02 | As visualizações devem ser compatíveis com navegadores modernos e com o Metabase | ALTA | ✅ Implementado | Frontend responsivo; Metabase embedding |
| RNF-03 | Consultas usuais ao DW devem ter tempo de resposta inferior a 5 segundos | ALTA | ✅ Implementado | Índices otimizados; tabelas mart agregadas |
| RNF-04 | O portal web deve ser responsivo, acessível em desktop e dispositivos móveis | ALTA | ✅ Implementado | Next.js + Tailwind CSS (design responsivo) |
| RNF-05 | O processo de ETL deve ser automatizado e possuir documentação de manutenção | ALTA | ✅ Implementado | Scripts Python documentados; `docs/integration.md` |
| RNF-06 | Deve haver autenticação e controle de acesso para usuários internos autorizados | MÉDIA | ✅ Implementado | Django + JWT Authentication |
| RNF-07 | O sistema deve suportar crescimento de volume de dados em escala sem perda de desempenho | MÉDIA | ✅ Implementado | Arquitetura dimensional (Star Schema); PostgreSQL |
| RNF-08 | O design das visualizações deve seguir padrões de acessibilidade digital, com contraste adequado e alternativas textuais | ALTA | ✅ Implementado | Cores acessíveis; labels descritivos |

---

## 🏗️ Estrutura de Dados

### Data Warehouse - Modelo Dimensional (Star Schema)

#### Tabela Fato

**`fact_lacreisaude_appointments`**
- Registra cada agendamento individual realizado entre paciente e profissional
- Permite análises quantitativas: contagem de agendamentos, cancelamentos, tempo de espera

| Campo | Tipo | Descrição |
|-------|------|-----------|
| appointment_sk | INTEGER | Chave substituta primária |
| patient_sk | INTEGER | FK para dim_patient |
| professional_sk | INTEGER | FK para dim_professional |
| clinic_sk | INTEGER | FK para dim_clinic |
| report_sk | INTEGER | FK para dim_report |
| cancellation_sk | INTEGER | FK para dim_cancellation |
| created_date_sk | INTEGER | FK para dim_date (data de criação) |
| appointment_date_sk | INTEGER | FK para dim_date (data do agendamento) |
| waiting_time_days | INTEGER | Tempo de espera em dias |
| is_cancelled | BOOLEAN | Indica se foi cancelado |
| is_completed | BOOLEAN | Indica se foi concluído |

#### Dimensões

**`dim_lacreisaude_date`** - Dimensão Temporal
- Auxilia análises temporais (dia, mês, ano, trimestre, semana)

**`dim_lacreisaude_patient`** - Pacientes
- Dados demográficos anonimizados
- Campos: etnia, identidade de gênero, pronome, orientação sexual, tipo de deficiência, faixa etária

**`dim_lacreisaude_professional`** - Profissionais
- Dados profissionais e demográficos
- Campos: especialidade, estado, status do perfil, dados de diversidade

**`dim_lacreisaude_clinic`** - Clínicas
- Dados de clínicas presenciais e online
- Campos: preço, duração, aceita plano, acessibilidade, localização

**`dim_lacreisaude_report`** - Feedbacks/Avaliações
- Avaliações dos profissionais pelos pacientes
- Campos: nota (evaluation), feedback textual

**`dim_lacreisaude_cancellation`** - Cancelamentos
- Motivos de cancelamento de consultas
- Campos: data, razão do cancelamento

---

## 📊 Data Marts

### `mart_patients`
Tabela agregada por período mensal e grupos demográficos contendo informações de engajamento dos pacientes.

**Principais métricas:**
- Total de pacientes cadastrados
- Pacientes ativos/inativos
- Taxa de crescimento mês a mês
- Distribuição por faixa etária, gênero, orientação sexual

### `mart_patients_disability`
Agregação mensal por tipo de deficiência.

**Principais métricas:**
- Total de pacientes por tipo de deficiência
- Pacientes ativos/inativos com deficiência

### `mart_professionals`
Agregação por profissional com dados de perfil e desempenho.

**Principais métricas:**
- Total de atendimentos concluídos
- Média de avaliação recebida
- Distribuição por especialidade e estado

### `mart_professional_appointments`
Agregação mensal por profissional com métricas de atendimentos.

**Principais métricas:**
- Total de atendimentos por mês
- Taxa de conclusão
- Taxa de cancelamento
- Tempo médio de espera

---

## 🔄 Pipeline ETL

### Staging 1 - Extração
**Função:** `_rodar_etl_staging1()`
- Extrai dados brutos do banco de dados de origem (PostgreSQL da Lacrei Saúde)
- Cria schema: `lacreisaude_staging_01`
- Tabelas extraídas: `appointment`, `user`, `profile`, `clinic`, `report`, `cancellation`, etc.

### Staging 2 - Transformação
**Principais transformações:**
- Padronização de tipos (datas, booleanos, inteiros)
- Limpeza de dados inconsistentes
- Deduplicação
- Normalização de campos (ex: estados, especialidades)
- **Anonimização:** `first_name` e `last_name` → NULL

### Model - Modelagem Dimensional
**Função:** `_rodar_etl_model()`
- Cria tabela fato e dimensões no schema `lacreisaude_model`
- Implementa Star Schema
- Gera chaves substitutas (surrogate keys)

### Mart - Agregações
**Função:** `_rodar_etl_mart()`
- Cria tabelas agregadas no schema `lacreisaude_mart`
- Dados otimizados para consumo pelos dashboards
- Pré-calcula métricas e KPIs

---

## 🌐 Ambiente de Produção

**URL do Portal:** http://44.197.116.219/

### Funcionalidades do Portal:

1. **Tela de Login**
   - Autenticação JWT
   - Controle de acesso para usuários autorizados

2. **Ação: Atualizar Dados**
   - Dispara o pipeline ETL completo
   - Atualiza todas as camadas (staging → model → mart)
   - Endpoint: `POST /api/etl/run`

3. **Ação: Ver Gráficos**
   - Redireciona para área de dashboards
   - Consome dados dos Data Marts
   - Integração com Metabase

### Dashboards Disponíveis:

#### 📊 Dashboard - Visão Geral
- Total de atendimentos finalizados
- Taxa de cancelamento
- Evolução temporal de atendimentos
- Média de avaliação por estado
- Preço médio de consulta ao longo do tempo
- Atendimentos por especialidade

#### 👨‍⚕️ Dashboard - Profissionais
- Total de profissionais por especialidade
- Distribuição geográfica (por estado)
- Profissionais ativos na plataforma
- Distribuição por média de avaliação

#### 🏥 Dashboard - Pacientes
- Total de pacientes por faixa etária
- Pacientes por tipo de deficiência
- Status de agendamentos
- Contagem de cadastros
- Taxa de crescimento de pacientes

---

## 🛠️ Stack Tecnológica

### Backend
- **Python 3.11+**
- **Django 4.x** + Django REST Framework
- **PostgreSQL** (banco de dados principal e DW)

### Frontend
- **Next.js 14**
- **React 18**
- **TypeScript**
- **Tailwind CSS**

### BI & Analytics
- **Metabase** (dashboards e visualizações)
- **Python** (scripts ETL)

### Infraestrutura
- **AWS** (hospedagem)
- **GitHub Actions** (CI/CD)

### Segurança
- **JWT** (autenticação)
- **CORS** (controle de origem)
- **LGPD Compliance** (anonimização de dados)

---

## 📚 Documentação Adicional

Para mais detalhes sobre cada componente:

- **Integração e ETL:** Ver `docs/integration.md`
- **Especificações de Requisitos:** Ver `docs/especification.md`
- **Contexto do Projeto:** Ver `docs/context.md`
- **Referências:** Ver `docs/references.md`

---

## 🧪 Testes

O projeto utiliza múltiplas camadas de testes:

- **Selenium:** Testes E2E com fluxo completo do usuário
- **Cypress:** Testes E2E focados no frontend
- **Jest:** Testes unitários em componentes React
- **Postman:** Testes de rotas e validação de APIs
- **Testes manuais:** Validações em cenários específicos

---

## 👥 Equipe de Desenvolvimento

- **Scrum Master:** Nico Rocha da Costa
- **Product Owner:** Daniel Dutra (Lacrei Saúde)
- **Desenvolvedores:**
  - João Gabriel Rosa Costa
  - Lucas Warley Matos Nascimento
  - Luini de Freitas Salles
  - Nico Rocha da Costa
  - Ryann Victor de Almeida Parreira
  - Sarah Cesar Martins dos Santos

---

## 📝 Notas de Versão

**Versão Atual:** 1.0.0 (Produção)

**Principais Entregas:**
- ✅ Pipeline ETL completo (4 camadas)
- ✅ Data Warehouse com Star Schema
- ✅ Data Marts otimizados
- ✅ Portal web com autenticação
- ✅ 3 Dashboards interativos no Metabase
- ✅ Conformidade LGPD (anonimização)
- ✅ Deploy em produção (AWS)
