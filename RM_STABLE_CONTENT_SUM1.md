# Sistema JEC

Uma aplicação de interface de linha de comando (CLI) para gerenciamento de casos de juizados especiais cíveis.

## Visão Geral do Projeto

```json
{
  "projeto": {
    "nome": "Sistema JEC",
    "tipo": "CLI",
    "linguagem": "Python",
    "interface": "Rich",
    "escopo": "gestao_juizado_especial_civel",
    "media_max_usuarios": 15
  },
  "versoes": {
    "0.0": "Proposta inicial (2025-02)",
    "0.1": "2025-04-04: Implementação do núcleo + autenticação",
    "roadmap": {
      "v0.2": "Otimização do pool de conexões com o banco de dados - COMPLETO",
      "v0.3": "Integração, Aperfeiçoamento e Revisão da UI Proposta atraves de integração de dois novos arquivos: rich_cli e config>> proceder para testes e revisão da integração geral - COMPLETO",
      "v0.4": "Implementar e integrar sistema abrangente de logging com logger.py - EM PROCESSO",
      "v0.5 em diante": "TESTE GERAL DE TODOS MÓDULOS - NÃO INICIADO",
      "vNUMERO": "[...]",
      "v0.7 em diante": "Implementar gerenciamento completo de usuários, documentos e processos em etapas - NÃO INICIADO"
    
    }
  },
  "notas_tecnicas": {
    "pendente_revisao": {
      "modulo": "TODOS OS MODULOS",
      "atual": "lógica e robustez EM GERAL",
      "prazo": "v0.9",
      "impacto": "SEGURANCA E ui/ux"
    }
  }
}
```

## Testes

```json
{
  "testes": {
    "metodologia": "TDD com pytest via arquivos standalone (test_*.py)",
    "estrategia": "execução standalone dos arquivos pytest a partir do root, com ponto principal ao fim usando "{
      if __name__ == "__main__":
    import sys

    sys.exit(pytest.main(["-v", __file__]))
para obter resultados detalhados e rapidos
}"",
    "cobertura": {
      "STATUS - revisoes feitas e 5 testes concluidos - hora de INTEGRAR LOGGER E RICH_CLI": [[originais:"auth.py", "database.py",] [recentes:"rich_cli.py,config.py,logger.py"]],
    },
    "git_integracao": "Commits por módulo testado"
  }
}
```

## Estrutura de Arquivos

```json
{
  "estrutura_arquivos": {
    "localizacao_arquivos": "todos os arquivos na raiz do projeto",
    "arquivos_principais_em_root": [
      {
        "nome": "main.py - não foi criado ainda",
        "funcao": "Ponto de Entrada",
        "descricao": "Gerencia O PONTO DE ENTRADA"
      },
      {
        "nome": "database.py",
        "funcao": "Gerenciador de Banco de Dados",
        "descricao": "Gerencia conexões e consultas ao banco PostgreSQL."
      },
      {
        "nome": "auth.py",
        "funcao": "Autenticação e Segurança",
        "descricao": "Gerencia autenticação de usuários, hash de senhas (\"PBKDF2-HMAC-SHA256 (600k iterações)\") e sessões."
      },
      {
        "nome": "config.py",
        "funcao": "Configuração Básica",
        "descricao": "Gerencia configurações básicas e garante principios dry de escrita de codigo"
      },
      {
        "nome": "rich_cli.py",
        "funcao": "Comandos da CLI & Lógica de Negócio",
        "descricao": "Define interface utilizando Rich, implementando funcionalidades principais e garantindo principios DRY de escrita de codigo."
      },
      {
        "nome": "logger.py --->>> a ser criado --->>> criado e funcionando --->>> test_logger.py e test_logger2.py ALL GREEN",
        "funcao": "Gerencia o sub dir logs/ com 3 logs principais: conexoes, logica e interface",
        "descricao": "[timing de queries está ok nos testes - prosseguir a teste com novo auth para integração.]"
      }
    ],
    "arquivos_suporte_e_venv": [".env", ".gitignore", ".venv"],
    "template_env": {
      "DB_HOST": "",
      "DB_PORT": "",
      "DB_USUARIO": "",
      "DB_SENHA": "",
      "DB_NOME": "",
      "DB_SCHEMA": "jec"
    }
  }
}
```

---

## 📁 **Database Configuration**
```json
{
  "user": "postgres",
  "db": "postgres",
  "schema": "jec"
}
```

---

### 🗂️ **Tables Overview (jec schema)**

