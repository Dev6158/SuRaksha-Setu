import 'package:flutter/material.dart';
import '../../widgets/custom_text_field.dart';
import '../../widgets/primary_button.dart';
import '../../services/auth_service.dart';

class RegistrationView extends StatefulWidget {
  const RegistrationView({super.key});

  @override
  State<RegistrationView> createState() => _RegistrationViewState();
}

class _RegistrationViewState extends State<RegistrationView> {
  final PageController _pageController = PageController();
  int _currentStep = 0;
  bool _isLoading = false;
  String? _errorMessage;

  // Step 1
  final _firstNameController = TextEditingController();
  final _lastNameController = TextEditingController();
  final _emailController = TextEditingController();
  final _phoneController = TextEditingController();
  final _step1Key = GlobalKey<FormState>();

  // Step 2
  final _passwordController = TextEditingController();
  final _confirmPasswordController = TextEditingController();
  final _step2Key = GlobalKey<FormState>();

  bool _agreedToTerms = false;

  final _authService = AuthService();

  @override
  void dispose() {
    _pageController.dispose();
    _firstNameController.dispose();
    _lastNameController.dispose();
    _emailController.dispose();
    _phoneController.dispose();
    _passwordController.dispose();
    _confirmPasswordController.dispose();
    super.dispose();
  }

  void _nextStep() {
    if (_currentStep == 0 && _step1Key.currentState!.validate()) {
      setState(() => _currentStep = 1);
      _pageController.nextPage(
        duration: const Duration(milliseconds: 300),
        curve: Curves.easeInOut,
      );
    }
  }

