Aqui está um plano detalhado para os testes de segurança focados em autenticação e SQL Injection:

---

### **Passo a Passo para Testes de Segurança**  
**Objetivo:** Identificar e mitigar vulnerabilidades de Timing Attack e SQL Injection

---

#### **1. Preparação do Ambiente (1h)**  
✅ **Configuração de Teste:**
```bash
# Criar ambiente isolado
python -m venv .venv-test
source .venv-test/bin/activate  # Linux/Mac
# .\.venv-test\Scripts\activate  # Windows

# Instalar dependências de teste
pip install pytest requests rich numpy
```

✅ **Banco de Dados de Teste:**
```sql
-- Criar schema de teste
CREATE SCHEMA jec_test;
-- Popular com dados sensíveis fictícios
INSERT INTO jec_test.usuarios (cpf, senha) VALUES 
('11111111111', 'test_hash'),
('22222222222', 'hash_legacy');
```

---

#### **2. Timing Attack na Autenticação (3h)**  
🔍 **Metodologia:** Medir tempo de resposta para diferentes cenários de login  

✅ **Caso 1 - Usuário Existente vs. Inexistente:**
```python
# Script: test_timing.py
import timeit

def test_user_existence():
    # Usuário existente
    existente = timeit.timeit('auth_manager.login("victor.didier@gmail.com", "wrongpass")', 
                             setup='from auth import auth_manager', number=100)
    
    # Usuário inexistente
    inexistente = timeit.timeit('auth_manager.login("naoexiste@test.com", "wrongpass")', 
                               setup='from auth import auth_manager', number=100)
    
    assert abs(existente - inexistente) < 0.1  # 100ms de tolerância
```

✅ **Caso 2 - Hash Correto vs. Incorreto:**
```python
# Modificar auth.py temporariamente para logging
def verify_password(stored_hash, provided_password):
    start = time.perf_counter()
    # ... código original ...
    elapsed = time.perf_counter() - start
    logging.debug(f"Tempo verificação: {elapsed:.6f}s")
    return result
```

✅ **Análise:**
```bash
# Executar com profiling
python -m cProfile -s cumtime auth.py
```

---

#### **3. Testes de SQL Injection (4h)**  
🔍 **Vetores de Ataque:**  

✅ **Payloads Básicos (Login):**
```python
payloads = [
    "' OR '1'='1'--",
    "admin'--",
    "'; DROP TABLE usuarios;--"
]

for p in payloads:
    response = auth_manager.login(p, "anypass")
    assert "Invalid credentials" in response  # Resposta genérica esperada
```

✅ **Teste em Consultas de Processos:**
```python
# Testar campo de busca
payloads = [
    "123'; UPDATE usuarios SET senha='hacked' WHERE email='victor.didier@gmail.com';--",
    "%' UNION SELECT cpf, senha FROM usuarios WHERE '1'='1"
]

for p in payloads:
    results = db_manager.execute_query(f"SELECT * FROM processos WHERE numero_processo LIKE '{p}'")
    assert not results  # Não deve retornar dados
```

✅ **Teste Blind SQL (Time-Based):**
```python
import time

def test_blind_sql():
    start = time.time()
    db_manager.execute_query("SELECT pg_sleep(2)")  # 2 segundos
    elapsed = time.time() - start
    assert elapsed < 2.5  # Tolerância de rede
```

---

#### **4. Análise de Resultados (2h)**  
🔍 **Critérios de Risco:**

| Vulnerabilidade       | Critério de Falha             | Gravidade |
|-----------------------|--------------------------------|-----------|
| Timing Attack         | Diferença > 100ms entre casos  | Alta      |
| SQL Injection         | Execução bem-sucedida de query | Crítica   |

📊 **Relatório de Exemplo:**
```markdown
## Resultados dos Testes

### Timing Attack
- Diferença média entre usuário existente/inexistente: 127ms ❌
- **Recomendação:** 
  ```python
  # Adicionar delay fixo
  def verify_password(...):
      result = ...  # Lógica original
      time.sleep(0.15)  # 150ms adicional
      return result
  ```

### SQL Injection
- 3/10 payloads retornaram dados ❌
- **Código Vulnerável Encontrado:**
  ```python
  # commands.py (Linha 142)
  query = f"SELECT * FROM processos WHERE titulo LIKE '%{term}%'"  # ❌
  ```
```

---

#### **5. Mitigação e Validação (3h)**  
✅ **Correções Prioritárias:**
```python
# Correção para SQL Injection
def execute_query(query, params=None):
    # Usar sempre parâmetros separados
    cursor.execute(query, params)  # ✅
```

✅ **Validação Final:**
```bash
# Testar após correções
pytest test_security.py -v

# Verificar logs do PostgreSQL
tail -f /var/log/postgresql/postgresql-14-main.log | grep 'ERROR'
```

---

#### **6. Documentação (1h)**  
📄 **Relatório Final Deve Conter:**
1. Metodologia utilizada
2. Payloads testados
3. Trechos de código vulneráveis
4. Evidências de sucesso/falha
5. Gráficos de tempo de resposta

**Template:**  
```markdown
# Relatório de Segurança JEC v2.0

## Timing Attack
![Gráfico de Tempos](timing_chart.png)

## SQL Injection
```sql
-- Query maliciosa bloqueada
SELECT * FROM processos WHERE numero_processo = '123'; DROP...'
-- Resultado: ERROR: syntax error at end of input
```

---

**Recursos Adicionais:**  
- [OWASP Testing Guide - Timing Attacks](https://owasp.org/www-community/attacks/Testing_for_Timing_Attacks)
- [SQL Injection Cheat Sheet](https://pentestmonkey.net/cheat-sheet/sql-injection/postgres-sql-injection-cheat-sheet)

Este plano combina técnicas manuais e automatizadas para garantir uma cobertura robusta das vulnerabilidades alvo. Adapte os intervalos de tempo e payloads conforme a realidade do seu ambiente! 🔒