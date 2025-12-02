# 📋 Especificações do Projeto - Lacrei Insights

## 👥 Personas

### Daniel Dutra (Product Owner)
**Idade:** 32 anos  
**Profissão:** Gestor da Lacrei Saúde  
**Perfil:** Profissional dedicado à causa LGBTQIAPN+, trabalha remotamente e coordena voluntários de tecnologia e negócios. Nos momentos livres, gosta de participar de eventos sobre diversidade e inclusão.

**Motivações:**
- Expandir o alcance da plataforma para todo o Brasil
- Garantir a qualidade dos profissionais cadastrados
- Melhorar a experiência dos usuários LGBTQIAPN+
- Tomar decisões baseadas em dados concretos

**Frustrações:**
- Falta de visibilidade sobre métricas de desempenho da plataforma
- Dificuldade em demonstrar impacto social para parceiros e financiadores
- Ausência de dados consolidados para identificar gargalos operacionais

**Necessidades:**
- Dashboards que mostrem indicadores-chave em tempo real
- Relatórios sobre distribuição de profissionais por região
- Métricas de satisfação e retenção de usuários
- Análises sobre taxa de conversão e engajamento

---

### Ana Paula Silva
**Idade:** 28 anos  
**Profissão:** Voluntária de TI na Lacrei Saúde  
**Perfil:** Desenvolvedora backend com experiência em Python e bancos de dados. Trabalha remotamente e dedica algumas horas por semana ao projeto. Apaixonada por tecnologia para o bem social.

**Motivações:**
- Contribuir com uma causa que acredita
- Aplicar suas habilidades técnicas em projetos de impacto
- Aprender sobre Business Intelligence e análise de dados

**Frustrações:**
- Dificuldade em acessar dados históricos da plataforma
- Falta de padronização nos dados operacionais
- Processos manuais de extração e análise de informações

**Necessidades:**
- Pipeline ETL automatizado e documentado
- Estrutura de dados organizada (Data Warehouse)
- Processos claros de atualização de dados

---

### Dr. Carlos Mendes
**Idade:** 45 anos  
**Profissão:** Psicólogo cadastrado na plataforma Lacrei Saúde  
**Perfil:** Profissional com especialização em questões LGBTQIAPN+, atende presencialmente e online. Busca constantemente melhorar seu atendimento e alcançar pacientes que precisam de acolhimento especializado.

**Motivações:**
- Oferecer atendimento de qualidade para pessoas LGBTQIAPN+
- Aumentar sua visibilidade na plataforma
- Receber feedback construtivo dos pacientes

**Frustrações:**
- Não sabe como melhorar sua avaliação na plataforma
- Falta de transparência sobre sua performance comparada a outros profissionais
- Desconhece a demanda real por sua especialidade

**Necessidades:**
- Visibilidade sobre suas métricas de atendimento
- Comparação de performance por especialidade e região
- Feedback consolidado dos pacientes

---

### Lucas Oliveira
**Idade:** 24 anos  
**Perfil:** Homem trans, universitário, mora em São Paulo  
**Situação:** Busca psicólogo que compreenda questões relacionadas à transição de gênero e respeite seu nome social

**Motivações:**
- Encontrar profissionais capacitados e inclusivos
- Ter um atendimento seguro e sem discriminação
- Acessar informações claras sobre profissionais disponíveis

**Frustrações:**
- Experiências anteriores de discriminação em serviços de saúde
- Dificuldade em encontrar profissionais especializados
- Receio de não ser respeitado durante o atendimento

**Necessidades:**
- Plataforma confiável com profissionais validados
- Transparência sobre especialidades e experiência dos profissionais
- Processo de agendamento simples e rápido

---

## 📖 Histórias de Usuários

Com base na análise das personas foram identificadas as seguintes histórias de usuários:

| EU COMO... | QUERO/PRECISO... | PARA... |
|------------|------------------|---------|
| **Gestor da Lacrei Saúde** | Visualizar métricas consolidadas de atendimentos, cadastros e cancelamentos | Monitorar o desempenho da plataforma e tomar decisões estratégicas baseadas em dados |
| **Gestor da Lacrei Saúde** | Gerar relatórios sobre distribuição geográfica de profissionais | Identificar lacunas de cobertura e planejar expansão regional |
| **Gestor da Lacrei Saúde** | Acompanhar a evolução de cadastros de usuários e profissionais ao longo do tempo | Avaliar o crescimento da plataforma e efetividade de campanhas |
| **Gestor da Lacrei Saúde** | Analisar a taxa de conversão de buscas em consultas efetivadas | Identificar pontos de atrito na jornada do usuário |
| **Voluntário de TI** | Executar o processo ETL de forma automatizada | Garantir que os dados estejam sempre atualizados sem processos manuais |
| **Voluntário de TI** | Acessar dados estruturados em um Data Warehouse | Facilitar análises e manutenção do sistema de BI |
| **Profissional de Saúde** | Visualizar minhas métricas de desempenho (número de atendimentos, avaliações) | Entender minha performance e identificar pontos de melhoria |
| **Profissional de Saúde** | Comparar minhas avaliações com a média da plataforma | Ter referências para melhorar meu atendimento |
| **Usuário LGBTQIAPN+** | Ter acesso a uma plataforma que demonstre compromisso com inclusão através de dados transparentes | Confiar que a organização realmente trabalha para melhorar o acesso à saúde inclusiva |
| **Parceiro/Financiador** | Visualizar relatórios de impacto social da plataforma | Avaliar a efetividade do projeto e justificar apoio continuado |

---

## 📊 Requisitos

As tabelas a seguir apresentam os requisitos funcionais e não funcionais que detalham o escopo do projeto Lacrei Insights.

