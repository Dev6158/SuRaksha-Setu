import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import '../../widgets/file_preview_card.dart';
import '../../widgets/primary_button.dart';
import '../../services/document_service.dart';

class UploadWizardView extends StatefulWidget {
  const UploadWizardView({super.key});

  @override
  State<UploadWizardView> createState() => _UploadWizardViewState();
}

class _UploadWizardViewState extends State<UploadWizardView> {
  int _currentStep = 0;
  String? _selectedDocTypeId;

  // Each entry: { 'name': ..., 'size': ..., 'bytes': List<int> }
  final List<Map<String, dynamic>> _selectedFiles = [];

  bool _isUploading = false;
  bool _uploadComplete = false;
  bool _isLoadingTypes = true;
  String? _loadError;

  List<DocumentType> _docTypes = [];
  final _documentService = DocumentService();

  @override
  void initState() {
    super.initState();
    _loadDocumentTypes();
  }

  Future<void> _loadDocumentTypes() async {
    setState(() {
      _isLoadingTypes = true;
      _loadError = null;
    });

    final result = await _documentService.getDocumentTypes();

    if (!mounted) return;
    setState(() {
      _isLoadingTypes = false;
      if (result.isSuccess) {
        _docTypes = result.data!;
      } else {
        _loadError = result.error;
      }
    });
  }

  /// Opens the native file picker and reads the file as bytes.
  /// `withData: true` is required for Flutter Web — it loads the file
  /// contents into memory immediately since web has no filesystem path.
  Future<void> _pickFile() async {

    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions:
          _selectedDocType?.acceptedFormats ?? ['pdf', 'jpg', 'jpeg', 'png'],
      withData: true,
    );

    if (result == null || result.files.isEmpty) return;

