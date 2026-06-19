import 'package:flutter/material.dart';

enum ChipStatus { success, pending, failed, approved, rejected, review }

class StatusChip extends StatelessWidget {
  final String label;
  final ChipStatus status;
  final double fontSize;

  const StatusChip({
    super.key,
    required this.label,
    required this.status,
    this.fontSize = 11,
  });

  /// Convenience constructor — derives status from a raw string.
  factory StatusChip.fromString(String raw, {double fontSize = 11}) {
    ChipStatus status;
    switch (raw.toLowerCase().replaceAll('_', '').replaceAll(' ', '')) {
      case 'success':
        status = ChipStatus.success;
        break;
      case 'approved':
        status = ChipStatus.approved;
        break;
      case 'pending':
      case 'pendingreview':
        status = ChipStatus.pending;
        break;
      case 'failed':
        status = ChipStatus.failed;
        break;
      case 'rejected':
        status = ChipStatus.rejected;
        break;
      default:
        status = ChipStatus.review;
    }
    final label = raw
        .replaceAll('_', ' ')
        .split(' ')
        .map((w) => w.isEmpty
            ? ''
            : '${w[0].toUpperCase()}${w.substring(1).toLowerCase()}')
        .join(' ');
    return StatusChip(label: label, status: status, fontSize: fontSize);
  }

  Color get _bgColor {
    switch (status) {
      case ChipStatus.success:
      case ChipStatus.approved:
        return const Color(0xFFDCFCE7);
      case ChipStatus.pending:
      case ChipStatus.review:
        return const Color(0xFFFEF3C7);
      case ChipStatus.failed:
      case ChipStatus.rejected:
        return const Color(0xFFFEE2E2);
    }
  }

  Color get _textColor {
    switch (status) {
      case ChipStatus.success:
      case ChipStatus.approved:
        return const Color(0xFF16A34A);
      case ChipStatus.pending:
      case ChipStatus.review:
        return const Color(0xFFD97706);
      case ChipStatus.failed:
      case ChipStatus.rejected:
        return const Color(0xFFDC2626);
    }
  }

  IconData get _icon {
    switch (status) {
      case ChipStatus.success:
      case ChipStatus.approved:
        return Icons.check_circle_outline;
      case ChipStatus.pending:
      case ChipStatus.review:
        return Icons.schedule_outlined;
      case ChipStatus.failed:
      case ChipStatus.rejected:
        return Icons.cancel_outlined;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: EdgeInsets.symmetric(
          horizontal: fontSize * 0.7, vertical: fontSize * 0.3),
      decoration: BoxDecoration(
        color: _bgColor,
        borderRadius: BorderRadius.circular(20),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(_icon, size: fontSize + 1, color: _textColor),
          SizedBox(width: fontSize * 0.35),
          Text(
            label,
            style: TextStyle(
              fontSize: fontSize,
              fontWeight: FontWeight.w600,
              color: _textColor,
            ),
          ),
        ],
      ),
    );
  }
}