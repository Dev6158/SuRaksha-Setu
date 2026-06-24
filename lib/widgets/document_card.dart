import 'package:flutter/material.dart';
import '../services/document_service.dart';
import 'status_chip.dart';

class DocumentCard extends StatefulWidget {
  final String documentId;
  final String documentTypeId;
  final String fileName;
  final String status;
  final DateTime uploadedAt;
  final List<int>? fileBytes; // needed to send for analysis

  const DocumentCard({
    super.key,
    required this.documentId,
    required this.documentTypeId,
    required this.fileName,
    required this.status,
    required this.uploadedAt,
    this.fileBytes,
  });

  @override
  State<DocumentCard> createState() => _DocumentCardState();
}

class _DocumentCardState extends State<DocumentCard> {
  bool _hovered = false;
  bool _expanded = false;
  bool _isAnalysing = false;
  DocumentAnalysis? _analysis;
  String? _analysisError;

  final _documentService = DocumentService();

  Future<void> _runAnalysis() async {
    if (widget.fileBytes == null) {
      setState(() {
        _analysisError =
            'File data not available. Please re-upload to analyse.';
        _expanded = true;
      });
      return;
    }

    setState(() {
      _isAnalysing = true;
      _analysisError = null;
      _expanded = true;
    });

    final result = await _documentService.analyzeDocument(
      fileBytes: widget.fileBytes!,
      fileName: widget.fileName,
    );

    if (!mounted) return;
    setState(() {
      _isAnalysing = false;
      if (result.isSuccess) {
        _analysis = result.data;
      } else {
        _analysisError = result.error;
      }
    });
  }