#### 1. **usuarios**
- Stores system users (`servidor`, `juiz`, `advogado`, `parte`).
- Key fields: `id`, `cpf`, `nome_completo`, `email`, `senha`, `tipo`.
- Unique constraints: `cpf`, `email`.

#### 2. **audit_log**
- Tracks user actions.
- Fields: `user_id`, `action`, `description`, `ip_address`, `timestamp`.
- FK: `user_id → usuarios(id)`.

#### 3. **categorias_causas**
- Hierarchical category structure.
- Fields: `nome`, `descricao`, `valor_maximo`, `categoria_pai_id`.
- FK: `categoria_pai_id → categorias_causas(id)`.

#### 4. **documentos**
- Documents related to legal processes.
- Fields: `tipo`, `nome_arquivo`, `caminho_arquivo`, `processo_id`, `obrigatorio`.
- Enum check on `tipo`.
- FK: `processo_id → processos(id)`.

#### 5. **partes**
- Legal parties involved in processes.
- Fields: `tipo`, `nome`, `cpf_cnpj`, `advogado_id`.
- Unique: [`tipo`, `cpf_cnpj`].
- Enum check on `tipo`.
- FK: `advogado_id → usuarios(id)`.

#### 6. **partes_processo**
- Associates parties to processes.
- Fields: `processo_id`, `parte_id`, `tipo`, `principal`.
- Unique: [`processo_id`, `parte_id`, `tipo`].
- Enum check on `tipo`.
- FKs: `processo_id → processos(id)`, `parte_id → partes(id)`.

#### 7. **processos**
- Core entity for legal cases.
- Fields: `numero_processo`, `titulo`, `categoria_id`, `subcategoria_id`, `valor_causa`, `status`, `juiz_id`, `servidor_id`.
- Unique: `numero_processo`.
- Enum check on `status`.
- FKs: multiple to `categorias_causas`, `usuarios`.

#### 8. **processos_ativos**
- Likely a view or simplified table for active cases.
- No constraints defined.
- Fields: subset of `processos`.

#### 9. **test_counter**
- Simple counter (possibly for testing).
- Fields: `id`, `value`.

---

### 🧪 **Example Table: usuarios**
Contains example records with fields like:
- `id`, `cpf`, `nome`, `email`, `senha`, `perfil`, `telefone`, `criado_em`, `atualizado_em`.

---

### 🔧 **Constraint Template Reference**
Defines standard structure for:
- `primary_key`, `unique`, `foreign_keys`, `checks`.

---



## Authentication Implementation Details

```json
{
  "hashing": {
    "algorithm": "PBKDF2-HMAC-SHA256",
    "library": "hashlib",
    "salt": {
      "length_bytes": 16,
      "generator": "secrets.token_hex(16)"
    },
    "iterations": 600000,
    "format": "pbkdf2:sha256:600000$<salt>$<hash>"
  },
  "functions": {
    "hash_password": {
      "input": ["password", "salt (optional)"],
      "behavior": [
        "Generates random 16-byte hex salt if not provided",
        "Hashes password using hashlib.pbkdf2_hmac with specified salt and iterations",
        "Returns formatted string"
      ]
    },
    "verify_password": {
      "input": ["stored_hash", "provided_password"],
      "behavior": [
        "If stored_hash is legacy plaintext, compare directly",
        "Parse algorithm, iterations, salt, and hash from format",
        "Recompute hash with same params",
        "Use secrets.compare_digest for constant-time comparison"
      ]
    },
    "migrate_password_on_login": {
      "condition": "If stored password is not PBKDF2-formatted and login is successful",
      "action": [
        "Rehash password with PBKDF2",
        "Update user record in database"
      ]
    },
    "validate_password_complexity": {
      "rules": {
        "min_length": 8,
        "uppercase": true,
        "lowercase": true,
        "digit": true,
        "special_characters": "!@#$%^&*(),.?\":{}|<>"
      }
    }
  },
  "flow": {
    "signup": [
      "Validate password complexity",
      "Hash password using PBKDF2",
      "Store in database"
    ],
    "login": [
      "Verify password",
      "If legacy hash: rehash and update"
    ],
    "password_change": [
      "Validate complexity",
      "Hash and store updated password"
    ]
  },
  "security": {
    "resistant_to": [
      "Rainbow table attacks",
      "Brute-force attacks (via high iteration count)",
      "Timing attacks (via constant-time comparison)"
    ]
  }
}
```




## Módulos Nucleares

