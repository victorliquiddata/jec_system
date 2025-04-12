**Integration Test Setup - Module Sharing Template**

**Architecture Overview**:
[Sistema JEC é uma aplicação CLI em Python para gerenciar casos de juizados especiais cíveis, com foco em até 15 usuários simultâneos e funcionalidades como autenticação, gerenciamento de usuários, documentos e processos. O projeto está sendo desenvolvido com o framework Rich para interface de linha de comando e PostgreSQL como banco de dados.

Versões:
v0.0: Proposta inicial (fev/2025)

v0.1: Autenticação implementada (abr/2025)

v0.2-v0.6: Melhorias na conexão com o banco de dados, UI e logging

v0.7+: Testes de integração e melhorias na UI/UX

Funcionalidades Principais:
Login e autenticação com segurança (PBKDF2-HMAC-SHA256)

Gestão de usuários, processos, documentos

Rastreamento de processos com status e prazos

Componentes Técnicos:
Banco de Dados: PostgreSQL com pool de conexões

Autenticação: Algoritmo de hash PBKDF2-HMAC-SHA256

Testes: Desenvolvido com pytest, cobrindo módulos críticos

Interface: Menus dinâmicos e componentes como barras de progresso e seletores de tema

Banco de Dados:
Tabelas incluem usuários, processos, documentos, auditoria, partes e categorias, com relacionamentos de chaves estrangeiras.

Prioridades:
Foco atual: Gerenciamento de documentos

Prazo: 7 dias para finalização do módulo de documentos

Módulos e Arquivos:
Arquivos principais incluem main.py, auth.py, database.py, rich_cli.py, e logger.py

Testes: Cobertura de testes para a maioria dos módulos essenciais.]

---

**Current Sharing Progress**:  
`[X/7]` modules shared  
`[X]` auth.py  
`[X]` config.py  
`[X]` database.py  
`[X]` logger.py  
`[X]` main.py  
`[X]` rich_cli.py  
`[X]` logging_context.py  

---

**Next Module to Share**:
```python
# File: [filename.py]
[Paste complete file content here]

# TEST NOTES:
[Any specific integration points or test considerations for this file]
```

---

**Previous Modules Summary**:  
[I'll automatically maintain this section with each submission]

---

**How to Use This Template**:
1. Fill in the Architecture Overview first (if not already shared)
2. For each file:
   - Update the `[X/7]` counter
   - Check the box for the file you're sharing
   - Paste the complete code
   - Add any test-specific notes
3. I'll acknowledge each file and maintain full context













--

### **8-Hour Focus Plan: Integration Testing for JEC System**  
**Objective**: Rigorously test all 7 modules (`auth.py`, `config.py`, `database.py`, `logger.py`, `main.py`, `rich_cli.py`, `logging_context.py`) with unit, integration, CLI, and RBAC tests.  

#### **Hour 0-1: Setup & Architecture Review**  
1. **Share Modules** (30 mins):  
   - Use the structured template to share all 7 files (I’ll confirm context after each).  
   - Highlight key integration points (e.g., `auth.py` → `database.py`, `logger.py` → all modules).  
2. **Test Environment Setup** (30 mins):  
   - Configure `pytest` + `pytest-postgresql` or `testcontainers`.  
   - Create mock fixtures for `database.py` and `logger.py`.  

#### **Hour 1-3: Unit Testing (Priority Modules)**  
1. **`auth.py`** (45 mins):  
   - Test password hashing/verification (`test_hash_password`, `test_verify_password`).  
   - RBAC function tests (`test_admin_access`, `test_visitor_denied`).  
2. **`database.py`** (45 mins):  
   - CRUD operations with mocked PostgreSQL (`test_create_user`, `test_fetch_process`).  
   - Connection robustness (`test_database_retry_on_failure`).  
3. **`logger.py`** (30 mins):  
   - Verify log actions (`test_log_action_called`).  

#### **Hour 3-5: Integration Testing**  
1. **Auth + Database** (45 mins):  
   - Test login flow with real DB calls (`test_login_integration`).  
   ```python
   def test_login_integration(db_connection):
       # Insert test user
       cursor = db_connection.cursor()
       cursor.execute("INSERT INTO usuarios (email, senha) VALUES ('test@jec.com', 'hash123')")
       # Verify auth
       assert auth.verify_login('test@jec.com', 'hash123') is True
   ```  
2. **CLI + Auth** (45 mins):  
   - Use `CliRunner` to simulate login/logout (`test_cli_login_success`).  
3. **Logger + All Modules** (30 mins):  
   - Verify logs for user actions across modules (`test_log_on_process_create`).  

#### **Hour 5-6: RBAC & Security Testing**  
1. **Role-Based Access** (45 mins):  
   - Test `rich_cli.py` menu restrictions per role (`test_judge_can_access_sensitive_menu`).  
2. **Edge Cases** (15 mins):  
   - Invalid inputs, SQL injection attempts (`test_sanitize_input`).  

#### **Hour 6-7: CI & Robustness Checks**  
1. **CI Pipeline Setup** (30 mins):  
   - Draft GitHub Actions workflow to run tests in Docker with PostgreSQL.  
2. **Stress Tests** (30 mins):  
   - Concurrent user logins, DB connection pooling.  

#### **Hour 7-8: Final Validation & Report**  
1. **Full Test Suite Run** (30 mins):  
   - Execute all tests + generate coverage report (`pytest --cov`).  
2. **Documentation** (30 mins):  
   - Update `README.md` with test instructions and coverage badges.  

---

### **Key Strategies**:  
- **Parallelize**: Share modules while setting up test environment (Hour 0-1).  
- **Mock Early**: Isolate `database.py` and `logger.py` for unit tests.  
- **Integrate Gradually**: Start with auth/database, then expand to CLI/RBAC.  
- **Automate**: CI-ready by Hour 6.  

**Deliverables**:  
1. 100% unit test coverage for core logic (`auth.py`, `database.py`).  
2. 5+ integration tests covering critical workflows.  
3. CI pipeline running tests on push.  
