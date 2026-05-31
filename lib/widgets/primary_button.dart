import 'package:flutter/material.dart';

class PrimaryButton extends StatefulWidget {
  final String label;
  final VoidCallback? onPressed;
  final bool isLoading;
  final bool isDisabled;
  final IconData? icon;
  final Color? backgroundColor;
  final Color? foregroundColor;
  final double? width;

  const PrimaryButton({
    super.key,
    required this.label,
    this.onPressed,
    this.isLoading = false,
    this.isDisabled = false,
    this.icon,
    this.backgroundColor,
    this.foregroundColor,
    this.width,
  });

  @override
  State<PrimaryButton> createState() => _PrimaryButtonState();
}

class _PrimaryButtonState extends State<PrimaryButton> {
  bool _isHovered = false;

  @override
  Widget build(BuildContext context) {
    final isActive = !widget.isDisabled && !widget.isLoading;
    final bgColor = widget.backgroundColor ?? const Color(0xFF1A3A6B);

    return MouseRegion(
      onEnter: (_) => setState(() => _isHovered = true),
      onExit: (_) => setState(() => _isHovered = false),
      cursor: isActive ? SystemMouseCursors.click : SystemMouseCursors.basic,
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: widget.width ?? double.infinity,
        height: 52,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          color: widget.isDisabled
              ? const Color(0xFFCBD5E1)
              : _isHovered && isActive
                  ? bgColor.withOpacity(0.85)
                  : bgColor,
          boxShadow: isActive && _isHovered
              ? [
                  BoxShadow(
                    color: bgColor.withOpacity(0.35),
                    blurRadius: 12,
                    offset: const Offset(0, 4),
                  )
                ]
              : [],
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: isActive ? widget.onPressed : null,
            borderRadius: BorderRadius.circular(8),
            splashColor: Colors.white.withOpacity(0.1),
            child: Center(
              child: widget.isLoading
                  ? const SizedBox(
                      width: 22,
                      height: 22,
                      child: CircularProgressIndicator(
                        strokeWidth: 2.5,
                        valueColor:
                            AlwaysStoppedAnimation<Color>(Colors.white),
                      ),
                    )
                  : Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (widget.icon != null) ...[
                          Icon(
                            widget.icon,
                            color: widget.isDisabled
                                ? const Color(0xFF94A3B8)
                                : (widget.foregroundColor ?? Colors.white),
                            size: 18,
                          ),
                          const SizedBox(width: 8),
                        ],
                        Text(
                          widget.label,
                          style: TextStyle(
                            fontSize: 16,
                            fontWeight: FontWeight.w600,
                            letterSpacing: 0.5,
                            color: widget.isDisabled
                                ? const Color(0xFF94A3B8)
                                : (widget.foregroundColor ?? Colors.white),
                          ),
                        ),
                      ],
                    ),
            ),
          ),
        ),
      ),
    );
  }
}