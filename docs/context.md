# 📊 Projeto de Business Intelligence – Lacrei Saúde

## 📌 Introdução  

O presente projeto tem como objetivo desenvolver uma solução de **Business Intelligence** para a plataforma **Lacrei Saúde**, que atua na conexão de pessoas LGBTQIAPN+ a profissionais de saúde inclusivos.  

A proposta contempla a construção de um **Data Warehouse (DW)**, de um **Data Mart temático** e de **dashboards interativos** no Power BI, com vistas à transformação de dados operacionais em análises estratégicas que qualifiquem a gestão, ampliem a transparência e subsidiem a formulação de políticas públicas e institucionais.  

A iniciativa justifica-se pela necessidade de sistematizar e analisar informações referentes ao acesso, ao engajamento e à qualidade do atendimento destinado à população LGBTQIAPN+, a qual historicamente enfrenta barreiras no sistema de saúde.  

Estudos apontam que parte significativa dessa população evita procurar serviços de saúde por receio de práticas discriminatórias, resultando em afastamento e menor adesão a cuidados preventivos. Soma-se a esse cenário a insuficiente capacitação dos profissionais de saúde em lidar com demandas específicas, como o processo de transição de pessoas transgênero e o reconhecimento do nome social. Além disso, persiste a concentração das ações em torno de pautas relacionadas ao HIV/AIDS e a outras infecções sexualmente transmissíveis, o que contribui para a estigmatização e a limitação do conhecimento acerca da diversidade de necessidades dessa população.  

Por meio da solução proposta, será possível:  
- Mensurar a distribuição de profissionais por região e especialidade;  
- Identificar lacunas de acesso;  
- Avaliar a experiência do usuário;  
- Monitorar indicadores de retenção;  
- Analisar a efetividade de campanhas de engajamento.  

A relevância deste projeto manifesta-se em duas dimensões complementares:  
- **Acadêmica**: ao disponibilizar uma base de dados estruturada que viabilize pesquisas científicas sobre saúde inclusiva e equidade social;  
- **Social**: ao contribuir para a consolidação de práticas de cuidado em saúde orientadas pelos princípios de inclusão, representatividade e segurança, assegurando às pessoas LGBTQIAPN+ o direito a um atendimento digno e respeitoso.  

**Principais ações previstas:**  
1. Levantamento e integração de dados oriundos da plataforma;  
2. Construção do **Data Warehouse** e do **Data Mart**;  
3. Desenvolvimento de indicadores e dashboards no Power BI;  
4. Capacitação de usuários para o uso das ferramentas desenvolvidas;  
5. Avaliação sistemática dos resultados para subsidiar políticas públicas e o aprimoramento de práticas institucionais.  

---

## 🔍 Diagnóstico da Situação-Problema  

Diversos estudos nacionais e internacionais evidenciam que pessoas LGBTQIAPN+ enfrentam desigualdades persistentes no acesso aos serviços de saúde, decorrentes tanto de práticas discriminatórias quanto da insuficiente capacitação dos profissionais para lidar com demandas específicas dessa população.  

Pesquisas realizadas por instituições de referência, como a **Fiocruz (2019)** e a **UNAIDS (2021)**, indicam que mais de **60% das pessoas trans** relataram experiências de discriminação em contextos de atendimento em saúde, o que contribui para o afastamento dessa população dos serviços formais de cuidado.  

Além disso, observa-se a carência de profissionais inclusivos em diversas regiões do Brasil, o que reforça desigualdades territoriais no acesso a práticas de saúde dignas e seguras. Esse cenário é agravado pela predominância de ações historicamente voltadas ao enfrentamento do **HIV/AIDS** e de outras **ISTs**. Embora fundamentais, tais iniciativas acabam restringindo a compreensão das necessidades da população LGBTQIAPN+, invisibilizando outras dimensões, como:  
- Saúde mental;  
- Cuidados hormonais;  
- Processo transexualizador;  
- Reconhecimento do nome social;  
- Garantia de ambientes de acolhimento.  

A **Lacrei Saúde** emerge, nesse contexto, como uma iniciativa que busca atuar como ponte entre usuários LGBTQIAPN+ e profissionais de saúde comprometidos com práticas inclusivas, promovendo representatividade, acolhimento e equidade.  