```json
{
  "modulos_nucleares": {
    "config": {
      "descricao": "Gerenciamento de temas",
      "temas": ["padrao", "escuro"],
      "funcionalidades": ["esquemas_cores"]
    },
    "banco_dados": {
      "tipo": "PostgreSQL",
      "conexao": {
        "pooling": "SimpleConnectionPool (implementado com reconexão automática)",
        "min_conexoes": 1,
        "max_conexoes": 5,
        "timeout": 30,
        "tentativas_reconexao": 3
      },
      "implementado": {
        "core": ["auth", "database", "cli_base"],
        "pendente": [
          "melhorias de ui",
          "temas_ui",
          "implementação de modelos",
          "modularização",
          "opções crud básicas",
          "opções crud avançadas",
          "relatórios",
          "análise básica",
          "análise avançada",
          "integração com sistemas: esaj, etc"
        ]
      }
    },
    "autenticacao": {
      "seguranca": {
        "hashing": "PBKDF2-HMAC-SHA256",
        "iteracoes": 600000,
        "tempo_expiracao_sessao": "30_minutos"
      },
      "roles_usuarios": ["advogado", "juiz", "servidor", "parte", "visitante"]
    },
    "menus": {
      "estilo": "painel_numerado",
      "funcionalidades": ["atalhos", "contexto_dinamico", "entrada_sql"]
    },
    "servicos": {
      "entidades": ["corresponde_info_db"]
    }
  }
}
```

## Especificações Técnicas

```json
{
  "especificacoes_tecnicas": {
    "sistema_operacional_unico": "Windows",
    "servidor": {
      "modelo": "Acer 2020",
      "especificacoes": "20GB RAM, Intel Core i5, servidor: apenas roda postgres e pgadmin e se conecta ao wifi doméstico"
    },
    "rede": "Wi-Fi LAN",
    "cliente": {
      "modelo": "Lenovo 2014",
      "especificacoes": "16GB RAM, Intel Core i7, Geforce RTX 4050, cliente/ambiente dev: apenas VS Code + Python + PowerShell + CMD + integração com GitHub, etc; conexão via Wi-Fi doméstico"
    },
    "log": {
      "nivel": "desconhecido - [inserir após análise]",
      "requisitos_venv": [
        "psycopg2-binary",
        "python-dotenv",
        "rich",
        "pytest", 
        "[ADICIONAR MAIS SE NECESSÁRIO]"
      ]
    }
  }
}
```

## Funcionalidades

```json
{
  "funcionalidades": {
    "essenciais": {
      "gerenciamento_de_login_e_temas": ["CRUD", "autenticacao"],
      "gerenciamento_usuarios": ["CRUD", "autenticacao"],
      "gerenciamento_processos": ["CRUD", "autenticacao"],
      "rastreamento_processos": ["status", "prazos"]
    },
    "futuro": {
      "calendario": ["audiências", "compromissos"],
      "integracoes": ["PJe", "Esaj"],
      "escalabilidade": ["dados_flexiveis", "principios_DRY"]
    }
  }
}
```

## Requisitos de Interface (UI)

```json
{
  "requisitos_ui": {
    "estilo": "dashboard_moderno_minimalista_com_cores_suaves",
    "componentes": [
      "barras_de_progresso",
      "seletor_de_tema",
      "tela_de_login"
    ],
    "navegacao": {
      "restricoes_visitante": true,
      "pre_visualizacoes_rapidas": true
    },
    "seguranca": {
      "hashing": "PBKDF2-HMAC-SHA256 (600k iterações)",
      "salt": "secrets.token_hex(16)",
      "legacy_support": "Manipulador de migração de senhas em texto plano",
      "complexity_rules": [
        "mínimo 8 caracteres",
        "letra maiúscula",
        "letra minúscula",
        "dígito",
        "caractere especial"
      ]
    }
  }
}
```


## Informações de Entrega do Projeto

```json
{
  "entrega": {
    "prazo": "15_dias",
    "prioridade": "gerenciamento_documentos",
    "restricoes": ["uso_interno_somente"]
  },
  "implementacao": {
    "foco_atual": [
      "conexao_banco_dados",
      "CRUD_basico_usuarios"
    ],
    "padroes_codigo": [
      "tratamento_de_erros",
      "validacao_de_parametros",
      "robustez_da_conexao",
      "configuracao_env"
    ]
  },
  "desenvolvedor": {
    "nome": "Victor",
    "data_nascimento": "06/1994",
    "localizacao": "São Paulo, Brasil",
    "email": "victor.didier@gmail.com",
    "skills": [
      "sql_intermediario",
      "python_intermediario",
      "graphic_design_intermediario"
    ]
  }
}
```

