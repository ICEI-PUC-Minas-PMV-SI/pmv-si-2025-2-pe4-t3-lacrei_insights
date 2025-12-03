# 🎨 **Template Padrão do Site — Guia de Estilo (HTML + CSS)**

O template do sistema **Lacrei Saúde BI** foi desenvolvido com foco em simplicidade, consistência visual, responsividade e acessibilidade.
A identidade visual foi baseada na paleta de cores e estilo da plataforma Lacrei Saúde, adaptada para uma interface administrativa limpa e moderna.

A seguir, são apresentados os elementos fundamentais do guia de estilo utilizado no projeto.

---

# ## 🌐 1. Layout Padrão (HTML + Estrutura Base)

Todas as páginas do sistema seguem um layout padronizado, composto por:

* **Header** com logotipo + nome do sistema
* **Área de conteúdo central**
* **Cards e componentes arredondados**
* **Botões grandes com cor primária verde**
* **Espaçamento amplo e uso de sombras suaves**
* **Design minimalista e flat**

### 📄 **Estrutura HTML base utilizada em todas as páginas**

```html
<body>
  <header class="header">
    <div class="logo-area">
      <img src="/logo.png" alt="Lacrei Saúde" class="logo">
      <span class="title">Lacrei Saúde BI</span>
    </div>
    <nav class="nav-actions">
      <button class="btn-secondary">Github</button>
      <button class="btn-primary-outline">Sair</button>
    </nav>
  </header>

  <main class="content">
    <!-- Conteúdo específico da página -->
  </main>
</body>
```

### ⚙️ CSS Geral do Layout

```css
body {
  background: #eef7f2;
  font-family: 'Inter', sans-serif;
  margin: 0;
  padding: 0;
}

.header {
  display: flex;
  justify-content: space-between;
  padding: 24px;
  background: #ffffff;
  box-shadow: 0 1px 4px rgba(0,0,0,0.08);
}

.logo {
  width: 48px;
  border-radius: 8px;
}

.content {
  padding: 32px;
}
```

---

# ## 🧭 2. Design Geral

O design segue os seguintes princípios:

* **Clean** e minimalista
* **Espaçamento generoso** (padding e margins amplos)
* **Elementos com cantos arredondados** (border-radius 12–20px)
* **Sombras suaves** para destacar cartões
* **Tipografia simples e amigável**
* **Layout responsivo** baseado em Flexbox e Grid
* **Componentes consistentes em todas as telas**

### 🧩 **Elementos fixos nas páginas**

* Logo do sistema posicionado no topo esquerdo
* Botões *Swagger* e *Sair* no topo direito
* Cards para ações principais (Rodar ETL, Ver Dashboard)
* Área central para Metabase / gráficos
* Containers brancos sobre fundo verde-claro

---

# ## 🌈 3. Paleta de Cores

A paleta foi inspirada na identidade da Lacrei Saúde, com leves adaptações para um painel administrativo.

### 🎨 **Cores principais utilizadas**

| Nome             | Hex         | Uso                                 |
| ---------------- | ----------- | ----------------------------------- |
| Verde Primário   | **#0F8B5F** | Botões, destaques                   |
| Verde Água Claro | **#EAF7F2** | Fundo principal do site             |
| Verde Escuro     | **#0A6041** | Hover de botões / títulos           |
| Branco           | **#FFFFFF** | Cards e containers                  |
| Cinza Suave      | **#F4F4F4** | Bordas, divisões, backgrounds leves |
| Preto Suave      | **#1A1A1A** | Texto principal                     |
| Cinza Médio      | **#7A7A7A** | Texto secundário                    |

### Exemplo de CSS aplicado:

```css
:root {
  --primary: #0F8B5F;
  --primary-dark: #0A6041;
  --background: #EAF7F2;
  --text-main: #1A1A1A;
  --text-secondary: #7A7A7A;
  --white: #FFFFFF;
}
```

---

# ## 🔤 4. Tipografia

O sistema utiliza a fonte **Inter**, conhecida por sua boa legibilidade em ambientes digitais.

### **Hierarquia tipográfica**

| Elemento             | Tamanho | Peso | Uso                       |
| -------------------- | ------- | ---- | ------------------------- |
| **Título principal** | 32px    | 700  | Cabeçalho de página       |
| **Título de seção**  | 24px    | 600  | Cards / blocos principais |
| **Subtítulo**        | 18px    | 500  | Nomes de campos / seções  |
| **Texto do corpo**   | 16px    | 400  | Parágrafos, descrições    |
| **Rótulos**          | 14px    | 500  | Labels de inputs, botões  |

### CSS da tipografia

```css
h1 {
  font-size: 32px;
  font-weight: 700;
}

h2 {
  font-size: 24px;
  font-weight: 600;
}

p, span {
  font-size: 16px;
  font-weight: 400;
}

label {
  font-size: 14px;
  font-weight: 500;
}
```

---

# ## 🖼️ 5. Iconografia

A iconografia segue princípios de:

* **Simplicidade**
* **Traços finos**
* **Ícones universais e acessíveis**
* Compatível com bibliotecas como *Lucide Icons* e *HeroIcons*

### Ícones utilizados

| Ícone        | Função                         | Exemplo           |
| ------------ | ------------------------------ | ----------------- |
| 🔄 Refresh   | Botão de rodar ETL             | `Rodar ETL`       |
| 📊 Dashboard | Acessar Metabase               | `Abrir Dashboard` |
| 🔑 Login     | Campos de autenticação         | Tela de login     |
| 🚪 Logout    | Sair do sistema                | Botão “Sair”      |
| ⚙️ Config    | Swagger / Documentação técnica | Botão Swagger     |

CSS aplicado aos ícones:

```css
.icon {
  width: 20px;
  height: 20px;
  margin-right: 8px;
}
```

---

# ## 📦 6. Componentes Principais (CSS)

Aqui estão alguns dos componentes centrais utilizados no sistema.

---

## ### 🔘 Botões

```css
.btn-primary {
  background: var(--primary);
  padding: 12px 24px;
  color: white;
  border-radius: 12px;
  border: none;
  font-weight: 600;
}

.btn-primary:hover {
  background: var(--primary-dark);
}

.btn-secondary {
  background: white;
  color: var(--primary);
  border: 2px solid var(--primary);
  padding: 10px 20px;
  border-radius: 12px;
}
```

---

## ### 🧊 Cards

```css
.card {
  background: white;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 4px 10px rgba(0,0,0,0.05);
}
```

---

## ### 📁 Containers e Seções

```css
.section {
  margin-bottom: 32px;
}

.container {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}
```

---

# ## 📱 7. Responsividade

O layout foi projetado com foco em responsividade utilizando **Flexbox** e **Grid**, permitindo que:

* Cards se reorganizem automaticamente
* Inputs e botões se ajustem a telas menores
* Navegação continue simples em tablets e notebooks

### CSS de exemplo:

```css
@media (max-width: 768px) {
  .content {
    padding: 16px;
  }

  .card {
    padding: 24px;
  }

  h1 {
    font-size: 24px;
  }
}
```

---