    final file = result.files.single;
    if (file.bytes == null) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content:
              Text('Could not read the selected file. Please try again.'),
          backgroundColor: Color(0xFFDC2626),
        ),
      );
      return;
    }

    final double sizeMb = file.size / (1024 * 1024);

    setState(() {
      _selectedFiles.add({
        'name': file.name,
        'size': '${sizeMb.toStringAsFixed(1)} MB',
        'bytes': file.bytes!,
      });
    });
  }

  Future<void> _handleUpload() async {
    if (_selectedFiles.isEmpty || _selectedDocTypeId == null) return;
    setState(() => _isUploading = true);

    final file = _selectedFiles.first;
    final result = await _documentService.uploadDocument(
      documentTypeId: _selectedDocTypeId!,
      fileBytes: file['bytes'] as List<int>,
      fileName: file['name'] as String,
    );

    if (!mounted) return;
    setState(() {
      _isUploading = false;
      if (result.isSuccess) {
        _uploadComplete = true;
        _currentStep = 2;
      } else {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(result.error ?? 'Upload failed. Please try again.'),
            backgroundColor: const Color(0xFFDC2626),
          ),
        );
      }
    });
  }

  DocumentType? get _selectedDocType =>
      _docTypes.where((d) => d.id == _selectedDocTypeId).isNotEmpty
          ? _docTypes.firstWhere((d) => d.id == _selectedDocTypeId)
          : null;

  String get _selectedDocLabel => _selectedDocType?.label ?? 'Document';

  IconData _iconForDocType(String id) {
    switch (id) {
      case 'AADHAAR':
        return Icons.credit_card_outlined;
      case 'PAN':
        return Icons.receipt_outlined;
      case 'salary_slip':
        return Icons.request_page_outlined;
      case 'BANK_STATEMENT':
        return Icons.account_balance_outlined;
      case 'passport':
        return Icons.menu_book_outlined;
      case 'utility_bill':
        return Icons.home_outlined;
      default:
        return Icons.description_outlined;
    }
  }

  Color _colorForDocType(String id) {
    switch (id) {
      case 'aadhaar':
        return const Color(0xFF1A3A6B);
      case 'pan':
        return const Color(0xFF7C3AED);
      case 'salary_slip':
        return const Color(0xFF059669);
      case 'bank_statement':
        return const Color(0xFF0891B2);
      case 'passport':
        return const Color(0xFFD97706);
      case 'utility_bill':
        return const Color(0xFFDC2626);
      default:
        return const Color(0xFF1A3A6B);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4FA),
      appBar: AppBar(
        title: const Text('Document Upload'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (_currentStep > 0 && !_uploadComplete) {
              setState(() {
                _currentStep--;
                if (_currentStep == 0) _selectedFiles.clear();
              });
            } else {
              Navigator.pop(context);
            }
          },
        ),
        actions: [
          TextButton.icon(
            onPressed: () => Navigator.pop(context),
            icon: const Icon(Icons.close, size: 18),
            label: const Text('Cancel'),
            style: TextButton.styleFrom(foregroundColor: Colors.white70),
          ),
        ],
      ),
      body: Column(
        children: [
          if (!_uploadComplete)
            Container(
              color: Colors.white,
              padding:
                  const EdgeInsets.symmetric(horizontal: 24, vertical: 16),
              child: Column(
                children: [
                  Row(
                    children: List.generate(3, (i) {
                      final isActive = i <= _currentStep;
                      final isDone = i < _currentStep;
                      return Expanded(
                        child: Row(
                          children: [
                            _StepDot(
                                step: i + 1,
                                isActive: isActive,
                                isDone: isDone),
                            if (i < 2)
                              Expanded(
                                child: AnimatedContainer(
                                  duration: const Duration(milliseconds: 300),
                                  height: 2,
                                  color: isDone
                                      ? const Color(0xFF1A3A6B)
                                      : const Color(0xFFCBD5E1),
                                ),
                              ),
                          ],
                        ),
                      );
                    }),
                  ),
                  const SizedBox(height: 10),
                  const Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text('Select Type',
                          style: TextStyle(
                              fontSize: 11, color: Color(0xFF64748B))),
                      Text('Choose File',
                          style: TextStyle(
                              fontSize: 11, color: Color(0xFF64748B))),
                      Text('Upload',
                          style: TextStyle(
                              fontSize: 11, color: Color(0xFF64748B))),
                    ],
                  ),
                ],
              ),
            ),

          Expanded(
            child: _uploadComplete
                ? _buildSuccessState()
                : _currentStep == 0
                    ? _buildSelectTypeStep()
                    : _buildUploadStep(),
          ),
        ],
      ),
    );
  }

  Widget _buildSelectTypeStep() {
    if (_isLoadingTypes) {
      return const Center(
        child: CircularProgressIndicator(
          color: Color(0xFF1A3A6B),
          strokeWidth: 2,
        ),
      );
    }

    if (_loadError != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(32),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline,
                  color: Color(0xFFDC2626), size: 40),
              const SizedBox(height: 12),
              Text(
                _loadError!,
                textAlign: TextAlign.center,
                style: const TextStyle(color: Color(0xFF64748B)),
              ),
              const SizedBox(height: 20),
              PrimaryButton(
                label: 'Retry',
                onPressed: _loadDocumentTypes,
                width: 140,
                icon: Icons.refresh,
              ),
            ],
          ),
        ),
      );
    }

    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Text(
            'Select Document Type',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'Choose the type of document you want to upload.',
            style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
          ),
          const SizedBox(height: 20),

          GridView.builder(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
              crossAxisCount: 2,
              crossAxisSpacing: 12,
              mainAxisSpacing: 12,
              childAspectRatio: 1.4,
            ),
            itemCount: _docTypes.length,
            itemBuilder: (context, i) {
              final doc = _docTypes[i];
              final isSelected = _selectedDocTypeId == doc.id;

              return _DocTypeCard(
                icon: _iconForDocType(doc.id),
                label: doc.label,
                subtitle: doc.subtitle,
                color: _colorForDocType(doc.id),
                isRequired: doc.isRequired,
                isSelected: isSelected,
                onTap: () =>
                    setState(() => _selectedDocTypeId = doc.id),
              );
            },
          ),
          const SizedBox(height: 24),

          PrimaryButton(
            label: 'Continue',
            onPressed: _selectedDocTypeId == null
                ? null
                : () => setState(() => _currentStep = 1),
            isDisabled: _selectedDocTypeId == null,
            icon: Icons.arrow_forward,
          ),
        ],
      ),
    );
  }

  Widget _buildUploadStep() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(20),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            padding:
                const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
            decoration: BoxDecoration(
              color: const Color(0xFFEFF6FF),
              borderRadius: BorderRadius.circular(20),
              border: Border.all(color: const Color(0xFFBFDBFE)),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Icon(Icons.check_circle,
                    color: Color(0xFF1D4ED8), size: 14),
                const SizedBox(width: 6),
                Text(
                  _selectedDocLabel,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF1D4ED8),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          const Text(
            'Upload your file',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'Supported formats: ${_selectedDocType?.acceptedFormats.join(', ').toUpperCase() ?? 'PDF, JPG, PNG'}. Max size: ${_selectedDocType?.maxSizeMb ?? 10} MB.',
            style:
                const TextStyle(fontSize: 14, color: Color(0xFF64748B)),
          ),
          const SizedBox(height: 20),

          _selectedFiles.isEmpty
              ? _DropZone(onTap: _pickFile)
              : Column(
                  children: [
                    ..._selectedFiles.map(
                      (f) => Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: FilePreviewCard(
                          fileName: f['name'] as String,
                          fileSize: f['size'] as String,
                          documentType: _selectedDocLabel,
                          onRemove: () =>
                              setState(() => _selectedFiles.remove(f)),
                        ),
                      ),
                    ),
                    const SizedBox(height: 8),
                    _AddMoreButton(onTap: _pickFile),
                  ],
                ),
          const SizedBox(height: 20),

          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: const Color(0xFFFFFBEB),
              borderRadius: BorderRadius.circular(10),
              border: Border.all(color: const Color(0xFFFDE68A)),
            ),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.lightbulb_outline,
                        color: Color(0xFFD97706), size: 16),
                    SizedBox(width: 6),
                    Text(
                      'Upload Guidelines',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: Color(0xFFD97706),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                ...[
                  'Document must be clearly visible and not blurred',
                  'All four corners of the document must be visible',
                  'File size should not exceed ${_selectedDocType?.maxSizeMb ?? 10} MB',
                  'Password-protected PDFs are not accepted',
                ].map(
                  (tip) => Padding(
                    padding: const EdgeInsets.only(bottom: 5),
                    child: Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text('• ',
                            style: TextStyle(
                                color: Color(0xFFB45309), fontSize: 12)),
                        Expanded(
                          child: Text(
                            tip,
                            style: const TextStyle(
                              fontSize: 12,
                              color: Color(0xFFB45309),
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 24),

          PrimaryButton(
            label: _isUploading ? 'Uploading...' : 'Upload Document',
            onPressed: _selectedFiles.isEmpty ? null : _handleUpload,
            isLoading: _isUploading,
            isDisabled: _selectedFiles.isEmpty,
            icon: _isUploading ? null : Icons.cloud_upload_outlined,
          ),
        ],
      ),
    );
  }

  Widget _buildSuccessState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: const BoxDecoration(
                color: Color(0xFFDCFCE7),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.check_circle_outline,
                color: Color(0xFF16A34A),
                size: 64,
              ),
            ),
            const SizedBox(height: 24),
            const Text(
              'Upload Successful',
              style: TextStyle(
                fontSize: 24,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 10),
            Text(
              '$_selectedDocLabel has been submitted for verification.',
              textAlign: TextAlign.center,
              style: const TextStyle(
                  fontSize: 15, color: Color(0xFF64748B), height: 1.5),
            ),
            const SizedBox(height: 8),
            const Text(
              'Our team will review it within 24–48 business hours.',
              textAlign: TextAlign.center,
              style: TextStyle(
                  fontSize: 14, color: Color(0xFF94A3B8), height: 1.5),
            ),
            const SizedBox(height: 36),

            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.schedule_outlined,
                      color: Color(0xFF64748B), size: 18),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Estimated verification time',
                      style: TextStyle(
                          fontSize: 13, color: Color(0xFF64748B)),
                    ),
                  ),
                  Text(
                    '24–48 hrs',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF1A3A6B),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 32),

            PrimaryButton(
              label: 'Upload Another Document',
              onPressed: () => setState(() {
                _currentStep = 0;
                _selectedDocTypeId = null;
                _selectedFiles.clear();
                _uploadComplete = false;
              }),
              icon: Icons.upload_file_outlined,
            ),
            const SizedBox(height: 14),
            TextButton(
              onPressed: () => Navigator.pop(context),
              style: TextButton.styleFrom(
                foregroundColor: const Color(0xFF64748B),
              ),
              child: const Text(
                'Back to Dashboard',
                style:
                    TextStyle(fontSize: 15, fontWeight: FontWeight.w500),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------------------
// Helper widgets
// ---------------------------------------------------------------------------

class _StepDot extends StatelessWidget {
  final int step;
  final bool isActive;
  final bool isDone;

  const _StepDot(
      {required this.step, required this.isActive, required this.isDone});

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      width: 28,
      height: 28,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color:
            isActive ? const Color(0xFF1A3A6B) : const Color(0xFFE2E8F0),
      ),
      child: Center(
        child: isDone
            ? const Icon(Icons.check, color: Colors.white, size: 14)
            : Text(
                '$step',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  color:
                      isActive ? Colors.white : const Color(0xFF94A3B8),
                ),
              ),
      ),
    );
  }
}

