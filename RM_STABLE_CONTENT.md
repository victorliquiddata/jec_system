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
    "estrategia": "execução standalone dos arquivos pytest a partir do root",
    "cobertura": {
      "STATUS - REVISAndo TODOS aos poucos": [[originais:"auth.py", "database.py",] [recentes:"rich_cli.py,
config.py"]],
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
        "nome": "main.py",
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
        "nome": "logger.py --->>> a ser criado --->>> criado e funcionando como esperado",
        "funcao": "Gerencia o sub dir logs/ com 3 logs principais: conexoes, logica e interface",
        "descricao": "[timing de queries está ok nos testes - prosseguir a teste com auth para integração.]"
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

## Estrutura da Base de Dados

### Database Config
```json
{
  "db": {
    "user": "postgres",
    "db": "postgres",
    "schema": "jec"
  }
}
```

### Database Schema
```json


{
  "schema": "jec",
  "tables": {
    "audit_log": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "user_id": { "type": "uuid", "nullable": true },
        "action": { "type": "varchar(50)", "nullable": false },
        "description": { "type": "text", "nullable": true },
        "ip_address": { "type": "varchar(45)", "nullable": true },
        "timestamp": { "type": "timestamp", "nullable": true, "default": "CURRENT_TIMESTAMP" }
      },
      "constraints": {
        "primary_key": ["id"],
        "foreign_keys": {
          "user_id": { "references": "usuarios(id)" }
        }
      }
    },
    "categorias_causas": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "categoria_pai_id": { "type": "uuid", "nullable": true },
        "nome": { "type": "varchar(50)", "nullable": false },
        "descricao": { "type": "text", "nullable": true },
        "valor_maximo": { "type": "numeric", "nullable": true }
      },
      "constraints": {
        "primary_key": ["id"],
        "unique": ["nome"],
        "foreign_keys": {
          "categoria_pai_id": { "references": "categorias_causas(id)" }
        }
      }
    },
    "documentos": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "processo_id": { "type": "uuid", "nullable": false },
        "tipo": { "type": "varchar(50)", "nullable": false },
        "nome_arquivo": { "type": "varchar(100)", "nullable": false },
        "caminho_arquivo": { "type": "varchar(255)", "nullable": false },
        "data_envio": { "type": "timestamp", "nullable": true, "default": "CURRENT_TIMESTAMP" },
        "descricao": { "type": "text", "nullable": true },
        "obrigatorio": { "type": "boolean", "nullable": true, "default": "true" }
      },
      "constraints": {
        "primary_key": ["id"],
        "foreign_keys": {
          "processo_id": { "references": "processos(id)" }
        },
        "checks": [
          "tipo IN ('peticao_inicial', 'contrato', 'nota_fiscal', 'laudo_medico', 'boletim_ocorrencia', 'comprovante_pagamento', 'outros')"
        ]
      }
    },
    "partes": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "tipo": { "type": "varchar(15)", "nullable": false },
        "nome": { "type": "varchar(100)", "nullable": false },
        "cpf_cnpj": { "type": "varchar(20)", "nullable": false },
        "endereco": { "type": "text", "nullable": true },
        "telefone": { "type": "varchar(20)", "nullable": true },
        "email": { "type": "varchar(100)", "nullable": true },
        "advogado_id": { "type": "uuid", "nullable": true }
      },
      "constraints": {
        "primary_key": ["id"],
        "unique": ["tipo", "cpf_cnpj"],
        "foreign_keys": {
          "advogado_id": { "references": "usuarios(id)" }
        },
        "checks": [
          "tipo IN ('pessoa_fisica', 'pessoa_juridica', 'orgao_publico')"
        ]
      }
    },
    "partes_processo": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "processo_id": { "type": "uuid", "nullable": false },
        "parte_id": { "type": "uuid", "nullable": false },
        "tipo": { "type": "varchar(15)", "nullable": false },
        "principal": { "type": "boolean", "nullable": true, "default": "false" }
      },
      "constraints": {
        "primary_key": ["id"],
        "unique": ["processo_id", "parte_id", "tipo"],
        "foreign_keys": {
          "processo_id": { "references": "processos(id)" },
          "parte_id": { "references": "partes(id)" }
        },
        "checks": [
          "tipo IN ('autor', 'reu', 'testemunha')"
        ]
      }
    },
    "processos": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "numero_processo": { "type": "varchar(25)", "nullable": false },
        "titulo": { "type": "varchar(100)", "nullable": false },
        "descricao": { "type": "text", "nullable": true },
        "categoria_id": { "type": "uuid", "nullable": false },
        "subcategoria_id": { "type": "uuid", "nullable": true },
        "valor_causa": { "type": "numeric", "nullable": false },
        "data_distribuicao": { "type": "date", "nullable": false },
        "status": { "type": "varchar(30)", "nullable": false },
        "juiz_id": { "type": "uuid", "nullable": true },
        "servidor_id": { "type": "uuid", "nullable": true },
        "data_criacao": { "type": "timestamp", "nullable": true, "default": "CURRENT_TIMESTAMP" },
        "data_atualizacao": { "type": "timestamp", "nullable": true, "default": "CURRENT_TIMESTAMP" }
      },
      "constraints": {
        "primary_key": ["id"],
        "unique": ["numero_processo"],
        "foreign_keys": {
          "categoria_id": { "references": "categorias_causas(id)" },
          "subcategoria_id": { "references": "categorias_causas(id)" },
          "juiz_id": { "references": "usuarios(id)" },
          "servidor_id": { "references": "usuarios(id)" }
        },
        "checks": [
          "status IN ('rascunho', 'protocolado', 'em_analise', 'verificacao_competencia', 'aguardando_documentos', 'em_andamento', 'aguardando_decisao', 'concluido', 'arquivado')"
        ]
      }
    },
    "processos_ativos": {
      "columns": {
        "id": { "type": "uuid", "nullable": true },
        "numero_processo": { "type": "varchar(25)", "nullable": true },
        "titulo": { "type": "varchar(100)", "nullable": true },
        "categoria": { "type": "varchar(50)", "nullable": true },
        "status": { "type": "varchar(30)", "nullable": true },
        "data_distribuicao": { "type": "date", "nullable": true },
        "autor": { "type": "varchar(100)", "nullable": true }
      },
      "constraints": {}
    },
    "test_counter": {
      "columns": {
        "id": { "type": "integer", "nullable": false },
        "value": { "type": "integer", "nullable": true }
      },
      "constraints": {
        "primary_key": ["id"]
      }
    },
    "usuarios": {
      "columns": {
        "id": { "type": "uuid", "nullable": false, "default": "uuid_generate_v4()" },
        "cpf": { "type": "varchar(14)", "nullable": false },
        "nome_completo": { "type": "varchar(100)", "nullable": false },
        "email": { "type": "varchar(100)", "nullable": false },
        "senha": { "type": "varchar(255)", "nullable": false },
        "tipo": { "type": "varchar(20)", "nullable": false },
        "telefone": { "type": "varchar(20)", "nullable": true },
        "data_cadastro": { "type": "timestamp", "nullable": true, "default": "CURRENT_TIMESTAMP" },
        "ultimo_login": { "type": "timestamp", "nullable": true }
      },
      "constraints": {
        "primary_key": ["id"],
        "unique": ["cpf", "email"],
        "checks": [
          "tipo IN ('servidor', 'juiz', 'advogado', 'parte')"
        ]
      }
    }
  }
}
```

### Example Constraint Object Template
```json
{
  "constraints": {
    "primary_key": ["id"],
    "unique": ["column_name"],
    "foreign_keys": {
      "column": "referenced_table(column)"
    },
    "checks": {
      "column": ["valid_value1", "valid_value2"]
    }
  }
}
```

### Sample Data from `jec.usuarios` Table
```json
[
  {
    "id": "41c2576c-a2dc-4b0c-9415-8fd446dd63d7",
    "cpf": "54354354367",
    "nome": "VICVIC",
    "email": "vicvic@vic.com",
    "senha": "pbkdf2:sha256:600000$3390a8f9a74160c3d9525c2ec7ece963$cd09980696fbe7440ff478ec2b3eab91fa92ba0fa24286f747dfeed12c75731b",
    "perfil": "advogado",
    "telefone": "243523452345",
    "criado_em": "2025-04-01T01:05:31.542927",
    "atualizado_em": "2025-04-01T01:44:26.855411"
  },
  {
    "id": "fe7c837a-fbcf-4b47-ad63-e6cc26b5cb3b",
    "cpf": "00000000000",
    "nome": "vvvvvvvvv dddddd",
    "email": "dddddd.ddddd@gggg.cccc",
    "senha": "pbkdf2:sha256:600000$d84e0a048bbb5d82f5ea314006c12bd7$8e3fc8f763d7da1b4e8897bb09ff248b2fdf1200bbf6511ff20d7e3202c71315",
    "perfil": "juiz",
    "telefone": null,
    "criado_em": "2025-03-28T16:53:44.539278",
    "atualizado_em": "2025-04-02T16:51:42.379772"
  },
  {
    "id": "18655835-a61a-4d6e-ae1b-2fd0beb0f9b5",
    "cpf": "40935935827",
    "nome": "VICTOR RABELLO DIDIER",
    "email": "victor.didier@gmail.com",
    "senha": "pbkdf2:sha256:600000$be9eb53af35f207999a112a4438978f1$a25d9780fa20611e4d0db6d4e1d5d294c9a3b2ab6435d2b1c92202362f5504d7",
    "perfil": "servidor",
    "telefone": "+55 11 99442-4200",
    "criado_em": "2025-04-02T16:57:00.650645",
    "atualizado_em": "2025-04-02T16:58:02.292646"
  }
]
```

### Sample Data from `jec.categorias_causas`
```json
[
  {
    "id": "3588c22a-e7af-41e6-81ac-e195bbed2251",
    "codigo": null,
    "nome": "Cobranças",
    "descricao": "Ações de cobrança de dívidas, cheques, notas promissórias",
    "valor_causa": 40000.00
  },
  {
    "id": "7b399399-13c7-4023-ac5a-89f42bfc1aa3",
    "codigo": null,
    "nome": "Acidentes",
    "descricao": "Acidentes de trânsito e danos materiais/morais",
    "valor_causa": 40000.00
  },
  {
    "id": "55299dd6-66ad-4ee6-ab70-73b2cb8a1040",
    "codigo": null,
    "nome": "Locação",
    "descricao": "Contratos de locação residencial e comercial",
    "valor_causa": 40000.00
  },
  {
    "id": "bb31f71f-334b-44c7-b082-6aee7f062721",
    "codigo": null,
    "nome": "Danos",
    "descricao": "Danos morais e materiais de menor valor",
    "valor_causa": 40000.00
  },
  {
    "id": "59254a4c-a1ab-4b4e-b949-d4d4861e2797",
    "codigo": null,
    "nome": "Consumidor",
    "descricao": "Conflitos nas relações de consumo",
    "valor_causa": 40000.00
  },
  {
    "id": "fae237b4-bd82-4a0f-be12-581a6f8c275f",
    "codigo": null,
    "nome": "Saúde",
    "descricao": "Planos de saúde e questões médicas",
    "valor_causa": 40000.00
  },
  {
    "id": "4f18d550-dd58-4428-aebb-9bbdf063643c",
    "codigo": null,
    "nome": "Outras Causas",
    "descricao": "Demais matérias de competência do JEC",
    "valor_causa": 40000.00
  },
  {
    "id": "9e99e36f-63a3-4f4f-8e3a-3d14d8ab1e7b",
    "codigo": null,
    "nome": "Danos Estéticos",
    "descricao": "Danos à imagem e estética pessoal",
    "valor_causa": 40000.00
  },
  {
    "id": "be771afb-fa3b-4dd0-a703-2285d5b6e64e",
    "codigo": null,
    "nome": "Causas Diversas",
    "descricao": "Outras questões cíveis de menor complexidade",
    "valor_causa": 40000.00
  }
]
```

### Sample Data from `jec.audit_log`
```json
[
  {
    "id": "92bbf108-afe3-4c2d-b350-bd131e329d20",
    "usuario_id": "fe7c837a-fbcf-4b47-ad63-e6cc26b5cb3b",
    "acao": "user_create",
    "descricao": "Created user sadfasdf@waerqwer.qwer (servidor)",
    "ip": "127.0.0.1",
    "data_hora": "2025-03-31T22:53:11.37572"
  },
  {
    "id": "5ebc1322-f6c1-4961-af2d-24f8f46e290d",
    "usuario_id": "fe7c837a-fbcf-4b47-ad63-e6cc26b5cb3b",
    "acao": "password_change",
    "descricao": "Password changed successfully",
    "ip": "127.0.0.1",
    "data_hora": "2025-03-31T23:59:18.11363"
  },
  {
    "id": "d609d9b8-798d-42d2-8cec-31bc80ca86fd",
    "usuario_id": "fe7c837a-fbcf-4b47-ad63-e6cc26b5cb3b",
    "acao": "user_create",
    "descricao": "Created user vicvic@vic.com (advogado)",
    "ip": "127.0.0.1",
    "data_hora": "2025-04-01T01:05:33.808183"
  },
  {
    "id": "4677313b-2ba9-4767-a702-171b5382be85",
    "usuario_id": "41c2576c-a2dc-4b0c-9415-8fd446dd63d7",
    "acao": "password_change",
    "descricao": "Password changed successfully",
    "ip": "127.0.0.1",
    "data_hora": "2025-04-01T01:45:46.160476"
  }
]
```

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