No entanto, a organização ainda não dispõe de uma estrutura analítica suficientemente robusta para mensurar de forma integrada e contínua os resultados de suas ações. Em especial, carece de instrumentos que permitam monitorar:  

- **A jornada digital dos usuários** e a taxa de conversão em consultas, possibilitando compreender pontos de maior atrito ou abandono;  
- **A cobertura de profissionais por localidade**, identificando desigualdades regionais no acesso;  
- **Os níveis de satisfação e retenção de usuários**, fundamentais para avaliar a qualidade percebida;  
- **Os resultados de campanhas de engajamento e parcerias institucionais**, mensurando sua efetividade e alcance.  

A ausência de indicadores consolidados e integrados limita a capacidade da Lacrei Saúde de avaliar com precisão o **impacto social** de sua atuação, dificultando tanto a identificação de lacunas estratégicas quanto a comunicação transparente de seus resultados a parceiros, financiadores e sociedade civil.  

Diante disso, torna-se imperativo o desenvolvimento de uma solução de **Business Intelligence** capaz de estruturar, organizar e analisar dados operacionais, oferecendo subsídios concretos para a tomada de decisão, a qualificação da gestão e a consolidação da plataforma como referência em saúde inclusiva.  

---

## 🎯 Objetivo Geral  

Desenvolver uma solução de **Business Intelligence** que integre e sistematize os dados da plataforma **Lacrei Saúde** em um **Data Warehouse** e em um **Data Mart temático**, viabilizando a criação de **painéis interativos no Power BI**.  

Tal solução buscará monitorar, de forma contínua e estruturada, o **acesso**, o **engajamento** e a **qualidade dos serviços** ofertados à comunidade **LGBTQIAPN+**, subsidiando a **gestão estratégica**, a **avaliação de impacto social** e a **formulação de políticas públicas inclusivas**.  

---

## 🎯 Objetivos Específicos  

- **Realizar o levantamento, mapeamento e padronização das fontes de dados operacionais da plataforma**, assegurando a integridade, a consistência e a confiabilidade das informações a serem analisadas;  

- **Projetar e estruturar o Data Warehouse e o Data Mart temático**, organizando os dados em conformidade com as boas práticas de modelagem multidimensional, de modo a possibilitar análises históricas e comparativas;  

- **Definir e operacionalizar indicadores-chave de desempenho (KPIs)** relacionados ao acesso, à cobertura de profissionais, ao engajamento de usuários e à qualidade do atendimento, com base em critérios validados por literatura científica e pelas necessidades institucionais da Lacrei Saúde;  

- **Desenvolver dashboards e relatórios analíticos no Power BI**, direcionados a diferentes públicos-alvo — gestores, pesquisadores e parceiros institucionais — promovendo transparência, tomada de decisão orientada por dados e disseminação de informações qualificadas;  

- **Capacitar as equipes envolvidas no uso das ferramentas analíticas**, por meio de treinamentos e materiais de apoio, visando à apropriação das tecnologias e ao fortalecimento da cultura organizacional orientada por dados;  

- **Estabelecer um processo de monitoramento e avaliação periódica dos resultados obtidos**, a fim de identificar boas práticas, apontar lacunas e propor melhorias contínuas tanto nos aspectos técnicos da solução quanto na efetividade das ações de saúde inclusiva;  

- **Favorecer a produção acadêmica e científica**, ao disponibilizar uma base estruturada de dados que subsidie pesquisas relacionadas à saúde da população LGBTQIAPN+, à equidade em saúde e à formulação de políticas públicas de inclusão.  

---

## 📖 Justificativa  

A presente proposta fundamenta-se em sua dupla relevância: **social** e **acadêmica**.  
O projeto contribui para a promoção da **equidade em saúde da população LGBTQIAPN+**, historicamente marcada por situações de exclusão, discriminação e estigmatização nos serviços de saúde.  

Ao estruturar e analisar dados relacionados ao acesso, à qualidade e ao engajamento em práticas de cuidado inclusivas, a iniciativa possibilitará a produção de evidências que orientem a melhoria das condições de acesso e o fortalecimento de **políticas públicas** que assegurem o direito universal à saúde, em consonância com os princípios do **Sistema Único de Saúde (SUS)** e com a perspectiva de **direitos humanos**.  

Sob a ótica acadêmica, o projeto oferece uma **base de dados estruturada** que poderá subsidiar pesquisas interdisciplinares em áreas como:  

