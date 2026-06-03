import 'package:flutter/material.dart';
import '../../widgets/custom_text_field.dart';
import '../../widgets/primary_button.dart';
import '../../services/auth_service.dart';

class LoginView extends StatefulWidget {
  const LoginView({super.key});

  @override
  State<LoginView> createState() => _LoginViewState();
}

class _LoginViewState extends State<LoginView> {
  final _formKey = GlobalKey<FormState>();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  final _emailFocus = FocusNode();
  final _passwordFocus = FocusNode();
  bool _isLoading = false;
  bool _rememberMe = false;
  String? _errorMessage;

  final _authService = AuthService();

  @override
  void dispose() {
    _emailController.dispose();
    _passwordController.dispose();
    _emailFocus.dispose();
    _passwordFocus.dispose();
    super.dispose();
  }

  Future<void> _handleLogin() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _authService.login(
      LoginRequest(
        email: _emailController.text.trim(),
        password: _passwordController.text,
        rememberMe: _rememberMe,
      ),
    );

    if (!mounted) return;
    setState(() => _isLoading = false);

    if (result.isSuccess) {
      Navigator.pushReplacementNamed(context, '/home');
    } else {
      setState(() => _errorMessage = result.error);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4FA),
      body: SafeArea(
        child: Row(
          children: [
            if (MediaQuery.of(context).size.width > 800)
              Expanded(
                flex: 5,
                child: ClipRect(
                  child: Container(
                    decoration: const BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topLeft,
                        end: Alignment.bottomRight,
                        colors: [
                          Color(0xFF0A1628),
                          Color(0xFF0F2550),
                          Color(0xFF1A3A6B),
                        ],
                      ),
                    ),
                    child: Stack(
                      children: [
                        Positioned(
                          top: -80,
                          right: -80,
                          child: Container(
                            width: 340,
                            height: 340,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color: const Color(0xFF2563EB).withOpacity(0.18),
                            ),
                          ),
                        ),
                        Positioned(
                          bottom: -100,
                          left: -60,
                          child: Container(
                            width: 300,
                            height: 300,
                            decoration: BoxDecoration(
                              shape: BoxShape.circle,
                              color:
                                  const Color(0xFF1D4ED8).withOpacity(0.15),
                            ),
                          ),
                        ),
                        Positioned.fill(
                          child: CustomPaint(painter: _DotGridPainter()),
                        ),
                        Padding(
                          padding: const EdgeInsets.all(48),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              RichText(
                                text: const TextSpan(
                                  children: [
                                    TextSpan(
                                      text: 'SuRaksha',
                                      style: TextStyle(
                                        color: Colors.white,
                                        fontSize: 40,
                                        fontWeight: FontWeight.w900,
                                        letterSpacing: -1,
                                        height: 1.1,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              RichText(
                                text: const TextSpan(
                                  children: [
                                    TextSpan(
                                      text: 'Setu',
                                      style: TextStyle(
                                        color: Color(0xFF60A5FA),
                                        fontSize: 40,
                                        fontWeight: FontWeight.w900,
                                        letterSpacing: -1,
                                        height: 1.1,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(height: 12),
                              Container(
                                width: 52,
                                height: 3,
                                decoration: BoxDecoration(
                                  color: const Color(0xFF60A5FA),
                                  borderRadius: BorderRadius.circular(2),
                                ),
                              ),
                              const SizedBox(height: 18),
                              const Text(
                                'Your trusted bridge to secure\ndigital banking.',
                                style: TextStyle(
                                  color: Color(0xFF93C5FD),
                                  fontSize: 15,
                                  height: 1.7,
                                ),
                              ),
                              const SizedBox(height: 44),
                              const _FeatureBadge(
                                icon: Icons.shield_outlined,
                                text: '256-bit SSL Encryption',
                              ),
                              const SizedBox(height: 14),
                              const _FeatureBadge(
                                icon: Icons.fingerprint,
                                text: 'Biometric Authentication',
                              ),
                              const SizedBox(height: 14),
                              const _FeatureBadge(
                                icon: Icons.verified_user_outlined,
                                text: 'RBI Regulated & Insured',
                              ),
                              const SizedBox(height: 14),
                              const _FeatureBadge(
                                icon: Icons.bolt_outlined,
                                text: 'Instant Transfers & Payments',
                              ),
                              const SizedBox(height: 44),
                              Container(
                                padding: const EdgeInsets.symmetric(
                                    horizontal: 14, vertical: 10),
                                decoration: BoxDecoration(
                                  color: Colors.white.withOpacity(0.07),
                                  borderRadius: BorderRadius.circular(10),
                                  border: Border.all(
                                      color:
                                          Colors.white.withOpacity(0.1)),
                                ),
                                child: const Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    Icon(Icons.lock_outlined,
                                        color: Color(0xFF34D399), size: 14),
                                    SizedBox(width: 8),
                                    Text(
                                      'Protected by AI-powered fraud detection',
                                      style: TextStyle(
                                        color: Color(0xFF6EE7B7),
                                        fontSize: 12,
                                        fontWeight: FontWeight.w500,
                                      ),
                                    ),
                                  ],
                                ),
                              ),
                            ],
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            Expanded(
              flex: 4,
              child: SingleChildScrollView(
                padding: const EdgeInsets.symmetric(
                    horizontal: 32, vertical: 40),
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 420),
                  child: Form(
                    key: _formKey,
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        if (MediaQuery.of(context).size.width <= 800) ...[
                          const Text(
                            'SuRaksha Setu',
                            style: TextStyle(
                              fontSize: 26,
                              fontWeight: FontWeight.w900,
                              color: Color(0xFF1A3A6B),
                              letterSpacing: -0.5,
                            ),
                          ),
                          const SizedBox(height: 24),
                        ],
                        const Text(
                          'Welcome back',
                          style: TextStyle(
                            fontSize: 26,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFF0F172A),
                            letterSpacing: -0.3,
                          ),
                        ),
                        const SizedBox(height: 6),
                        const Text(
                          'Sign in to your account to continue.',
                          style: TextStyle(
                              fontSize: 14, color: Color(0xFF64748B)),
                        ),
                        const SizedBox(height: 32),

                        if (_errorMessage != null) ...[
                          Container(
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
                                    _errorMessage!,
                                    style: const TextStyle(
                                      fontSize: 13,
                                      color: Color(0xFFDC2626),
                                    ),
                                  ),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(height: 20),
                        ],

                        CustomTextField(
                          label: 'Email Address',
                          hint: 'you@example.com',
                          prefixIcon: Icons.email_outlined,
                          controller: _emailController,
                          focusNode: _emailFocus,
                          keyboardType: TextInputType.emailAddress,
                          textInputAction: TextInputAction.next,
                          onSubmitted: (_) => FocusScope.of(context)
                              .requestFocus(_passwordFocus),
                          validator: (v) {
                            if (v == null || v.isEmpty)
                              return 'Email is required';
                            if (!RegExp(
                                    r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$')
                                .hasMatch(v)) {
                              return 'Enter a valid email address';
                            }
                            return null;
                          },
                        ),
                        const SizedBox(height: 20),

                        CustomTextField(
                          label: 'Password',
                          hint: 'Enter your password',
                          prefixIcon: Icons.lock_outline,
                          isPassword: true,
                          controller: _passwordController,
                          focusNode: _passwordFocus,
                          textInputAction: TextInputAction.done,
                          onSubmitted: (_) => _handleLogin(),
                          validator: (v) {
                            if (v == null || v.isEmpty)
                              return 'Password is required';
                            return null;
                          },
                        ),
                        const SizedBox(height: 16),

                        Row(
                          mainAxisAlignment:
                              MainAxisAlignment.spaceBetween,
                          children: [
                            Row(
                              children: [
                                SizedBox(
                                  width: 20,
                                  height: 20,
                                  child: Checkbox(
                                    value: _rememberMe,
                                    onChanged: (v) => setState(
                                        () => _rememberMe = v ?? false),
                                    activeColor: const Color(0xFF1A3A6B),
                                    shape: RoundedRectangleBorder(
                                      borderRadius:
                                          BorderRadius.circular(4),
                                    ),
                                  ),
                                ),
                                const SizedBox(width: 8),
                                const Text(
                                  'Remember me',
                                  style: TextStyle(
                                      fontSize: 13,
                                      color: Color(0xFF475569)),
                                ),
                              ],
                            ),
                            _HoverTextButton(
                              label: 'Forgot password?',
                              onTap: () {},
                            ),
                          ],
                        ),
                        const SizedBox(height: 28),

                        PrimaryButton(
                          label: 'Sign In',
                          onPressed: _handleLogin,
                          isLoading: _isLoading,
                        ),
                        const SizedBox(height: 16),

                        _HoverOutlinedButton(
                          label: 'Sign in with Biometrics',
                          onTap: () {},
                        ),
                        const SizedBox(height: 32),

                        Center(
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Text(
                                'New to SuRaksha Setu? ',
                                style: TextStyle(
                                    fontSize: 14,
                                    color: Color(0xFF64748B)),
                              ),
                              _HoverTextButton(
                                label: 'Open an account',
                                onTap: () => Navigator.pushNamed(
                                    context, '/register'),
                              ),
                            ],
                          ),
                        ),
                        const SizedBox(height: 32),
                        Center(
                          child: Text(
                            '© ${DateTime.now().year} SuRaksha Setu. All rights reserved.',
                            style: TextStyle(
                                fontSize: 12,
                                color: Colors.grey.shade400),
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
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

class _FeatureBadge extends StatelessWidget {
  final IconData icon;
  final String text;
  const _FeatureBadge({required this.icon, required this.text});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          padding: const EdgeInsets.all(8),
          decoration: BoxDecoration(
            color: Colors.white.withOpacity(0.12),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Icon(icon, color: Colors.white, size: 18),
        ),
        const SizedBox(width: 12),
        Text(
          text,
          style: const TextStyle(
              color: Colors.white,
              fontSize: 14,
              fontWeight: FontWeight.w500),
        ),
      ],
    );
  }
}

class _HoverTextButton extends StatefulWidget {
  final String label;
  final VoidCallback onTap;
  const _HoverTextButton({required this.label, required this.onTap});

  @override
  State<_HoverTextButton> createState() => _HoverTextButtonState();
}

class _HoverTextButtonState extends State<_HoverTextButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: GestureDetector(
        onTap: widget.onTap,
        child: AnimatedDefaultTextStyle(
          duration: const Duration(milliseconds: 150),
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: _hovered
                ? const Color(0xFF2563EB)
                : const Color(0xFF1A3A6B),
            decoration:
                _hovered ? TextDecoration.underline : TextDecoration.none,
          ),
          child: Text(widget.label),
        ),
      ),
    );
  }
}

class _HoverOutlinedButton extends StatefulWidget {
  final String label;
  final VoidCallback onTap;
  const _HoverOutlinedButton({required this.label, required this.onTap});

  @override
  State<_HoverOutlinedButton> createState() => _HoverOutlinedButtonState();
}

class _HoverOutlinedButtonState extends State<_HoverOutlinedButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      cursor: SystemMouseCursors.click,
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      child: AnimatedContainer(
        duration: const Duration(milliseconds: 150),
        width: double.infinity,
        height: 52,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(8),
          border: Border.all(
            color: _hovered
                ? const Color(0xFF1A3A6B)
                : const Color(0xFFCBD5E1),
            width: _hovered ? 2 : 1,
          ),
          color:
              _hovered ? const Color(0xFFEEF3FB) : Colors.white,
        ),
        child: Material(
          color: Colors.transparent,
          child: InkWell(
            onTap: widget.onTap,
            borderRadius: BorderRadius.circular(8),
            child: Center(
              child: Text(
                widget.label,
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.w600,
                  color: _hovered
                      ? const Color(0xFF1A3A6B)
                      : const Color(0xFF475569),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}

class _DotGridPainter extends CustomPainter {
  @override
  void paint(Canvas canvas, Size size) {
    final paint = Paint()
      ..color = Colors.white.withOpacity(0.045)
      ..style = PaintingStyle.fill;
    const double spacing = 28;
    const double radius = 1.4;
    for (double x = spacing; x < size.width; x += spacing) {
      for (double y = spacing; y < size.height; y += spacing) {
        canvas.drawCircle(Offset(x, y), radius, paint);
      }
    }
  }

  @override
  bool shouldRepaint(covariant CustomPainter oldDelegate) => false;
}