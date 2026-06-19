# Current file structure
frontend/
└── lib/
    ├── main.dart
    │
    ├── services/
    │   ├── api_service.dart
    │   ├── auth_service.dart
    │   ├── continuous_auth_service.dart
    │   ├── offline_telemetry_cache.dart
    │   ├── dashboard_service.dart
    │   ├── document_service.dart
    │   ├── session_provider.dart
    │   └── risk_score_provider.dart
    │
    ├── views/
    │   ├── auth/
    │   │   ├── login_view.dart
    │   │   └── registration_view.dart
    │   │
    │   ├── dashboard/
    │   │   └── home_portal_view.dart
    │   │
    │   ├── document/
    │   │   ├── upload_wizard_view.dart
    │   │   └── my_documents_view.dart
    │   │
    │   └── security/
    │       └── adaptive_security_view.dart
    │
    └── widgets/
        ├── custom_text_field.dart
        ├── primary_button.dart
        ├── transaction_card.dart
        ├── file_preview_card.dart
        ├── status_chip.dart
        ├── document_card.dart
        └── stats_card.dart

