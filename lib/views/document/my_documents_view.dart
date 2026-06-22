import 'package:flutter/material.dart';
import '../../services/document_service.dart';
import '../../widgets/document_card.dart';
import '../../widgets/status_chip.dart';

class MyDocumentsView extends StatefulWidget {
  const MyDocumentsView({super.key});

  @override
  State<MyDocumentsView> createState() => _MyDocumentsViewState();
}

class _MyDocumentsViewState extends State<MyDocumentsView> {
  bool _isLoading = true;
  String? _errorMessage;
  List<UploadedDocument> _documents = [];
  String _filterStatus = 'all';

  final _documentService = DocumentService();

  final List<Map<String, String>> _filters = [
    {'key': 'all', 'label': 'All'},
    {'key': 'pending_review', 'label': 'Pending'},
    {'key': 'approved', 'label': 'Approved'},
    {'key': 'rejected', 'label': 'Rejected'},
  ];

  @override
  void initState() {
    super.initState();
    _loadDocuments();
  }

  Future<void> _loadDocuments() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _documentService.getMyDocuments();

    if (!mounted) return;
    setState(() {
      _isLoading = false;
      if (result.isSuccess) {
        _documents = result.data!;
      } else {
        _errorMessage = result.error;
      }
    });
  }

  List<UploadedDocument> get _filteredDocuments {
  if (_filterStatus == 'all') {
    return _documents;
  }

  return _documents.where((d) {
    final status = d.status.toLowerCase();

    switch (_filterStatus) {
      case 'pending':
        return status.contains('pending');

      case 'approved':
        return status.contains('approved');

      case 'rejected':
        return status.contains('rejected');

      default:
        return true;
    }
  }).toList();
}

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4FA),
      appBar: AppBar(
        title: const Text('My Documents'),
        actions: [
          IconButton(
            icon: const Icon(Icons.upload_file_outlined),
            tooltip: 'Upload new',
            onPressed: () =>
                Navigator.pushNamed(context, '/upload').then((_) {
              _loadDocuments();
            }),
          ),
        ],
      ),
      body: Column(
        children: [
          // Summary strip
          if (!_isLoading && _documents.isNotEmpty)
            Container(
              color: Colors.white,
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
              child: Row(
                children: [
                  _SummaryTile(
                    count: _documents
                        .where((d) => d.status == 'pending_review')
                        .length,
                    label: 'Pending',
                    status: 'pending_review',
                  ),
                  const SizedBox(width: 8),
                  _SummaryTile(
                    count: _documents
                        .where((d) => d.status == 'approved')
                        .length,
                    label: 'Approved',
                    status: 'approved',
                  ),
                  const SizedBox(width: 8),
                  _SummaryTile(
                    count: _documents
                        .where((d) => d.status == 'rejected')
                        .length,
                    label: 'Rejected',
                    status: 'rejected',
                  ),
                ],
              ),
            ),

          // Filter chips
          Container(
            color: Colors.white,
            padding:
                const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Row(
              children: _filters.map((f) {
                final isSelected = _filterStatus == f['key'];
                return Padding(
                  padding: const EdgeInsets.only(right: 8),
                  child: GestureDetector(
                    onTap: () =>
                        setState(() => _filterStatus = f['key']!),
                    child: AnimatedContainer(
                      duration: const Duration(milliseconds: 150),
                      padding: const EdgeInsets.symmetric(
                          horizontal: 14, vertical: 7),
                      decoration: BoxDecoration(
                        color: isSelected
                            ? const Color(0xFF1A3A6B)
                            : const Color(0xFFF1F5F9),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        f['label']!,
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w500,
                          color: isSelected
                              ? Colors.white
                              : const Color(0xFF64748B),
                        ),
                      ),
                    ),
                  ),
                );
              }).toList(),
            ),
          ),

          // AI analysis notice
          Container(
            margin: const EdgeInsets.fromLTRB(16, 12, 16, 0),
            padding: const EdgeInsets.all(12),
            decoration: BoxDecoration(
              color: const Color(0xFFEFF6FF),
              borderRadius: BorderRadius.circular(8),
              border: Border.all(color: const Color(0xFFBFDBFE)),
            ),
            child: const Row(
              children: [
                Icon(Icons.auto_awesome,
                    color: Color(0xFF1D4ED8), size: 16),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'Tap "Analyse" on any document to run AI risk analysis and get a detailed summary.',
                    style: TextStyle(
                        fontSize: 12, color: Color(0xFF1D4ED8)),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 12),

          Expanded(
            child: _isLoading
                ? const Center(
                    child: CircularProgressIndicator(
                      color: Color(0xFF1A3A6B),
                      strokeWidth: 2,
                    ),
                  )
                : _errorMessage != null
                    ? _buildError()
                    : _filteredDocuments.isEmpty
                        ? _buildEmpty()
                        : RefreshIndicator(
                            color: const Color(0xFF1A3A6B),
                            onRefresh: _loadDocuments,
                            child: ListView.separated(
                              padding: const EdgeInsets.fromLTRB(
                                  16, 0, 16, 100),
                              itemCount: _filteredDocuments.length,
                              separatorBuilder: (_, __) =>
                                  const SizedBox(height: 10),
                              itemBuilder: (context, i) {
                                final doc = _filteredDocuments[i];
                                return DocumentCard(
                                  documentId: doc.id,
                                  documentTypeId: '',
                                  fileName: doc.documentName,
                                  status: doc.status,
                                  uploadedAt: doc.uploadedAt,
                                  // fileBytes will be null here since we
                                  // don't cache bytes from the list API.
                                  // The card handles this gracefully by
                                  // showing a re-upload message.
                                  fileBytes: null,
                                );
                              },
                            ),
                          ),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => Navigator.pushNamed(context, '/upload')
            .then((_) => _loadDocuments()),
        backgroundColor: const Color(0xFF1A3A6B),
        icon: const Icon(Icons.add, color: Colors.white),
        label: const Text(
          'Upload Document',
          style: TextStyle(
              color: Colors.white, fontWeight: FontWeight.w600),
        ),
      ),
    );
  }

  Widget _buildError() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline,
                color: Color(0xFFDC2626), size: 48),
            const SizedBox(height: 12),
            Text(
              _errorMessage!,
              textAlign: TextAlign.center,
              style: const TextStyle(
                  fontSize: 14, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              onPressed: _loadDocuments,
              icon: const Icon(Icons.refresh),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1A3A6B),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildEmpty() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                color: Color(0xFFEFF6FF),
                shape: BoxShape.circle,
              ),
              child: const Icon(Icons.folder_open_outlined,
                  color: Color(0xFF1A3A6B), size: 48),
            ),
            const SizedBox(height: 16),
            Text(
              _filterStatus == 'all'
                  ? 'No documents uploaded yet'
                  : 'No ${_filterStatus.replaceAll('_', ' ')} documents',
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.w600,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Upload your documents to get started.',
              style:
                  TextStyle(fontSize: 14, color: Color(0xFF94A3B8)),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              onPressed: () =>
                  Navigator.pushNamed(context, '/upload')
                      .then((_) => _loadDocuments()),
              icon: const Icon(Icons.upload_file_outlined),
              label: const Text('Upload Now'),
              style: ElevatedButton.styleFrom(
                backgroundColor: const Color(0xFF1A3A6B),
                foregroundColor: Colors.white,
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _SummaryTile extends StatelessWidget {
  final int count;
  final String label;
  final String status;

  const _SummaryTile({
    required this.count,
    required this.label,
    required this.status,
  });

  @override
  Widget build(BuildContext context) {
    return Expanded(
      child: Container(
        padding: const EdgeInsets.symmetric(vertical: 10),
        decoration: BoxDecoration(
          color: const Color(0xFFF8FAFF),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: const Color(0xFFE2E8F0)),
        ),
        child: Column(
          children: [
            Text(
              '$count',
              style: const TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 4),
            StatusChip.fromString(status, fontSize: 10),
          ],
        ),
      ),
    );
  }
}