### Requisitos Funcionais

| Código | Descrição do Requisito | Prioridade |
|--------|------------------------|------------|
| RF-01 | A aplicação deve extrair dados da plataforma Lacrei Saúde (pacientes, profissionais, atendimentos e feedbacks) | ALTA |
| RF-02 | A aplicação deve executar processo de ETL em Python com padronização, limpeza e anonimização de dados sensíveis em conformidade com a LGPD | ALTA |
| RF-03 | A aplicação deve armazenar os dados tratados em um Data Warehouse centralizado com modelagem dimensional | ALTA |
| RF-04 | A aplicação deve disponibilizar dashboards interativos no Metabase, acessíveis via portal web | ALTA |
| RF-05 | A aplicação deve oferecer visualizações de KPIs: total de cadastros, atendimentos realizados, feedbacks e distribuições demográficas | ALTA |
| RF-06 | A aplicação deve permitir atualização periódica dos dados (disparo manual via portal) | MÉDIA |
| RF-07 | A aplicação deve gerar relatórios exportáveis (PDF/Excel) para gestores | MÉDIA |
| RF-08 | A aplicação deve disponibilizar indicadores comparativos: evolução de cadastros mês a mês, crescimento de atendimentos por especialidade | BAIXA |
| RF-09 | A aplicação deve implementar Data Marts temáticos para: Pacientes, Profissionais e Atendimentos | ALTA |
| RF-10 | A aplicação deve disponibilizar portal web com autenticação (login) para acesso aos recursos analíticos | ALTA |
| RF-11 | A aplicação deve oferecer ação "Atualizar dados" para disparo manual do pipeline ETL diretamente no portal | ALTA |
| RF-12 | A aplicação deve oferecer ação "Ver gráficos" que navega para a página de dashboards alimentada pela camada mart | ALTA |
| RF-13 | A aplicação deve consolidar dados de múltiplas tabelas fonte em uma estrutura Star Schema otimizada para análises | ALTA |
| RF-14 | A aplicação deve calcular automaticamente métricas agregadas: tempo médio de espera, taxa de cancelamento, taxa de crescimento | MÉDIA |

---

### Requisitos Não Funcionais

| Código | Descrição do Requisito | Prioridade |
|--------|------------------------|------------|
| RNF-01 | A aplicação deve garantir anonimização e proteção de dados sensíveis em conformidade com a LGPD | ALTA |
| RNF-02 | As visualizações devem ser compatíveis com navegadores modernos (Chrome, Firefox, Safari, Edge) e com o Metabase | ALTA |
| RNF-03 | Consultas usuais ao Data Warehouse devem ter tempo de resposta inferior a 5 segundos | ALTA |
| RNF-04 | O portal web deve ser responsivo, acessível em desktop e dispositivos móveis | ALTA |
| RNF-05 | O processo de ETL deve ser automatizado e possuir documentação técnica completa de manutenção | ALTA |
| RNF-06 | Deve haver autenticação JWT e controle de acesso para usuários internos autorizados | MÉDIA |
| RNF-07 | O sistema deve suportar crescimento de volume de dados em escala sem perda de desempenho | MÉDIA |
| RNF-08 | O design das visualizações deve seguir padrões de acessibilidade digital (WCAG 2.1), com contraste adequado e alternativas textuais | ALTA |
| RNF-09 | O código-fonte deve seguir padrões de desenvolvimento (PEP 8 para Python, ESLint para JavaScript) | MÉDIA |
| RNF-10 | O sistema deve ser implantado em ambiente de produção com alta disponibilidade (AWS) | ALTA |
| RNF-11 | O processo ETL deve registrar logs de execução para auditoria e troubleshooting | MÉDIA |
| RNF-12 | A aplicação deve implementar tratamento de erros robusto com mensagens claras para o usuário | MÉDIA |

---

## 🚧 Restrições

O projeto está restrito pelos itens apresentados na tabela a seguir:

| ID | Restrição |
|----|-----------|
| 01 | O projeto deve ser entregue até o final do semestre letivo (dezembro/2025) |
| 02 | O projeto deve utilizar exclusivamente dados fornecidos pela Lacrei Saúde, sem integração com sistemas externos além do banco de dados da organização |
| 03 | O sistema deve operar apenas com os dados de profissionais validados pela Lacrei Saúde |
| 04 | O projeto deve respeitar rigorosamente a LGPD, especialmente no tratamento de dados sensíveis (identidade de gênero, orientação sexual, etnia, deficiências) |
| 05 | A solução deve ser desenvolvida com tecnologias open-source ou com licenças compatíveis com projetos sem fins lucrativos |
| 06 | O projeto depende da disponibilidade de voluntários para desenvolvimento e manutenção |
| 07 | A infraestrutura de hospedagem está limitada aos recursos disponíveis na AWS dentro do orçamento da organização |
| 08 | Os dashboards devem ser acessíveis apenas para gestores e voluntários autorizados pela Lacrei Saúde |
| 09 | O escopo regional está inicialmente limitado ao estado de São Paulo, onde a Lacrei Saúde atua |
| 10 | O sistema deve funcionar de forma estável mesmo com interrupções ocasionais no desenvolvimento devido à natureza voluntária do trabalho |

---

## 🔗 Links Úteis

- [O que são Requisitos Funcionais e Requisitos Não Funcionais?](https://codificar.com.br/requisitos-funcionais-nao-funcionais/)
- [Histórias de Usuários: como escrever de forma eficaz](https://www.atlassian.com/br/agile/project-management/user-stories)
- [Star Schema - Modelagem Dimensional](https://www.kimballgroup.com/data-warehouse-business-intelligence-resources/kimball-techniques/dimensional-modeling-techniques/)

