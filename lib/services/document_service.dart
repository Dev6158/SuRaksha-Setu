import 'api_service.dart';

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

class DocumentType {
  final String id;
  final String label;
  final String subtitle;
  final bool isRequired;
  final List<String> acceptedFormats;
  final int maxSizeMb;

  const DocumentType({
    required this.id,
    required this.label,
    required this.subtitle,
    required this.isRequired,
    required this.acceptedFormats,
    required this.maxSizeMb,
  });

  factory DocumentType.fromJson(Map<String, dynamic> json) => DocumentType(
      id: (json['id'] ?? json['code']).toString().toLowerCase(),
      label: json['label'] as String,
      subtitle: json['subtitle'] as String? ?? '',
      isRequired: json['is_required'] as bool? ?? false,
      acceptedFormats: List<String>.from(
        json['accepted_formats'] ??
        json['allowedMimeTypes'] ??
        ['pdf', 'jpg', 'png'],
      ),
      maxSizeMb: json['max_size_mb'] as int? ?? 10,
    );
}

class UploadedDocument {
  final String documentId;
  final String documentTypeId;
  final String fileName;
  final String status; // pending_review | approved | rejected
  final DateTime uploadedAt;

  const UploadedDocument({
    required this.documentId,
    required this.documentTypeId,
    required this.fileName,
    required this.status,
    required this.uploadedAt,
  });

  factory UploadedDocument.fromJson(Map<String, dynamic> json) =>
      UploadedDocument(
        documentId: json['document_id'] as String,
        documentTypeId: json['document_type_id'] as String,
        fileName: json['file_name'] as String,
        status: json['status'] as String,
        uploadedAt: DateTime.parse(json['uploaded_at'] as String),
      );
}

// ---------------------------------------------------------------------------
// DocumentService
// ---------------------------------------------------------------------------

class DocumentService {
  static final DocumentService _instance = DocumentService._internal();
  factory DocumentService() => _instance;
  DocumentService._internal();

  final _api = ApiService();

  /// Fetch supported document types from the backend.
  /// Falls back to a standard set so the UI never shows empty on first load
  /// while the backend call is in flight.
  Future<ApiResponse<List<DocumentType>>> getDocumentTypes() async {
    final response = await _api.get('/api/v1/documents/types');
    if (!response.isSuccess) {
      return ApiResponse.failure(response.error);
    }
    try {
      final list = (response.data!['value'] as List)
      .map((e) => DocumentType.fromJson(e as Map<String, dynamic>))
      .toList();
      return ApiResponse.success(list);
    } catch (_) {
      return const ApiResponse.failure('Failed to parse document types.');
    }
  }

  /// Upload a single file for a given document type.
  Future<ApiResponse<UploadedDocument>> uploadDocument({
    required String documentTypeId,
    required String filePath,
  }) async {
    final response = await _api.uploadFile(
      path: '/api/v1/documents/upload',
      filePath: filePath,
      fieldName: 'file',
      fields: {'document_type_id': documentTypeId},
    );

    if (!response.isSuccess) {
      return ApiResponse.failure(response.error);
    }
    try {
      return ApiResponse.success(
          UploadedDocument.fromJson(response.data!['document'] as Map<String, dynamic>));
    } catch (_) {
      return const ApiResponse.failure('Upload succeeded but response was unexpected.');
    }
  }

  /// List all documents uploaded by the current user.
  Future<ApiResponse<List<UploadedDocument>>> getMyDocuments() async {
    final response = await _api.get('/api/v1/documents');
    if (!response.isSuccess) {
      return ApiResponse.failure(response.error);
    }
    try {
      final list = (response.data!['documents'] as List)
          .map((e) => UploadedDocument.fromJson(e as Map<String, dynamic>))
          .toList();
      return ApiResponse.success(list);
    } catch (_) {
      return const ApiResponse.failure('Failed to parse documents.');
    }
  }
}