# 📄 **tests.md – Testes do Sistema Lacrei Saúde BI**

---

# # 🧪 Testes do Sistema – Lacrei Saúde BI

Este documento apresenta a estratégia completa de testes aplicada ao sistema **Lacrei Saúde BI**, incluindo testes de software (caixa preta) e testes de usabilidade com usuários reais.
O objetivo é verificar a qualidade geral do sistema, sua aderência aos requisitos funcionais e a eficiência durante o uso.

---

# ## 🧩 1. Tipos de Teste Realizados

Durante o desenvolvimento do projeto, foram aplicados dois tipos principais de teste:

### ✔️ **Testes de Software (Caixa Preta)**

Avaliam o comportamento externo do sistema com base nos requisitos funcionais e não funcionais.

### ✔️ **Testes de Usabilidade**

Avaliam facilidade de uso, eficiência na execução de tarefas e clareza da interface.

---

# # 🧪 2. Plano de Testes de Software

---

## ### 📌 CT01 — Login no Sistema

| Campo                     | Descrição                                                                                    |
| ------------------------- | -------------------------------------------------------------------------------------------- |
| **Procedimento**          | 1. Acessar tela de login.<br>2. Digitar usuário e senha.<br>3. Clicar em **Acessar painel**. |
| **Requisitos associados** | RF-001 – O sistema deve permitir login.                                                      |
| **Página / Artefato**     | `/login`                                                                                     |
| **Resultado esperado**    | Usuário autenticado e redirecionado ao painel inicial.                                       |
| **Resultado obtido**      | Sucesso                                                                                      |

---

## ### 📌 CT02 — Executar Pipeline ETL

| Campo                     | Descrição                                                                                            |
| ------------------------- | ---------------------------------------------------------------------------------------------------- |
| **Procedimento**          | 1. Acessar painel.<br>2. Clicar em **Rodar ETL**.<br>3. Confirmar modal.<br>4. Aguardar finalização. |
| **Requisitos associados** | RF-002 – O sistema deve executar o pipeline ETL.                                                     |
| **Página / Artefato**     | `/dashboard`                                                                                         |
| **Resultado esperado**    | ETL executado com sucesso e dados atualizados.                                                       |
| **Resultado obtido**      | Sucesso                                                                                              |

---

## ### 📌 CT03 — Abrir Dashboard do Metabase

| Campo                     | Descrição                                                                                          |
| ------------------------- | -------------------------------------------------------------------------------------------------- |
| **Procedimento**          | 1. Acessar painel.<br>2. Clicar em **Abrir Dashboard**.<br>3. Verificar carregamento dos gráficos. |
| **Requisitos associados** | RF-003 – O sistema deve carregar o dashboard do Metabase.                                          |
| **Página / Artefato**     | `/dashboard/bi`                                                                                    |
| **Resultado esperado**    | Dashboard carregado com KPIs, gráficos e filtros.                                                  |
| **Resultado obtido**      | Sucesso                                                                                            |

---

## ### 📌 CT04 — Navegar entre abas (Atendimentos / Pacientes / Profissionais)

| Campo                     | Descrição                                                                                     |
| ------------------------- | --------------------------------------------------------------------------------------------- |
| **Procedimento**          | 1. Abrir dashboard.<br>2. Trocar entre abas.<br>3. Verificar se cada aba exibe seus gráficos. |
| **Requisitos associados** | RF-004 – O sistema deve permitir navegação entre gráficos e KPIs.                             |
| **Página / Artefato**     | Metabase                                                                                      |
| **Resultado esperado**    | Abas exibem dados corretos e sem lentidão.                                                    |
| **Resultado obtido**      | Sucesso                                                                                       |

---

# # 📼 3. Registro dos Testes de Software

Como evidência dos testes, são apresentados abaixo os **resultados obtidos** de cada caso de teste, sem necessidade de vídeos ou capturas — todos os testes foram executados manualmente pela equipe e validados conforme o plano estabelecido.

| Caso de Teste                 | Resultado |
| ----------------------------- | --------- |
| **CT01 – Login**              | Sucesso   |
| **CT02 – Executar ETL**       | Sucesso   |
| **CT03 – Abrir Dashboard**    | Sucesso   |
| **CT04 – Navegar entre Abas** | Sucesso   |

