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
        id: json['id'] as String,
        label: json['label'] as String,
        subtitle: json['subtitle'] as String,
        isRequired: json['is_required'] as bool? ?? false,
        acceptedFormats: List<String>.from(
            json['accepted_formats'] as List? ?? ['pdf', 'jpg', 'png']),
        maxSizeMb: json['max_size_mb'] as int? ?? 10,
      );
}

class UploadedDocument {
  final String documentId;
  final String documentTypeId;
  final String fileName;
  final String status;
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
// Analysis result model
// ---------------------------------------------------------------------------

enum RiskLevel { low, medium, high, unknown }

class DocumentAnalysis {
  final double riskScore;
  final String decision;
  final String summary;
  final RiskLevel riskLevel;

  const DocumentAnalysis({
    required this.riskScore,
    required this.decision,
    required this.summary,
    required this.riskLevel,
  });

  factory DocumentAnalysis.fromJson(Map<String, dynamic> json) {
    final decision = (json['decision'] as String? ?? '').toUpperCase();

    RiskLevel level;
    switch (decision) {
      case 'LOW_RISK':
        level = RiskLevel.low;
        break;
      case 'MEDIUM_RISK':
        level = RiskLevel.medium;
        break;
      case 'HIGH_RISK':
        level = RiskLevel.high;
        break;
      default:
        level = RiskLevel.unknown;
    }

    return DocumentAnalysis(
      riskScore: (json['riskScore'] as num? ?? 0).toDouble(),
      decision: decision,
      summary: json['summary'] as String? ?? 'No summary available.',
      riskLevel: level,
    );
  }

  String get riskLabel {
    switch (riskLevel) {
      case RiskLevel.low:
        return 'Low Risk';
      case RiskLevel.medium:
        return 'Medium Risk';
      case RiskLevel.high:
        return 'High Risk';
      case RiskLevel.unknown:
        return 'Unknown';
    }
  }

  String get riskPercent => '${(riskScore * 100).toStringAsFixed(0)}%';
}

// ---------------------------------------------------------------------------
// DocumentService
// ---------------------------------------------------------------------------

class DocumentService {
  static final DocumentService _instance = DocumentService._internal();
  factory DocumentService() => _instance;
  DocumentService._internal();

  final _api = ApiService();

  Future<ApiResponse<List<DocumentType>>> getDocumentTypes() async {
    final response = await _api.get('/api/v1/documents/types');
    if (!response.isSuccess) return ApiResponse.failure(response.error);
    try {
      final list = (response.data!['types'] as List)
          .map((e) => DocumentType.fromJson(e as Map<String, dynamic>))
          .toList();
      return ApiResponse.success(list);
    } catch (_) {
      return const ApiResponse.failure('Failed to parse document types.');
    }
  }

  Future<ApiResponse<UploadedDocument>> uploadDocument({
    required String documentTypeId,
    required List<int> fileBytes,
    required String fileName,
  }) async {
    final response = await _api.uploadFile(
      path: '/api/v1/documents/upload',
      fileBytes: fileBytes,
      fileName: fileName,
      fieldName: 'file',
      fields: {'document_type_id': documentTypeId},
    );
    if (!response.isSuccess) return ApiResponse.failure(response.error);
    try {
      return ApiResponse.success(UploadedDocument.fromJson(
          response.data!['document'] as Map<String, dynamic>));
    } catch (_) {
      return const ApiResponse.failure(
          'Upload succeeded but response was unexpected.');
    }
  }

  Future<ApiResponse<List<UploadedDocument>>> getMyDocuments() async {
    final response = await _api.get('/api/v1/documents');
    if (!response.isSuccess) return ApiResponse.failure(response.error);
    try {
      final list = (response.data!['documents'] as List)
          .map((e) => UploadedDocument.fromJson(e as Map<String, dynamic>))
          .toList();
      return ApiResponse.success(list);
    } catch (_) {
      return const ApiResponse.failure('Failed to parse documents.');
    }
  }

  /// Sends file bytes to POST /analyze-document for AI analysis.
  /// Returns riskScore, decision (LOW_RISK/MEDIUM_RISK/HIGH_RISK), summary.
  Future<ApiResponse<DocumentAnalysis>> analyzeDocument({
    required List<int> fileBytes,
    required String fileName,
  }) async {
    final response = await _api.uploadFile(
      path: '/analyze-document',
      fileBytes: fileBytes,
      fileName: fileName,
      fieldName: 'file',
    );
    if (!response.isSuccess) return ApiResponse.failure(response.error);
    try {
      return ApiResponse.success(DocumentAnalysis.fromJson(response.data!));
    } catch (_) {
      return const ApiResponse.failure(
          'Analysis completed but response was unexpected.');
    }
  }
}