- **Saúde pública**  
- **Ciência de dados**  
- **Sociologia**  
- **Direitos humanos**  
- **Políticas públicas**  

Além disso, dialoga diretamente com a **Política de Extensão Universitária da PUC Minas (2006)**, ao articular ensino, pesquisa e extensão em torno de um problema social concreto, e com o **Plano de Desenvolvimento Institucional (2012)**, ao fomentar ações voltadas para a cidadania, a justiça social e a inclusão de populações historicamente marginalizadas.  

---

## 🎓 Integração com Ensino, Pesquisa e Extensão  

A proposta integra-se às atividades de ensino e pesquisa em diferentes dimensões:  

1. **A experiência extensionista como objeto de problematização**  
   - A atuação junto à Lacrei Saúde permitirá evidenciar lacunas no acesso e na qualidade dos serviços de saúde voltados à população LGBTQIAPN+, transformando a prática em fonte de reflexão crítica e de produção de conhecimento.  

2. **Subsídio metodológico para a construção do Data Warehouse**  
   - O diagnóstico quantitativo e qualitativo dos dados disponíveis possibilitará a definição de critérios de integração, padronização e análise, garantindo rigor científico ao processo de modelagem da solução de Business Intelligence.  

3. **Produção de conhecimento acessível à sociedade**  
   - Os resultados obtidos serão sistematizados em relatórios técnicos, indicadores e painéis públicos, ampliando a transparência institucional e fortalecendo a *accountability* perante parceiros, órgãos de fomento e a sociedade civil.  

4. **Estímulo à pesquisa futura e à interdisciplinaridade**  
   - A disponibilização de uma base estruturada e confiável de dados favorecerá a realização de investigações posteriores em áreas diversas, incluindo estudos de avaliação de impacto social, análises de equidade em saúde, desenvolvimento de metodologias analíticas aplicadas à ciência de dados e pesquisas sobre políticas inclusivas de direitos humanos.  

5. **Fortalecimento da formação discente e docente**  
   - Ao articular ensino, pesquisa e extensão, o projeto proporciona um espaço privilegiado de aprendizagem, no qual estudantes e professores poderão aplicar conhecimentos teóricos em contextos práticos, contribuindo para sua formação crítica, ética e cidadã.  

---

## 👥 Público-Alvo

- **Pessoas LGBTQIAPN+ em todo o território nacional**, que buscam atendimento em saúde inclusivo, seguro e livre de discriminação, representando o núcleo prioritário da intervenção.  
- **Profissionais de saúde cadastrados na plataforma Lacrei Saúde**, que atuam em distintas especialidades médicas e áreas correlatas, validados quanto à adesão a práticas inclusivas e respeitosas.  
- **Gestores institucionais e organizações parceiras**, especialmente aquelas que atuam em políticas públicas de saúde, diversidade e direitos humanos, interessadas em dados e indicadores para subsidiar estratégias e tomadas de decisão.  

---

### 1️⃣ Critérios de Inclusão do Público-Alvo  

- **Usuários da plataforma Lacrei Saúde** que realizam buscas ou consultas por atendimento inclusivo;  
- **Profissionais de saúde validados** pela plataforma quanto ao compromisso ético e técnico com a população LGBTQIAPN+;  
- **Gestores, pesquisadores e parceiros institucionais** com interesse em utilizar os dados produzidos pelo projeto como subsídio para ações de planejamento, monitoramento e avaliação em saúde inclusiva.  

---

### 2️⃣ Estimativa de Beneficiários Diretos  

Considerando a base atual de usuários e projeções de crescimento anual, estima-se o atendimento direto a aproximadamente:  

- **800 usuários da plataforma** que buscam serviços de saúde inclusivos;  
- **90 profissionais de saúde validados** pela Lacrei Saúde, distribuídos em diferentes especialidades e regiões do Brasil.  

---

### 3️⃣ Estimativa de Beneficiários Indiretos  

De forma indireta, o projeto deverá impactar cerca de **1.000 pessoas**, entre as quais:  

- **Familiares e redes de apoio** dos usuários que acessam a plataforma;  
- **Organizações sociais** que atuam na defesa dos direitos da população LGBTQIAPN+ e na promoção da equidade em saúde;  
- **Comunidade acadêmica e científica**, que poderá utilizar os dados estruturados e analisados como insumo para pesquisas e para a formulação de políticas públicas.  