  Future<void> _handleRegister() async {
    if (!_step2Key.currentState!.validate()) return;
    if (!_agreedToTerms) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Please agree to the Terms & Conditions to continue.'),
          backgroundColor: Color(0xFFDC2626),
        ),
      );
      return;
    }

    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await _authService.register(
      RegisterRequest(
        firstName: _firstNameController.text.trim(),
        lastName: _lastNameController.text.trim(),
        email: _emailController.text.trim(),
        phone: _phoneController.text.trim(),
        password: _passwordController.text,
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
      appBar: AppBar(
        title: const Text('Open Account'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back),
          onPressed: () {
            if (_currentStep > 0) {
              setState(() => _currentStep--);
              _pageController.previousPage(
                duration: const Duration(milliseconds: 300),
                curve: Curves.easeInOut,
              );
            } else {
              Navigator.pop(context);
            }
          },
        ),
      ),
      body: Column(
        children: [
          // Progress header
          Container(
            color: Colors.white,
            padding:
                const EdgeInsets.symmetric(horizontal: 24, vertical: 20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: List.generate(2, (i) {
                    final isActive = i <= _currentStep;
                    return Expanded(
                      child: Row(
                        children: [
                          _StepIndicator(
                            step: i + 1,
                            isActive: isActive,
                            isDone: i < _currentStep,
                          ),
                          if (i < 1)
                            Expanded(
                              child: Container(
                                height: 2,
                                color: i < _currentStep
                                    ? const Color(0xFF1A3A6B)
                                    : const Color(0xFFCBD5E1),
                              ),
                            ),
                        ],
                      ),
                    );
                  }),
                ),
                const SizedBox(height: 12),
                Text(
                  _currentStep == 0
                      ? 'Personal Information'
                      : 'Security Setup',
                  style: const TextStyle(
                    fontSize: 13,
                    color: Color(0xFF64748B),
                    fontWeight: FontWeight.w500,
                  ),
                ),
              ],
            ),
          ),

          Expanded(
            child: PageView(
              controller: _pageController,
              physics: const NeverScrollableScrollPhysics(),
              children: [
                _buildStep1(),
                _buildStep2(),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep1() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Form(
        key: _step1Key,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Tell us about yourself',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'We need a few details to set up your account.',
              style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 28),

            Row(
              children: [
                Expanded(
                  child: CustomTextField(
                    label: 'First Name',
                    prefixIcon: Icons.person_outline,
                    controller: _firstNameController,
                    validator: (v) =>
                        v == null || v.trim().isEmpty ? 'Required' : null,
                  ),
                ),
                const SizedBox(width: 16),
                Expanded(
                  child: CustomTextField(
                    label: 'Last Name',
                    controller: _lastNameController,
                    validator: (v) =>
                        v == null || v.trim().isEmpty ? 'Required' : null,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 20),

            CustomTextField(
              label: 'Email Address',
              prefixIcon: Icons.email_outlined,
              controller: _emailController,
              keyboardType: TextInputType.emailAddress,
              validator: (v) {
                if (v == null || v.isEmpty) return 'Email is required';
                if (!RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$')
                    .hasMatch(v)) {
                  return 'Enter a valid email address';
                }
                return null;
              },
            ),
            const SizedBox(height: 20),

            CustomTextField(
              label: 'Mobile Number',
              prefixIcon: Icons.phone_outlined,
              controller: _phoneController,
              keyboardType: TextInputType.phone,
              validator: (v) {
                if (v == null || v.isEmpty) return 'Mobile number is required';
                if (v.replaceAll(RegExp(r'[^0-9]'), '').length < 10) {
                  return 'Enter a valid 10-digit number';
                }
                return null;
              },
            ),
            const SizedBox(height: 32),

            PrimaryButton(
              label: 'Continue',
              onPressed: _nextStep,
              icon: Icons.arrow_forward,
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildStep2() {
    return SingleChildScrollView(
      padding: const EdgeInsets.all(24),
      child: Form(
        key: _step2Key,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Create your password',
              style: TextStyle(
                fontSize: 22,
                fontWeight: FontWeight.w700,
                color: Color(0xFF0F172A),
              ),
            ),
            const SizedBox(height: 6),
            const Text(
              'Use a strong password to protect your account.',
              style: TextStyle(fontSize: 14, color: Color(0xFF64748B)),
            ),
            const SizedBox(height: 28),

            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFEFF6FF),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFBFDBFE)),
              ),
              child: const Row(
                children: [
                  Icon(Icons.info_outline,
                      color: Color(0xFF1D4ED8), size: 16),
                  SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      'Minimum 8 characters with uppercase, lowercase, number, and special character.',
                      style: TextStyle(
                          fontSize: 12, color: Color(0xFF1D4ED8)),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            CustomTextField(
              label: 'Password',
              prefixIcon: Icons.lock_outline,
              isPassword: true,
              controller: _passwordController,
              validator: (v) {
                if (v == null || v.isEmpty) return 'Password is required';
                if (v.length < 8) return 'At least 8 characters required';
                if (!RegExp(r'(?=.*[A-Z])').hasMatch(v)) {
                  return 'Include at least one uppercase letter';
                }
                if (!RegExp(r'(?=.*[0-9])').hasMatch(v)) {
                  return 'Include at least one number';
                }
                if (!RegExp(r'(?=.*[!@#\$%^&*])').hasMatch(v)) {
                  return 'Include at least one special character';
                }
                return null;
              },
            ),
            const SizedBox(height: 20),

            CustomTextField(
              label: 'Confirm Password',
              prefixIcon: Icons.lock_outline,
              isPassword: true,
              controller: _confirmPasswordController,
              validator: (v) {
                if (v == null || v.isEmpty)
                  return 'Please confirm your password';
                if (v != _passwordController.text)
                  return 'Passwords do not match';
                return null;
              },
            ),
            const SizedBox(height: 20),

            if (_errorMessage != null) ...[
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF2F2),
                  borderRadius: BorderRadius.circular(8),
                  border:
                      Border.all(color: const Color(0xFFFCA5A5)),
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
                            fontSize: 13, color: Color(0xFFDC2626)),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 20),
            ],

            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFCBD5E1)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  SizedBox(
                    width: 20,
                    height: 20,
                    child: Checkbox(
                      value: _agreedToTerms,
                      onChanged: (v) =>
                          setState(() => _agreedToTerms = v ?? false),
                      activeColor: const Color(0xFF1A3A6B),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(4),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: RichText(
                      text: const TextSpan(
                        style: TextStyle(
                          fontSize: 13,
                          color: Color(0xFF475569),
                          height: 1.5,
                        ),
                        children: [
                          TextSpan(text: 'I agree to the '),
                          TextSpan(
                            text: 'Terms of Service',
                            style: TextStyle(
                              color: Color(0xFF1A3A6B),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          TextSpan(text: ' and '),
                          TextSpan(
                            text: 'Privacy Policy',
                            style: TextStyle(
                              color: Color(0xFF1A3A6B),
                              fontWeight: FontWeight.w600,
                            ),
                          ),
                          TextSpan(
                              text: ' of SuRaksha Setu.'),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            PrimaryButton(
              label: 'Create Account',
              onPressed: _handleRegister,
              isLoading: _isLoading,
              icon: Icons.check_circle_outline,
            ),
            const SizedBox(height: 20),

            Center(
              child: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  const Text(
                    'Already have an account? ',
                    style: TextStyle(
                        fontSize: 14, color: Color(0xFF64748B)),
                  ),
                  GestureDetector(
                    onTap: () => Navigator.pushReplacementNamed(
                        context, '/login'),
                    child: const Text(
                      'Sign In',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF1A3A6B),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StepIndicator extends StatelessWidget {
  final int step;
  final bool isActive;
  final bool isDone;

  const _StepIndicator({
    required this.step,
    required this.isActive,
    required this.isDone,
  });

  @override
  Widget build(BuildContext context) {
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      width: 32,
      height: 32,
      decoration: BoxDecoration(
        shape: BoxShape.circle,
        color: isActive
            ? const Color(0xFF1A3A6B)
            : const Color(0xFFE2E8F0),
        border: Border.all(
          color: isActive
              ? const Color(0xFF1A3A6B)
              : const Color(0xFFCBD5E1),
          width: 2,
        ),
      ),
      child: Center(
        child: isDone
            ? const Icon(Icons.check, color: Colors.white, size: 16)
            : Text(
                '$step',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                  color: isActive
                      ? Colors.white
                      : const Color(0xFF94A3B8),
                ),
              ),
      ),
    );
  }
}