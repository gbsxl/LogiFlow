# 📦 LogiFlow - Sistema de Gerenciamento de Tarefas Logísticas

## 📖 Sobre o Projeto

**Contexto**: A TechFlow Solutions foi contratada por uma startup de logística para desenvolver um sistema de gerenciamento que permita acompanhar o fluxo de trabalho em tempo real, priorizar tarefas críticas e monitorar o desempenho da equipe.

O **LogiFlow** é a solução desenvolvida: um sistema web robusto para controle de operações logísticas, permitindo gestão completa de tarefas, produtos em estoque e movimentações da equipe.

### 🎯 Objetivo

Criar uma plataforma integrada que facilite:
- Acompanhamento de fluxo de trabalho em tempo real
- Priorização de tarefas críticas
- Monitoramento de desempenho da equipe
- Controle de estoque e produtos
- Rastreamento de movimentações

### 🔧 Escopo Inicial

**Funcionalidades Principais:**
- ✅ Sistema de autenticação (login/logout)
- ✅ Gerenciamento de produtos (CRUD completo)
- ✅ Controle de estoque (entradas e saídas)
- ✅ Sistema de usuários com permissões (admin e comum)
- ✅ Histórico de movimentações
- ✅ Relatórios e dashboards
- ✅ Alertas de estoque baixo

---

## 🏃 Metodologia Ágil - Kanban

Este projeto utiliza **Kanban** para gestão das tarefas de desenvolvimento.

**Por que Kanban?**
- Visualização clara do fluxo de trabalho
- Flexibilidade para mudanças de prioridade
- Identificação rápida de gargalos
- Fluxo contínuo de entregas

**Organização do Quadro:**
- **To Do**: Tarefas planejadas e priorizadas
- **In Progress**: Tarefas em desenvolvimento (limite: 3 tarefas simultâneas)
- **Done**: Tarefas concluídas e testadas

O quadro Kanban está disponível na aba [Projects](../../projects) do GitHub.

---

## 🛠️ Tecnologias Utilizadas

| Categoria | Tecnologia |
|-----------|-----------|
| **Linguagem** | Python 3.10+ |
| **Framework Web** | Flask 3.0 |
| **ORM** | SQLAlchemy 2.0 |
| **Banco de Dados** | SQLite |
| **Autenticação** | Passlib (bcrypt) |
| **Testes** | Pytest |
| **CI/CD** | GitHub Actions |
| **Controle de Versão** | Git/GitHub |

---

## 📦 Estrutura do Projeto

```
LogiFlow/
│
├── src/
│   ├── __init__.py
│   └── app.py              # Aplicação principal Flask
│
├── tests/
│   ├── __init__.py
│   ├── test_app.py         # Testes da aplicação
│   └── test_models.py      # Testes dos modelos
│
├── docs/
│   ├── diagrama_casos_uso.mermaid
│   └── diagrama_classes.mermaid
│
├── .github/
│   └── workflows/
│       └── ci.yml          # Pipeline CI/CD
│
├── requirements.txt        # Dependências Python
├── README.md              # Este arquivo
├── .gitignore             # Arquivos ignorados pelo Git
└── estoque.db             # Banco de dados SQLite (gerado automaticamente)
```

---

## 🚀 Como Executar o Projeto

### Pré-requisitos

- Python 3.10 ou superior
- pip (gerenciador de pacotes Python)
- Git

### Instalação e Execução

```bash
# 1. Clone o repositório
git clone https://github.com/gbsxl/LogiFlow.git
cd LogiFlow

# 2. Crie um ambiente virtual
python -m venv venv

# 3. Ative o ambiente virtual
# Windows:
venv\\Scripts\\activate
# Linux/Mac:
source venv/bin/activate

# 4. Instale as dependências
pip install -r requirements.txt

# 5. Execute a aplicação
python src/app.py
```

### Acessar o Sistema

- **URL**: http://localhost:1531
- **Usuário padrão**: admin@sistema.com
- **Senha padrão**: admin123

---

## 🧪 Executar Testes

```bash
# Rodar todos os testes
pytest

# Rodar com relatório de cobertura
pytest --cov=src tests/ --cov-report=html

# Rodar testes específicos
pytest tests/test_app.py -v
```

---

## 📊 Pipeline de CI/CD

O projeto utiliza **GitHub Actions** para automação:

**Workflow Configurado:**
- ✅ Execução automática a cada push/pull request
- ✅ Instalação de dependências
- ✅ Execução de todos os testes
- ✅ Relatório de cobertura de código
- ✅ Validação de qualidade

Veja o arquivo `.github/workflows/ci.yml` para detalhes.

---

## 🔄 Mudança de Escopo - Sistema de Notificações

### **Alteração Implementada**

Durante o desenvolvimento, o cliente solicitou a adição de um **sistema de notificações por e-mail** para alertar a equipe sobre:
- Produtos com estoque crítico (abaixo do mínimo)
- Movimentações importantes
- Alertas de segurança

### **Justificativa da Mudança**

A startup de logística identificou que muitos produtos ficavam sem estoque sem que a equipe responsável fosse notificada rapidamente, causando atrasos nas operações. A implementação de notificações automáticas resolve este gargalo operacional.

### **Impacto no Projeto**

**Cards adicionados no Kanban:**
- Configurar servidor SMTP
- Criar função de envio de e-mails
- Implementar verificação automática de estoque baixo
- Adicionar testes para notificações

**Mudanças técnicas:**
- Nova função `enviar_notificacao_estoque_baixo()`
- Configuração de variáveis de ambiente para SMTP
- Job agendado para verificação diária
- Testes unitários para validação

Esta mudança foi gerenciada de forma ágil, com priorização imediata e implementação incremental seguindo os princípios do Kanban.

---

## 🎓 Contexto Acadêmico

Este projeto foi desenvolvido para a disciplina de **Engenharia de Software**, aplicando na prática:

- ✅ **Metodologias Ágeis**: Kanban para gestão de tarefas
- ✅ **Modelagem UML**: Diagramas de Casos de Uso e Classes
- ✅ **Controle de Qualidade**: Testes automatizados com Pytest
- ✅ **Integração Contínua**: GitHub Actions
- ✅ **Versionamento**: Git com commits semânticos
- ✅ **Gestão de Mudanças**: Adaptação ágil a novos requisitos
- ✅ **Documentação**: README completo e código comentado

---

## 👥 Equipe

- **Desenvolvedor**: Gabriel
- **GitHub**: [@gbsxl](https://github.com/gbsxl)
- **Instituição**: Unifecaf
- **Disciplina**: Engenharia de Software

---

## 📝 Licença

Este projeto foi desenvolvido para fins acadêmicos.

---

## 📞 Suporte

Para dúvidas ou sugestões:
- Abra uma [Issue](../../issues)
- Entre em contato via GitHub

---

## 📚 Referências

1. PRESSMAN, Roger. **Engenharia de Software: Uma Abordagem Profissional**
2. GitHub Actions Documentation: https://docs.github.com/actions
3. Atlassian - Kanban Guide: https://www.atlassian.com/agile/kanban
4. Flask Documentation: https://flask.palletsprojects.com/

---

**Última atualização**: Janeiro 2026

---

## 🎯 Status do Projeto

![Tests](https://github.com/gbsxl/LogiFlow/workflows/CI/badge.svg)
![Python Version](https://img.shields.io/badge/python-3.10+-blue.svg)
![License](https://img.shields.io/badge/license-Academic-green.svg)

**Status**: ✅ Em produção acadêmica