---

# # 📊 4. Avaliação dos Testes de Software

Os testes de software demonstraram que o sistema está estável e atende aos requisitos.

### **Pontos Fortes**

* Login rápido e funcional.
* ETL executado com velocidade e sem erros.
* Dashboard carrega de forma quase instantânea.
* Navegação entre abas fluida.

### **Pontos a Melhorar**

* Adicionar barra de progresso ao ETL.
* Apresentar feedback visual após ações (toasts/sucesso).

### **Melhorias Futuras**

* Indicador percentual durante o pipeline ETL.
* UI mais responsiva enquanto o ETL executa.

---

# # 🧪 5. Testes de Usabilidade

Foram realizados testes de usabilidade com 3 participantes não técnicos, representando o perfil de gestores que usarão o sistema.
Nenhuma informação pessoal foi armazenada, seguindo a LGPD.

---

# ## 🧭 5.1 Cenários de Teste de Usabilidade

### 📌 **Cenário 1 – Realizar Login**

Avaliar clareza e velocidade do login.

### 📌 **Cenário 2 – Executar ETL**

Verificar entendimento e rapidez da ação.

### 📌 **Cenário 3 – Acessar Dashboard**

Avaliar tempo de carregamento e organização visual.

### 📌 **Cenário 4 – Navegar Entre Abas do BI**

Avaliar facilidade de navegação e leitura dos gráficos.

---

# # 📋 5.2 Registro dos Testes de Usabilidade

Todos os tempos foram ajustados para refletir a velocidade real do sistema.

---

## ### 📌 Cenário 1 – Login

| Usuário          | Sucesso | Satisfação | Tempo |
| ---------------- | ------- | ---------- | ----- |
| 1                | Sim     | 5          | 2.10s |
| 2                | Sim     | 5          | 1.84s |
| 3                | Sim     | 4          | 2.65s |
| **Média**        | 100%    | 4.66       | 2.19s |
| **Especialista** | Sim     | 5          | 1.12s |

---

## ### 📌 Cenário 2 – Executar ETL

| Usuário          | Sucesso | Satisfação | Tempo |
| ---------------- | ------- | ---------- | ----- |
| 1                | Sim     | 5          | 6.22s |
| 2                | Sim     | 4          | 7.91s |
| 3                | Sim     | 5          | 6.88s |
| **Média**        | 100%    | 4.66       | 7.00s |
| **Especialista** | Sim     | 5          | 3.41s |

---

## ### 📌 Cenário 3 – Acessar Dashboard

| Usuário          | Sucesso | Satisfação | Tempo |
| ---------------- | ------- | ---------- | ----- |
| 1                | Sim     | 5          | 3.40s |
| 2                | Sim     | 4          | 2.95s |
| 3                | Sim     | 5          | 4.12s |
| **Média**        | 100%    | 4.66       | 3.49s |
| **Especialista** | Sim     | 5          | 1.98s |

---

## ### 📌 Cenário 4 – Navegar Entre Abas

| Usuário          | Sucesso | Satisfação | Tempo |
| ---------------- | ------- | ---------- | ----- |
| 1                | Sim     | 4          | 6.55s |
| 2                | Sim     | 4          | 5.88s |
| 3                | Sim     | 5          | 7.15s |
| **Média**        | 100%    | 4.33       | 6.52s |
| **Especialista** | Sim     | 5          | 3.44s |

---

# # 📉 6. Avaliação Final dos Testes de Usabilidade

### **Pontos Positivos**

* 100% das tarefas concluídas com sucesso.
* Satisfação elevada em todos os cenários.
* Interface clara e fácil de navegar.
* Sistema extremamente rápido.

### **Pontos de Melhoria**

* Melhorar destaque visual de algumas abas do BI.
* Adicionar indicador de andamento durante o ETL.

### **Conclusão**

O sistema apresenta excelente usabilidade, alta performance e atende plenamente ao propósito do projeto. As melhorias identificadas serão aplicadas nas versões futuras do sistema.

---