class _DocTypeCard extends StatefulWidget {
  final IconData icon;
  final String label;
  final String subtitle;
  final Color color;
  final bool isRequired;
  final bool isSelected;
  final VoidCallback onTap;

  const _DocTypeCard({
    required this.icon,
    required this.label,
    required this.subtitle,
    required this.color,
    required this.isRequired,
    required this.isSelected,
    required this.onTap,
  });

  @override
  State<_DocTypeCard> createState() => _DocTypeCardState();
}

class _DocTypeCardState extends State<_DocTypeCard> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: widget.isSelected
                ? const Color(0xFFEFF6FF)
                : _hovered
                    ? const Color(0xFFF8FAFF)
                    : Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: widget.isSelected
                  ? const Color(0xFF1A3A6B)
                  : _hovered
                      ? const Color(0xFF1A3A6B).withOpacity(0.3)
                      : const Color(0xFFE2E8F0),
              width: widget.isSelected ? 2 : 1,
            ),
            boxShadow: widget.isSelected || _hovered
                ? [
                    BoxShadow(
                      color:
                          const Color(0xFF1A3A6B).withOpacity(0.08),
                      blurRadius: 10,
                      offset: const Offset(0, 3),
                    )
                  ]
                : [],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Icon(widget.icon, color: widget.color, size: 24),
                  if (widget.isRequired)
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 5, vertical: 2),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFEE2E2),
                        borderRadius: BorderRadius.circular(4),
                      ),
                      child: const Text(
                        'Required',
                        style: TextStyle(
                          fontSize: 9,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFFDC2626),
                        ),
                      ),
                    ),
                  if (widget.isSelected)
                    const Icon(Icons.check_circle,
                        color: Color(0xFF1A3A6B), size: 16),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                widget.label,
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: widget.isSelected
                      ? const Color(0xFF1A3A6B)
                      : const Color(0xFF0F172A),
                ),
              ),
              const SizedBox(height: 2),
              Text(
                widget.subtitle,
                style: const TextStyle(
                  fontSize: 10,
                  color: Color(0xFF94A3B8),
                ),
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _DropZone extends StatefulWidget {
  final VoidCallback onTap;
  const _DropZone({required this.onTap});

  @override
  State<_DropZone> createState() => _DropZoneState();
}

class _DropZoneState extends State<_DropZone> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          width: double.infinity,
          padding:
              const EdgeInsets.symmetric(vertical: 40, horizontal: 24),
          decoration: BoxDecoration(
            color: _hovered
                ? const Color(0xFFEFF6FF)
                : const Color(0xFFF8FAFF),
            borderRadius: BorderRadius.circular(12),
            border: Border.all(
              color: _hovered
                  ? const Color(0xFF1A3A6B)
                  : const Color(0xFFCBD5E1),
              width: 2,
            ),
          ),
          child: Column(
            children: [
              AnimatedContainer(
                duration: const Duration(milliseconds: 150),
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: _hovered
                      ? const Color(0xFF1A3A6B).withOpacity(0.1)
                      : const Color(0xFFE2E8F0),
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.cloud_upload_outlined,
                  color: _hovered
                      ? const Color(0xFF1A3A6B)
                      : const Color(0xFF94A3B8),
                  size: 36,
                ),
              ),
              const SizedBox(height: 14),
              Text(
                _hovered ? 'Click to browse files' : 'Tap or click to upload',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: _hovered
                      ? const Color(0xFF1A3A6B)
                      : const Color(0xFF475569),
                ),
              ),
              const SizedBox(height: 6),
              const Text(
                'PDF, JPG, or PNG — max 10 MB',
                style:
                    TextStyle(fontSize: 13, color: Color(0xFF94A3B8)),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _AddMoreButton extends StatefulWidget {
  final VoidCallback onTap;
  const _AddMoreButton({required this.onTap});

  @override
  State<_AddMoreButton> createState() => _AddMoreButtonState();
}

class _AddMoreButtonState extends State<_AddMoreButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          padding: const EdgeInsets.symmetric(vertical: 12),
          decoration: BoxDecoration(
            color: _hovered
                ? const Color(0xFFEFF6FF)
                : Colors.transparent,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(
              color: _hovered
                  ? const Color(0xFF1A3A6B).withOpacity(0.3)
                  : const Color(0xFFCBD5E1),
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.add_circle_outline,
                size: 18,
                color: _hovered
                    ? const Color(0xFF1A3A6B)
                    : const Color(0xFF94A3B8),
              ),
              const SizedBox(width: 8),
              Text(
                'Add another file',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w500,
                  color: _hovered
                      ? const Color(0xFF1A3A6B)
                      : const Color(0xFF64748B),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
