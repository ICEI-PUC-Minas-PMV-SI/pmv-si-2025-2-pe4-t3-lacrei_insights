# 🎨 Projeto de Interface - Lacrei Insights

## 📋 Visão Geral

A interface do **Lacrei Insights** foi desenvolvida com foco em **simplicidade, acessibilidade e eficiência**, atendendo as necessidades de gestores e voluntários da Lacrei Saúde que precisam acessar indicadores e métricas de forma rápida e intuitiva.

### Princípios de Design

- ✅ **Simplicidade:** Interface limpa e minimalista, sem elementos desnecessários
- ✅ **Acessibilidade:** Conformidade com WCAG 2.1 (contraste, tamanhos de fonte, navegação por teclado)
- ✅ **Responsividade:** Funciona perfeitamente em desktop, tablet e mobile
- ✅ **Consistência:** Padrões visuais uniformes em todas as telas
- ✅ **Eficiência:** Acesso rápido às funcionalidades principais (máximo 2 cliques)

---

## 🔄 User Flow

### Fluxo Principal do Usuário

```
┌─────────────────┐
│   Página Inicial│
│   (Não autenticado)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Tela de Login  │ ← RF-10: Autenticação
└────────┬────────┘
         │ [Credenciais válidas]
         ▼
┌─────────────────┐
│  Dashboard Home │ ← Tela principal após login
│  [2 opções]     │
└────────┬────────┘
         │
    ┌────┴─────┐
    │          │
    ▼          ▼
┌─────────┐ ┌──────────────┐
│Atualizar│ │ Ver Gráficos │
│  Dados  │ │              │
│         │ │              │
│ RF-11   │ │   RF-12      │
└────┬────┘ └──────┬───────┘
     │             │
     │             ▼
     │      ┌─────────────────┐
     │      │   Dashboards    │
     │      │   [3 abas]      │
     │      └─────────┬───────┘
     │                │
     │        ┌───────┼───────┐
     │        │       │       │
     │        ▼       ▼       ▼
     │    ┌──────┐┌──────┐┌──────┐
     │    │Visão ││Pac   ││Prof  │
     │    │Geral ││      ││      │
     │    └──────┘└──────┘└──────┘
     │        │       │       │
     │        └───────┼───────┘
     │                │
     └────────────────┼─> [Volta ao Dashboard Home]
                      │
                      ▼
                 ┌─────────┐
                 │  Sair   │
                 └─────────┘
```

### Fluxo de Atualização de Dados (ETL)

```
[Dashboard Home]
      │
      ▼ [Clica em "Atualizar Dados"]
┌─────────────────┐
│ Modal de        │
│ Confirmação     │
└────────┬────────┘
         │ [Confirma]
         ▼
┌─────────────────┐
│ Loading Spinner │ ← Feedback visual
│ "Atualizando... │
│                 │
└────────┬────────┘
         │
         ▼ [ETL completo]
┌─────────────────┐
│ Modal de Sucesso│
│ "Dados          │
│  atualizados!"  │
└────────┬────────┘
         │
         ▼
[Retorna ao Dashboard Home]
```

---

## 🖼️ Telas da Interface

### 1. Tela de Login

**Requisitos Atendidos:** RF-10, RNF-06, RNF-08

<img width="1842" height="913" alt="image1" src="https://github.com/user-attachments/assets/1db1b758-e82b-4298-ad13-486547725f41" />


**Descrição da Interface:**

A tela de login apresenta um **layout dual-panel** moderno e clean:

**Painel Esquerdo (Branding):**
- Logo da Lacrei Saúde (ícone circular com "LS" em verde-água)
- Título: **"Lacrei Saúde"**
- Subtítulo de boas-vindas: **"Bem-vindo(a)!"**
- Texto descritivo: _"Acesse o painel interno e acompanhe os indicadores da Lacrei Saúde."_
- Background: Fundo claro minimalista

