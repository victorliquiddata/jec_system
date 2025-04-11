```json
{
  "test_sessions": [
    {
      "file": "test_auth_integration.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "TestAuthManager::test_password_hashing", "status": "PASSED"},
        {"name": "TestAuthManager::test_password_complexity[Short1!-False-Minimum length]", "status": "PASSED"},
        {"name": "TestAuthManager::test_password_complexity[nouppercase123!-False-Missing uppercase]", "status": "PASSED"},
        {"name": "TestAuthManager::test_password_complexity[NOLOWERCASE123!-False-Missing lowercase]", "status": "PASSED"},
        {"name": "TestAuthManager::test_password_complexity[NoDigits!-False-Missing digits]", "status": "PASSED"},
        {"name": "TestAuthManager::test_password_complexity[ValidPass123!-True-Valid password]", "status": "PASSED"},
        {"name": "TestAuthManager::test_password_complexity[Another$Valid1-True-Valid complex password]", "status": "PASSED"},
        {"name": "TestAuthManager::test_successful_login", "status": "PASSED"},
        {"name": "TestAuthManager::test_failed_login", "status": "PASSED"},
        {"name": "TestAuthManager::test_logout", "status": "PASSED"},
        {"name": "TestAuthManager::test_legacy_password_migration", "status": "PASSED"}
      ],
      "stats": {
        "total": 11,
        "passed": 11,
        "failed": 0,
        "duration": "1.89s"
      }
    },
    {
      "file": "test_config.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "TestAppConfig::test_version_constant", "status": "PASSED"},
        {"name": "TestAppConfig::test_db_config_structure", "status": "PASSED"},
        {"name": "TestAppConfig::test_auth_config", "status": "PASSED"},
        {"name": "TestAppConfig::test_theme_enum_values", "status": "PASSED"},
        {"name": "TestAppConfig::test_theme_configurations", "status": "PASSED"},
        {"name": "TestAppConfig::test_load_theme_method", "status": "PASSED"},
        {"name": "TestAppConfig::test_get_db_dsn", "status": "PASSED"}
      ],
      "stats": {
        "total": 7,
        "passed": 7,
        "failed": 0,
        "duration": "0.05s"
      }
    },
    {
      "file": "test_database_integration.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "test_connection_pool_initialization", "status": "PASSED"},
        {"name": "test_schema_enforcement", "status": "PASSED"},
        {"name": "test_execute_query_success", "status": "PASSED"},
        {"name": "test_execute_query_error", "status": "PASSED"},
        {"name": "test_logger_integration", "status": "PASSED"},
        {"name": "test_metrics_tracking", "status": "PASSED"},
        {"name": "test_connection_retry", "status": "PASSED"},
        {"name": "test_pool_closure", "status": "PASSED"},
        {"name": "test_connection_pool_exhaustion", "status": "PASSED"},
        {"name": "test_query_execution_time_logging", "status": "PASSED"},
        {"name": "test_connection_recycling", "status": "PASSED"},
        {"name": "test_concurrent_access", "status": "PASSED"},
        {"name": "test_transaction_rollback", "status": "PASSED"}
      ],
      "stats": {
        "total": 13,
        "passed": 13,
        "failed": 0,
        "duration": "0.14s"
      }
    },
    {
      "file": "test_integration.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "test_successful_login_with_modern_hash", "status": "PASSED"},
        {"name": "test_successful_login_and_legacy_password_upgrade", "status": "PASSED"},
        {"name": "test_login_failure_wrong_password", "status": "PASSED"},
        {"name": "test_logout_clears_session", "status": "PASSED"},
        {"name": "test_legacy_password_fails_if_incorrect", "status": "PASSED"},
        {"name": "test_legacy_password_triggers_upgrade", "status": "PASSED"},
        {"name": "test_login_blocked_in_strict_mode", "status": "PASSED"},
        {"name": "test_failed_login_logs_attempt", "status": "PASSED"}
      ],
      "stats": {
        "total": 8,
        "passed": 8,
        "failed": 0,
        "duration": "2.24s"
      }
    },
    {
      "file": "test_logger4.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "test_logger_initialization", "status": "PASSED"},
        {"name": "test_log_conexao_formatting", "status": "PASSED"},
        {"name": "test_log_negocio_metadata", "status": "PASSED"},
        {"name": "test_log_interface_user_context", "status": "PASSED"},
        {"name": "test_actual_file_writing", "status": "PASSED"},
        {"name": "test_log_file_rotation", "status": "PASSED"},
        {"name": "test_log_level_handling", "status": "PASSED"},
        {"name": "test_multiple_loggers_independence", "status": "PASSED"},
        {"name": "test_invalid_log_level_fallback", "status": "PASSED"}
      ],
      "stats": {
        "total": 9,
        "passed": 9,
        "failed": 0,
        "duration": "0.11s"
      }
    },
    {
      "file": "test_main.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "test_guest_exit", "status": "PASSED"},
        {"name": "test_authenticated_exit", "status": "PASSED"},
        {"name": "test_login_lockout", "status": "PASSED"}
      ],
      "stats": {
        "total": 3,
        "passed": 3,
        "failed": 0,
        "duration": "0.08s"
      }
    },
    {
      "file": "test_rich4.py",
      "environment": {
        "platform": "win32",
        "python": "3.13.2",
        "pytest": "8.3.5",
        "pluggy": "1.5.0"
      },
      "tests": [
        {"name": "TestJECCLI::test_initialization", "status": "PASSED"},
        {"name": "TestJECCLI::test_invalid_theme_defaults_to_dark", "status": "PASSED"},
        {"name": "TestJECCLI::test_apply_theme", "status": "PASSED"},
        {"name": "TestJECCLI::test_display_header_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_display_main_menu_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_display_status_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_prompt_input_string", "status": "PASSED"},
        {"name": "TestJECCLI::test_prompt_input_int", "status": "PASSED"},
        {"name": "TestJECCLI::test_prompt_input_validation_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_display_data_table_with_data_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_display_data_table_empty_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_update_footer_no_user_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_update_footer_with_user_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_clear_screen_mock", "status": "PASSED"},
        {"name": "TestJECCLI::test_singleton_instance", "status": "PASSED"},
        {"name": "test_display_header", "status": "PASSED"},
        {"name": "test_display_main_menu", "status": "PASSED"},
        {"name": "test_display_status_success", "status": "PASSED"},
        {"name": "test_prompt_input_valid", "status": "PASSED"},
        {"name": "test_prompt_input_invalid_then_valid", "status": "PASSED"},
        {"name": "test_display_data_table_with_data", "status": "PASSED"},
        {"name": "test_display_data_table_empty", "status": "PASSED"},
        {"name": "test_update_footer_authenticated", "status": "PASSED"},
        {"name": "test_update_footer_unauthenticated", "status": "PASSED"},
        {"name": "test_clear_screen", "status": "PASSED"}
      ],
      "stats": {
        "total": 25,
        "passed": 25,
        "failed": 0,
        "duration": "0.10s"
      }
    }
  ],
  "overall_summary": {
    "total_tests": 76,
    "passed": 76,
    "failed": 0,
    "success_rate": 100.0,
    "total_duration": "4.61s",
    "environment": {
      "platform": "win32",
      "python_version": "3.13.2",
      "pytest_version": "8.3.5",
      "test_coverage": {
        "auth": 11,
        "config": 7,
        "database": 13,
        "integration": 8,
        "logging": 9,
        "main": 3,
        "ui": 25
      }
    }
  }
}