  IconData get _fileIcon {
    final ext = widget.fileName.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return Icons.picture_as_pdf_outlined;
      case 'jpg':
      case 'jpeg':
      case 'png':
        return Icons.image_outlined;
      default:
        return Icons.insert_drive_file_outlined;
    }
  }

  Color get _fileColor {
    final ext = widget.fileName.split('.').last.toLowerCase();
    switch (ext) {
      case 'pdf':
        return const Color(0xFFDC2626);
      case 'jpg':
      case 'jpeg':
      case 'png':
        return const Color(0xFF7C3AED);
      default:
        return const Color(0xFF2563EB);
    }
  }

  String get _docTypeLabel {
    return widget.documentTypeId
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty
            ? ''
            : '${w[0].toUpperCase()}${w.substring(1).toLowerCase()}')
        .join(' ');
  }

  String get _formattedDate {
    final d = widget.uploadedAt;
    final now = DateTime.now();
    final diff = now.difference(d);
    if (diff.inDays == 0) return 'Today';
    if (diff.inDays == 1) return 'Yesterday';
    if (diff.inDays < 7) return '${diff.inDays} days ago';
    return '${d.day} ${_month(d.month)} ${d.year}';
  }

  String _month(int m) {
    const months = [
      '', 'Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec',
    ];
    return months[m];
  }

  Color get _riskColor {
    if (_analysis == null) return const Color(0xFF64748B);
    switch (_analysis!.riskLevel) {
      case RiskLevel.low:
        return const Color(0xFF16A34A);
      case RiskLevel.medium:
        return const Color(0xFFD97706);
      case RiskLevel.high:
        return const Color(0xFFDC2626);
      case RiskLevel.unknown:
        return const Color(0xFF64748B);
    }
  }

  Color get _riskBgColor {
    if (_analysis == null) return const Color(0xFFF1F5F9);
    switch (_analysis!.riskLevel) {
      case RiskLevel.low:
        return const Color(0xFFDCFCE7);
      case RiskLevel.medium:
        return const Color(0xFFFEF3C7);
      case RiskLevel.high:
        return const Color(0xFFFEE2E2);
      case RiskLevel.unknown:
        return const Color(0xFFF1F5F9);
    }
  }

  IconData get _riskIcon {
    if (_analysis == null) return Icons.help_outline;
    switch (_analysis!.riskLevel) {
      case RiskLevel.low:
        return Icons.verified_outlined;
      case RiskLevel.medium:
        return Icons.warning_amber_outlined;
      case RiskLevel.high:
        return Icons.dangerous_outlined;
      case RiskLevel.unknown:
        return Icons.help_outline;
    }
  }

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        decoration: BoxDecoration(
          color: _hovered ? const Color(0xFFF8FAFF) : Colors.white,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(
            color: _hovered
                ? const Color(0xFF1A3A6B).withOpacity(0.25)
                : const Color(0xFFE2E8F0),
          ),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF1A3A6B).withOpacity(0.05),
              blurRadius: 8,
              offset: const Offset(0, 2),
            ),
          ],
        ),
        child: Column(
          children: [
            // ---- Main row ----
            Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: _fileColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(10),
                    ),
                    child: Icon(_fileIcon, color: _fileColor, size: 24),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          widget.fileName,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: Color(0xFF0F172A),
                          ),
                          overflow: TextOverflow.ellipsis,
                        ),
                        const SizedBox(height: 3),
                        Text(
                          _docTypeLabel,
                          style: const TextStyle(
                            fontSize: 12,
                            color: Color(0xFF64748B),
                          ),
                        ),
                        const SizedBox(height: 6),
                        Row(
                          children: [
                            StatusChip.fromString(widget.status,
                                fontSize: 10),
                            const SizedBox(width: 8),
                            const Icon(Icons.schedule_outlined,
                                size: 11, color: Color(0xFF94A3B8)),
                            const SizedBox(width: 3),
                            Text(
                              _formattedDate,
                              style: const TextStyle(
                                fontSize: 11,
                                color: Color(0xFF94A3B8),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                  const SizedBox(width: 8),

                  // Analyse button
                  GestureDetector(
                    onTap: _isAnalysing ? null : _runAnalysis,
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 6),
                      decoration: BoxDecoration(
                        color: _analysis != null
                            ? _riskBgColor
                            : const Color(0xFF1A3A6B),
                        borderRadius: BorderRadius.circular(8),
                      ),
                      child: _isAnalysing
                          ? const SizedBox(
                              width: 14,
                              height: 14,
                              child: CircularProgressIndicator(
                                strokeWidth: 2,
                                color: Colors.white,
                              ),
                            )
                          : Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                Icon(
                                  _analysis != null
                                      ? _riskIcon
                                      : Icons.analytics_outlined,
                                  size: 13,
                                  color: _analysis != null
                                      ? _riskColor
                                      : Colors.white,
                                ),
                                const SizedBox(width: 4),
                                Text(
                                  _analysis != null
                                      ? _analysis!.riskLabel
                                      : 'Analyse',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: _analysis != null
                                        ? _riskColor
                                        : Colors.white,
                                  ),
                                ),
                              ],
                            ),
                    ),
                  ),

                  // Expand toggle if analysis done
                  if (_analysis != null || _analysisError != null) ...[
                    const SizedBox(width: 6),
                    GestureDetector(
                      onTap: () =>
                          setState(() => _expanded = !_expanded),
                      child: Icon(
                        _expanded
                            ? Icons.keyboard_arrow_up
                            : Icons.keyboard_arrow_down,
                        color: const Color(0xFF94A3B8),
                        size: 20,
                      ),
                    ),
                  ],
                ],
              ),
            ),

            // ---- Analysis result panel ----
            if (_expanded && (_analysis != null || _analysisError != null))
              Container(
                width: double.infinity,
                padding: const EdgeInsets.fromLTRB(14, 0, 14, 14),
                child: _analysisError != null
                    ? Container(
                        padding: const EdgeInsets.all(12),
                        decoration: BoxDecoration(
                          color: const Color(0xFFFEF2F2),
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(
                              color: const Color(0xFFFCA5A5)),
                        ),
                        child: Row(
                          children: [
                            const Icon(Icons.error_outline,
                                color: Color(0xFFDC2626), size: 16),
                            const SizedBox(width: 8),
                            Expanded(
                              child: Text(
                                _analysisError!,
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFFDC2626),
                                ),
                              ),
                            ),
                            GestureDetector(
                              onTap: _runAnalysis,
                              child: const Text(
                                'Retry',
                                style: TextStyle(
                                  fontSize: 12,
                                  color: Color(0xFFDC2626),
                                  fontWeight: FontWeight.w600,
                                ),
                              ),
                            ),
                          ],
                        ),
                      )
                    : _buildAnalysisPanel(),
              ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalysisPanel() {
    final a = _analysis!;
    return Container(
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: _riskBgColor,
        borderRadius: BorderRadius.circular(10),
        border: Border.all(color: _riskColor.withOpacity(0.3)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header row
          Row(
            children: [
              Icon(_riskIcon, color: _riskColor, size: 18),
              const SizedBox(width: 8),
              Text(
                'AI Analysis — ${a.riskLabel}',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: _riskColor,
                ),
              ),
              const Spacer(),
              // Risk score gauge
              Container(
                padding: const EdgeInsets.symmetric(
                    horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: _riskColor.withOpacity(0.12),
                  borderRadius: BorderRadius.circular(20),
                ),
                child: Text(
                  'Score: ${a.riskPercent}',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w700,
                    color: _riskColor,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Risk bar
          ClipRRect(
            borderRadius: BorderRadius.circular(4),
            child: LinearProgressIndicator(
              value: a.riskScore.clamp(0.0, 1.0),
              backgroundColor: _riskColor.withOpacity(0.15),
              valueColor: AlwaysStoppedAnimation<Color>(_riskColor),
              minHeight: 6,
            ),
          ),
          const SizedBox(height: 12),

          // Summary
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Icon(
                a.riskLevel == RiskLevel.low
                    ? Icons.check_circle_outline
                    : Icons.info_outline,
                size: 14,
                color: _riskColor,
              ),
              const SizedBox(width: 6),
              Expanded(
                child: Text(
                  a.summary,
                  style: TextStyle(
                    fontSize: 12,
                    color: _riskColor,
                    height: 1.5,
                  ),
                ),
              ),
            ],
          ),

          // Problem section for medium/high risk
          if (a.riskLevel == RiskLevel.medium ||
              a.riskLevel == RiskLevel.high) ...[
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: Colors.white.withOpacity(0.6),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(Icons.warning_amber_rounded,
                      size: 14, color: _riskColor),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          a.riskLevel == RiskLevel.high
                              ? 'Issue detected'
                              : 'Possible concern',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            color: _riskColor,
                          ),
                        ),
                        const SizedBox(height: 3),
                        Text(
                          a.summary,
                          style: TextStyle(
                            fontSize: 11,
                            color: _riskColor.withOpacity(0.85),
                            height: 1.5,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 10),

          // Re-analyse button
          GestureDetector(
            onTap: _runAnalysis,
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.refresh, size: 13, color: _riskColor),
                const SizedBox(width: 4),
                Text(
                  'Re-analyse',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: _riskColor,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