**Painel Direito (Formulário):**
- Header: **"Entrar"** com subtítulo _"Use suas credenciais para continuar"_
- Campo **"Usuário"** com placeholder "Digite seu usuário"
- Campo **"Senha"** com placeholder "Digite sua senha" (ícone de mostrar/ocultar)
- Botão primário: **"Acessar painel"** (verde-água #00B894)
- Footer: "Lacrei Saúde - Acesso interno"

**Características Técnicas:**
- Fundo geral: Verde-água muito claro (#F0FFFE)
- Cards com sombras suaves (elevation)
- Design responsivo e acessível
- Validação de campos obrigatórios
- Feedback visual nos inputs (ícones azuis)

**Elementos:**
- Campo de email (type="email", required)
- Campo de senha (type="password", required)
- Checkbox "Lembrar-me" (opcional)
- Botão "Entrar" (submit)
- Link "Esqueceu a senha?" (recuperação)

**Responsividade:**
- Desktop: 400px de largura, centralizado
- Mobile: 100% da largura com padding lateral

**Acessibilidade:**
- Labels descritivos para screen readers
- Navegação por Tab
- Mensagens de erro claras
- Contraste WCAG AA (4.5:1)

---

### 2. Dashboard Home (Tela Principal)

**Requisitos Atendidos:** RF-10, RF-11, RF-12, RNF-04


<img width="1835" height="909" alt="image2" src="https://github.com/user-attachments/assets/dbdf2395-4103-4436-9ae6-5f44a827d5b3" />


**Descrição da Interface:**

A tela principal após login apresenta um **design limpo e funcional** com duas ações principais:

**Header (Barra Superior):**
- Logo "LS" + "Lacrei Saúde" (esquerda)
- Botões: **"Github"** e **"Sair"** (direita, estilo ghost)
- Cor: Branco com borda inferior sutil

**Card de Boas-Vindas:**
- Título: **"Painel Lacrei Saúde"**
- Descrição: _"Execute as rotinas de ETL e acompanhe os dashboards da Lacrei Saúde."_
- Background: Branco com border-radius suave

**Dois Cards de Ação (Side by Side):**

**Card 1 - Atualizar Banco de Dados:**
- Ícone: 🔄 (implícito)
- Título: **"Atualizar Banco de Dados"**
- Descrição: _"Roda o ETL da staging 01 para staging 02 e atualiza os dados do mart."_
- Botão: **"ETL Rodar ETL"** (verde #00B894, full-width)
- **Atende:** RF-11 (Disparar pipeline ETL)

**Card 2 - Ver Dashboard:**
- Ícone: 📊 (implícito)
- Título: **"Ver Dashboard"**
- Descrição: _"Carrega o Metabase com os KPIs de experiência e atendimento."_
- Botão: **"BI Abrir Metabase"** (verde #00B894, full-width)
- **Atende:** RF-12 (Acessar dashboards)

**Preview do Dashboard:**
Abaixo dos cards, há um **preview inline** mostrando o dashboard Visão Geral - Atendimentos do Metabase com:
- Abas: Visão Geral - Atendimentos | Pacientes | Profissionais
- Filtros: Agrupamento de tempo, Trimestre, Especialidade
- KPIs visíveis: Total de atendimentos (68), Taxa de cancelamento (10), Taxa de tempo de espera (8,201.74)

**Paleta de Cores:**
- Primary: Verde-água #00B894
- Background: Verde-água muito claro #F0FFFE
- Cards: Branco #FFFFFF
- Texto: Cinza escuro #2D3748

---

---

### 5. Arquitetura ETL (Diagrama Técnico)

**Requisitos Atendidos:** RF-01, RF-02, RF-03, RNF-05

<img width="1152" height="462" alt="image5" src="https://github.com/user-attachments/assets/270508a9-8eae-41e1-aa77-5c0fb46fa19c" />


**Descrição do Diagrama:**

O diagrama mostra a **arquitetura completa do pipeline ETL**:

**1. Fonte de Dados (Esquerda):**
- **PostgreSQL** (ícone banco de dados roxo)
- Banco de dados transacional da Lacrei Saúde

**2. Integração de Dados - ETL (Centro):**

Caixa principal com **3 etapas numeradas**:

**Etapa 1 - Extração:**
- Texto: "Coleta dos dados brutos do banco relacional"
- Seta para: **Staging Area**
- API Python automatizada

**Etapa 2 - Transformação:**
- Texto: "Tratamento, limpeza e montagem dos dados"
- Logo: **Pandas** (biblioteca Python)
- Processa dados da Staging Area

**Etapa 3 - Carga:**
- Texto: "Carregamento dos dados no data warehouse"
- Seta para: **Amazon RDS** (banco DW em nuvem)

**3. Visualização e Análise de Dados (Direita):**
- **Metabase** (logo oficial)
- Flecha para: **Front-end (client)**
- Resultado: **Dashboards e relatórios**

**Fluxo Visual:**
```
PostgreSQL → Python API → [Extração → Transformação → Carga] → Amazon RDS → Metabase → Dashboards
```

**Cores:**
- Roxo/Rosa: Bancos de dados
- Verde-água: Componentes Lacrei
- Fundo: Bege claro


**Estados do Modal:**

**1. Confirmação (Estado Inicial)**
- Tela de Login
- Botão: Acessar Painel

**3. Sucesso**

<img width="1626" height="806" alt="2025-12-02 (25)" src="https://github.com/user-attachments/assets/498c7df4-18c4-40fd-9b60-1f789cde418c" />


---

### 6. Modelo do Data Warehouse (Star Schema)

**Requisitos Atendidos:** RF-03, RF-09

<img width="2226" height="1327" alt="modeloDimensional" src="https://github.com/user-attachments/assets/c5e27a27-3a90-45a9-a908-ac32c2929c6a" />



**Descrição do Diagrama (DBDiagram):**

O diagrama mostra a **modelagem dimensional completa** do Data Warehouse:

**Tabela Fato Central:**

**`fact_lacreisaude_appointments`** (centro do schema)
- Campos chave:
  - `appointment_sk` (PK, INT)
  - `appointment_fingerprint` (VARCHAR)
  - `created_date_sk` (FK para dim_date, INT NN)
  - `appointment_date_sk` (FK para dim_date, INT NN)
  - `status` (VARCHAR, NN)
  - `type` (VARCHAR, NN)
  - `waiting_time` (DECIMAL)
  - `professional_sk` (FK, INT NN)
  - `patient_sk` (FK, INT NN)
  - `clinic_sk` (FK, INT)
  - `report_sk` (FK, INT)
  - `cancellation_reason` (TIMESTAMP)
  - `cancellation_created_at` (VARCHAR)

**Dimensões (Star Schema):**

**1. `dim_lacreisaude_patient`** (esquerda inferior)
- `patient_sk` (PK)
- `patient_key` (VARCHAR)
- `created_at`, `first_name` (NULL), `last_name` (NULL)
- `birth_date`, `is_active`
- `profile_type`, `ethnic_group`
- `gender_identity`, `pronoun`
- `sexual_orientation`, `disability_type` (TEXT[])

**2. `dim_lacreisaude_date`** (esquerda superior)
- `date_sk` (PK)
- `calendar_date` (DATE NN)
- `day`, `month`, `year`, `week`, `quarter` (INT NN)

**3. `dim_lacreisaude_clinic`** (topo centro)
- `clinic_sk` (PK)
- `created_at`, `is_presential_clinic`, `is_online_clinic`
- `name`, `zip_code`, `city`, `state`
- `consult_price` (NUMERIC), `duration_minutes` (INT)
- `accepts_insurance_providers`, `provides_accessibility_standards`
- Campos para clínica online (price, duration, insurance)

**4. `dim_lacreisaude_professional`** (direita superior)
- `professional_sk` (PK)
- `profile_status`, `active`, `published`
- `specialty`, `ethnic_group`
- `gender_identity`, `pronoun`
- `sexual_orientation`, `profile_type`
- `state`, `disability_type` (TEXT[])

**5. `dim_lacreisaude_report`** (inferior centro)
- `report_sk` (PK)
- `created_at` (TIMESTAMP)
- `feedback` (VARCHAR)
- `evaluation` (INT) - nota de avaliação

**Relacionamentos (Foreign Keys):**
- Todas as dimensões conectadas à tabela fato
- Relacionamentos 1:N (uma dimensão, muitos fatos)
- Chaves substitutas (surrogate keys) para todas as tabelas

**Cores do Diagrama:**
- Azul escuro: Tabelas e headers
- Branco: Conteúdo das tabelas
- Linhas: Relacionamentos FK

<img width="1498" height="927" alt="2025-12-02 (23)" src="https://github.com/user-attachments/assets/c3ec532d-4ac5-422a-9c83-aa3ae4420c0d" />


**Elementos:**
- Navegação por abas (Tabs)
- Iframe do Metabase embedding
- Botão "Voltar" para Dashboard Home
- Info de última atualização

**Abas (Tabs):**

1. **📊 Visão Geral** (RF-05)
   - Total de atendimentos finalizados
   - Taxa de cancelamento
   - Gráfico temporal de atendimentos
   - Média de avaliação por estado
   - Preço médio de consulta
   - Atendimentos por especialidade

2. **👨‍⚕️ Profissionais** (RF-05)
   - Total por especialidade
   - Distribuição geográfica (estados)
   - Profissionais ativos
   - Distribuição por avaliação

3. **🏥 Pacientes** (RF-05, RF-08)
   - Total por faixa etária
   - Pacientes por tipo de deficiência
   - Status de agendamentos
   - Taxa de crescimento

---

---

### 3. Dashboard - Visão Geral (Atendimentos)

**Requisitos Atendidos:** RF-04, RF-05, RF-08, RNF-02, RNF-03

<img width="1397" height="1354" alt="image4" src="https://github.com/user-attachments/assets/b77a2723-5f58-4054-a4b1-2e218284e94d" />


**Descrição da Interface:**

Dashboard do **Metabase** integrado mostrando métricas de atendimentos:

**Header e Navegação:**
- Título: **"Lacrei Saúde BI"**
- Abas: **Visão Geral - Atendimentos** (ativa) | Pacientes | Profissionais
- Ícone home (canto superior direito)

**Filtros Interativos (Barra de Filtros):**
- 📅 **Agrupamento de tempo** (dropdown)
- 📅 **Trimestre** (dropdown)
- 🎯 **Especialidade** (dropdown)

**KPIs Principais (Cards Grandes):**

1. **Total de atendimentos finalizados:** `68`
2. **Taxa de cancelamento:** `10`
3. **Taxa de tempo de espera:** `8,201.74` (em dias/horas)

**Gráficos e Visualizações:**

**1. Atendimentos: finalizados e cancelados (Área/Linha)**
- Gráfico de área temporal (2021-2025)
- Legenda: Atendimentos finalizados (verde) | Atendimentos cancelados (laranja)
- Eixo X: Mês (janeiro 2021 a janeiro 2025)
- Eixo Y: Quantidade (0-4)
- **Insight:** Visualiza tendências e sazonalidade

**2. Taxa de avaliação de profissional por estado (Barras Horizontais)**
- Estados: Minas Gerais, Paraná, Rio de Janeiro, São Paulo
- Escala: 0-5 (média de avaliação)
- Cor: Roxo (#8B5CF6)
- **Insight:** Compara satisfação entre estados

**3. Tabela: Taxa de avaliação por atendimentos e profissional**
- Colunas: Professional ID | Total de atendimentos | Média de Avaliação
- Exemplo: ID 3, 0 atendimentos, avaliação 0 (destaque vermelho)
- **Insight:** Identifica profissionais com baixo desempenho

**4. Média de preço de consulta de clínicas ao longo do tempo (Linha)**
- Gráfico de linha temporal
- Eixo Y: Preço (0-250)
- Padrão: Oscilações periódicas
- **Insight:** Monitora variação de preços

---

### 6. Dashboard - Profissionais (Detalhado)

**Requisitos Atendidos:** RF-05, RNF-03

<img width="1397" height="1344" alt="profissionais" src="https://github.com/user-attachments/assets/b57e4586-8d1f-4315-9f9d-4d0f843b5144" />

---

---

### 4. Dashboard - Pacientes

**Requisitos Atendidos:** RF-05, RF-08, RNF-02, RNF-03

<img width="1408" height="1058" alt="pacientes" src="https://github.com/user-attachments/assets/d3d4a319-3cf8-45dd-a485-7c7e6f19bf7e" />


**Descrição da Interface:**

Dashboard do **Metabase** focado em métricas de pacientes:

**Header e Navegação:**
- Título: **"Lacrei Saúde BI"**
- Abas: Visão Geral - Atendimentos | **Pacientes** (ativa) | Profissionais

**Filtros Interativos:**
- 📅 **Agrupamento de tempo** (dropdown)
- 📅 **Trimestre** (dropdown)
- 👤 **Identidade de gênero** (dropdown)
- 🏳️‍🌈 **Sexualidade** (dropdown)
- 🌍 **Etnia** (dropdown)

**Visualizações Principais:**

**1. Total de pacientes por faixa-etária (Donut Chart)**
- Gráfico de rosca colorido
- Legenda:
  - 26-35: **63.16%** (rosa - maior fatia)
  - 36-45: **26.32%** (amarelo)
  - 18-25: **5.26%** (verde claro)
  - 46-60: **5.26%** (laranja)
- Centro: **19 Total**
- **Insight:** Maioria dos pacientes entre 26-35 anos

**2. Total de pacientes por tipo de deficiência (Donut Chart)**
- Gráfico de rosca multicolorido
- Legenda:
  - Deficiência ... : **25.00%** (roxo)
  - Deficiência ... : **25.00%** (laranja)
  - Deficiência ... : **16.67%** (azul claro)
  - Transtorno ... : **16.67%** (verde)
  - Deficiência I...: **8.33%** (rosa)
  - Deficiência P...: **8.33%** (verde claro)
- Centro: **12 Total**
- **Insight:** Distribuição equilibrada de tipos de deficiência

**3. Pacientes Ativos (Métrica Grande)**
- Card único com número grande: **18**
- Design minimalista
- **Insight:** Quantidade de pacientes atualmente ativos

**4. Taxa de crescimento de pacientes (Gráfico de Linha)**
- Eixo X: Anos (2020-2025)
- Eixo Y: Média de Growth Rate (0-50)
- Linha: Roxo claro
- Tendência: **Crescimento exponencial em 2025** (pico ~50)
- **Insight:** Crescimento acelerado recente


## 🎨 Análise de Design

### Identidade Visual

**Paleta de Cores Principal:**
- **Primary:** Verde-água #00B894 (identidade Lacrei Saúde)
- **Background:** Verde-água muito claro #F0FFFE
- **Cards:** Branco #FFFFFF
- **Texto:** Cinza escuro #2D3748
- **Acentos:** Roxo #8B5CF6 (gráficos Metabase)

**Typography:**
- Sans-serif moderna 
- Hierarquia clara: H1 (títulos grandes) → Body (textos descritivos)

### Padrões de UI

**Cards:**
- Border-radius suave (~12px)
- Sombras elevation sutis (box-shadow)
- Padding generoso (24px)
- Hover states nos botões

**Botões:**
- Primary: Verde #00B894, full-width
- Ghost: Transparente com border
- Border-radius: ~8px
- Estados: hover, active, disabled

**Inputs:**
- Border sutil com foco em azul
- Ícones inline (usuário, senha)
- Placeholders descritivos
- Feedback visual instantâneo

---

## 📱 Responsividade Implementada

### Breakpoints Observados

**Desktop (> 1024px):**
- Layout de 2 colunas para cards de ação
- Dashboards Metabase em largura completa
- Sidebar de filtros visível

**Tablet/Mobile:**
- Cards empilhados verticalmente
- Filtros colapsáveis
- Gráficos adaptáveis (scrollable)

---

## ♿ Acessibilidade (WCAG 2.1)

### Conformidade RNF-08

✅ **Contraste:** Mínimo 4.5:1 (Nível AA)
✅ **Navegação por Teclado:** Tab, Enter, Esc
✅ **Screen Readers:** Labels e ARIA attributes
✅ **Tamanhos de Fonte:** Mínimo 16px
✅ **Alvos de Toque:** Mínimo 44x44px
✅ **Mensagens de Erro:** Descritivas e visíveis

---

## 🔗 Links Úteis

- [Figma - Protótipo Interativo](https://www.figma.com/) (Ferramenta recomendada)
- [Adobe XD](https://www.adobe.com/products/xd.html)
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Material Design](https://material.io/design)
- [User Flow Best Practices](https://www.nngroup.com/articles/user-flow/)

---

### Gerenciamento de Estado

- **Autenticação:** JWT em cookies httpOnly
- **ETL Status:** React Context API
- **UI State:** useState/useReducer

---
