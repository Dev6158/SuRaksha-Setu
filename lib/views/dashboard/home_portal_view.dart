import 'package:flutter/material.dart';
import '../../widgets/transaction_card.dart';
import '../../services/dashboard_service.dart';
import '../../services/api_service.dart';

class HomePortalView extends StatefulWidget {
  const HomePortalView({super.key});

  @override
  State<HomePortalView> createState() => _HomePortalViewState();
}

class _HomePortalViewState extends State<HomePortalView> {
  int _selectedIndex = 0;
  bool _balanceVisible = true;
  bool _isLoading = true;
  String? _errorMessage;

  AccountSummary? _account;
  List<Transaction> _transactions = [];
  MonthlyStats? _stats;

  final _dashboardService = DashboardService();

  final List<Map<String, dynamic>> _quickActions = [
    {'icon': Icons.send_outlined, 'label': 'Transfer', 'color': Color(0xFF2563EB)},
    {'icon': Icons.qr_code_scanner_outlined, 'label': 'Pay', 'color': Color(0xFF7C3AED)},
    {'icon': Icons.receipt_long_outlined, 'label': 'History', 'color': Color(0xFF0891B2)},
    {'icon': Icons.upload_file_outlined, 'label': 'Documents', 'color': Color(0xFF059669)},
  ];

  @override
  void initState() {
    super.initState();
    _loadDashboard();
  }

  Future<void> _loadDashboard() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final results = await Future.wait([
      _dashboardService.getAccountSummary(),
      _dashboardService.getRecentTransactions(),
      _dashboardService.getMonthlyStats(),
    ]);

    if (!mounted) return;

    final accountRes = results[0] as ApiResponse<AccountSummary>;
    final txRes = results[1] as ApiResponse<List<Transaction>>;
    final statsRes = results[2] as ApiResponse<MonthlyStats>;

    setState(() {
      _isLoading = false;
      if (accountRes.isSuccess) _account = accountRes.data;
      if (txRes.isSuccess) _transactions = txRes.data!;
      if (statsRes.isSuccess) _stats = statsRes.data;
      if (!accountRes.isSuccess) _errorMessage = accountRes.error;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: const Color(0xFFF0F4FA),
      body: SafeArea(
        child: IndexedStack(
          index: _selectedIndex,
          children: [
            _buildDashboard(),
            _buildPlaceholder('Payments', Icons.payment_outlined),
            _buildPlaceholder('Cards', Icons.credit_card_outlined),
            _buildPlaceholder('Profile', Icons.person_outline),
          ],
        ),
      ),
      bottomNavigationBar: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF1A3A6B).withOpacity(0.08),
              blurRadius: 16,
              offset: const Offset(0, -4),
            ),
          ],
        ),
        child: BottomNavigationBar(
          currentIndex: _selectedIndex,
          onTap: (i) {
            if (i == 3) {
              Navigator.pushNamed(context, '/upload');
              return;
            }
            setState(() => _selectedIndex = i);
          },
          type: BottomNavigationBarType.fixed,
          backgroundColor: Colors.white,
          selectedItemColor: const Color(0xFF1A3A6B),
          unselectedItemColor: const Color(0xFF94A3B8),
          selectedLabelStyle:
              const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
          unselectedLabelStyle: const TextStyle(fontSize: 11),
          elevation: 0,
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.home_outlined),
              activeIcon: Icon(Icons.home),
              label: 'Home',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.payment_outlined),
              activeIcon: Icon(Icons.payment),
              label: 'Pay',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.credit_card_outlined),
              activeIcon: Icon(Icons.credit_card),
              label: 'Cards',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.person_outline),
              activeIcon: Icon(Icons.person),
              label: 'Profile',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDashboard() {
    return RefreshIndicator(
      color: const Color(0xFF1A3A6B),
      onRefresh: _loadDashboard,
      child: SingleChildScrollView(
        physics: const AlwaysScrollableScrollPhysics(),
        child: Column(
          children: [
            // Header
            Container(
              decoration: const BoxDecoration(
                gradient: LinearGradient(
                  begin: Alignment.topLeft,
                  end: Alignment.bottomRight,
                  colors: [Color(0xFF0F2550), Color(0xFF1A3A6B)],
                ),
              ),
              padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
              child: Column(
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text(
                            'Good morning,',
                            style: TextStyle(
                                color: Color(0xFFBDD3F5), fontSize: 13),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            _account?.displayName ?? '...',
                            style: const TextStyle(
                              color: Colors.white,
                              fontSize: 20,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ),
                      Row(
                        children: [
                          _IconHeaderButton(
                            icon: Icons.notifications_outlined,
                            badge: (_account?.unreadNotifications ?? 0) > 0,
                            onTap: () {},
                          ),
                          const SizedBox(width: 12),
                          GestureDetector(
                            onTap: () {},
                            child: CircleAvatar(
                              radius: 20,
                              backgroundColor: const Color(0xFF2563EB),
                              child: Text(
                                _account?.avatarInitials ?? '...',
                                style: const TextStyle(
                                  color: Colors.white,
                                  fontSize: 14,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                  const SizedBox(height: 28),

                  // Balance card
                  Container(
                    padding: const EdgeInsets.all(20),
                    decoration: BoxDecoration(
                      color: Colors.white.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(16),
                      border:
                          Border.all(color: Colors.white.withOpacity(0.15)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Row(
                          mainAxisAlignment: MainAxisAlignment.spaceBetween,
                          children: [
                            const Text(
                              'Available Balance',
                              style: TextStyle(
                                  color: Color(0xFFBDD3F5), fontSize: 13),
                            ),
                            GestureDetector(
                              onTap: () => setState(
                                  () => _balanceVisible = !_balanceVisible),
                              child: Icon(
                                _balanceVisible
                                    ? Icons.visibility_outlined
                                    : Icons.visibility_off_outlined,
                                color: const Color(0xFFBDD3F5),
                                size: 18,
                              ),
                            ),
                          ],
                        ),
                        const SizedBox(height: 8),
                        AnimatedSwitcher(
                          duration: const Duration(milliseconds: 300),
                          child: _balanceVisible
                              ? Text(
                                  _account != null
                                      ? '₹${_account!.availableBalance.toStringAsFixed(2)}'
                                      : '...',
                                  key: const ValueKey('visible'),
                                  style: const TextStyle(
                                    color: Colors.white,
                                    fontSize: 32,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: -0.5,
                                  ),
                                )
                              : const Text(
                                  '₹ ••••••••',
                                  key: ValueKey('hidden'),
                                  style: TextStyle(
                                    color: Colors.white,
                                    fontSize: 32,
                                    fontWeight: FontWeight.w800,
                                    letterSpacing: 2,
                                  ),
                                ),
                        ),
                        const SizedBox(height: 16),
                        Row(
                          children: [
                            const Icon(Icons.credit_card,
                                color: Color(0xFFBDD3F5), size: 14),
                            const SizedBox(width: 6),
                            Text(
                              _account?.maskedAccountNumber ??
                                  '---- ---- ---- ----',
                              style: const TextStyle(
                                color: Color(0xFFBDD3F5),
                                fontSize: 13,
                                letterSpacing: 1,
                              ),
                            ),
                            const Spacer(),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: const Color(0xFF16A34A).withOpacity(0.2),
                                borderRadius: BorderRadius.circular(20),
                                border: Border.all(
                                    color: const Color(0xFF16A34A)
                                        .withOpacity(0.4)),
                              ),
                              child: const Text(
                                '● Active',
                                style: TextStyle(
                                    color: Color(0xFF4ADE80),
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),

            // Content below gradient
            Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Security banner
                  Container(
                    padding: const EdgeInsets.all(14),
                    decoration: BoxDecoration(
                      color: const Color(0xFFEFF6FF),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFFBFDBFE)),
                    ),
                    child: Row(
                      children: [
                        const Icon(Icons.verified_user,
                            color: Color(0xFF1D4ED8), size: 18),
                        const SizedBox(width: 10),
                        const Expanded(
                          child: Text(
                            'Your account is fully secured. Risk level: Low',
                            style: TextStyle(
                              fontSize: 13,
                              color: Color(0xFF1D4ED8),
                              fontWeight: FontWeight.w500,
                            ),
                          ),
                        ),
                        const Icon(Icons.chevron_right,
                            color: Color(0xFF1D4ED8), size: 16),
                      ],
                    ),
                  ),
                  const SizedBox(height: 24),

                  // Quick actions
                  const Text(
                    'Quick Actions',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF0F172A),
                    ),
                  ),
                  const SizedBox(height: 14),

                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: _quickActions.map((action) {
                      return _QuickActionButton(
                        icon: action['icon'] as IconData,
                        label: action['label'] as String,
                        color: action['color'] as Color,
                        onTap: action['label'] == 'Documents'
                            ? () => Navigator.pushNamed(context, '/upload')
                            : () {},
                      );
                    }).toList(),
                  ),
                  const SizedBox(height: 24),

                  // Stats row
                  Row(
                    children: [
                      Expanded(
                        child: _StatCard(
                          title: 'Income',
                          amount: _stats != null
                              ? '₹${_stats!.totalIncome.toStringAsFixed(0)}'
                              : '--',
                          change: _stats != null
                              ? '${_stats!.incomeChangePercent > 0 ? '+' : ''}${_stats!.incomeChangePercent.toStringAsFixed(1)}%'
                              : '--',
                          isPositive:
                              (_stats?.incomeChangePercent ?? 0) >= 0,
                          icon: Icons.trending_up,
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: _StatCard(
                          title: 'Expenses',
                          amount: _stats != null
                              ? '₹${_stats!.totalExpenses.toStringAsFixed(0)}'
                              : '--',
                          change: _stats != null
                              ? '${_stats!.expenseChangePercent > 0 ? '+' : ''}${_stats!.expenseChangePercent.toStringAsFixed(1)}%'
                              : '--',
                          isPositive:
                              (_stats?.expenseChangePercent ?? 0) <= 0,
                          icon: Icons.trending_down,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 24),

                  // Recent transactions
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Recent Transactions',
                        style: TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF0F172A),
                        ),
                      ),
                      TextButton(
                        onPressed: () {},
                        style: TextButton.styleFrom(
                          foregroundColor: const Color(0xFF1A3A6B),
                          padding: EdgeInsets.zero,
                        ),
                        child: const Text(
                          'See All',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),

                  Container(
                    decoration: BoxDecoration(
                      color: Colors.white,
                      borderRadius: BorderRadius.circular(12),
                      boxShadow: [
                        BoxShadow(
                          color: const Color(0xFF1A3A6B).withOpacity(0.06),
                          blurRadius: 12,
                          offset: const Offset(0, 2),
                        ),
                      ],
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(12),
                      child: Column(
                        children: [
                          if (_isLoading)
                            const Padding(
                              padding: EdgeInsets.all(24),
                              child: Center(
                                child: CircularProgressIndicator(
                                  color: Color(0xFF1A3A6B),
                                  strokeWidth: 2,
                                ),
                              ),
                            )
                          else if (_errorMessage != null)
                            Padding(
                              padding: const EdgeInsets.all(24),
                              child: Center(
                                child: Text(
                                  _errorMessage!,
                                  style: const TextStyle(
                                      fontSize: 14,
                                      color: Color(0xFFDC2626)),
                                  textAlign: TextAlign.center,
                                ),
                              ),
                            )
                          else if (_transactions.isEmpty)
                            const Padding(
                              padding: EdgeInsets.all(24),
                              child: Center(
                                child: Text(
                                  'No recent transactions',
                                  style: TextStyle(
                                      fontSize: 14,
                                      color: Color(0xFF94A3B8)),
                                ),
                              ),
                            )
                          else
                            ..._transactions
                                .map((tx) => TransactionCard(transaction: tx))
                                .toList(),
                        ],
                      ),
                    ),
                  ),
                  const SizedBox(height: 20),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildPlaceholder(String title, IconData icon) {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(icon, size: 64, color: const Color(0xFFCBD5E1)),
          const SizedBox(height: 16),
          Text(
            title,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w600,
              color: Color(0xFF94A3B8),
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Coming soon',
            style: TextStyle(fontSize: 14, color: Color(0xFFCBD5E1)),
          ),
        ],
      ),
    );
  }
}

class _IconHeaderButton extends StatelessWidget {
  final IconData icon;
  final bool badge;
  final VoidCallback onTap;

  const _IconHeaderButton({
    required this.icon,
    required this.onTap,
    this.badge = false,
  });

  @override
  Widget build(BuildContext context) {
    return GestureDetector(
      onTap: onTap,
      child: Stack(
        children: [
          Container(
            padding: const EdgeInsets.all(8),
            decoration: BoxDecoration(
              color: Colors.white.withOpacity(0.12),
              borderRadius: BorderRadius.circular(10),
            ),
            child: Icon(icon, color: Colors.white, size: 22),
          ),
          if (badge)
            Positioned(
              top: 4,
              right: 4,
              child: Container(
                width: 8,
                height: 8,
                decoration: const BoxDecoration(
                  color: Color(0xFFFCA5A5),
                  shape: BoxShape.circle,
                ),
              ),
            ),
        ],
      ),
    );
  }
}

class _QuickActionButton extends StatefulWidget {
  final IconData icon;
  final String label;
  final Color color;
  final VoidCallback onTap;

  const _QuickActionButton({
    required this.icon,
    required this.label,
    required this.color,
    required this.onTap,
  });

  @override
  State<_QuickActionButton> createState() => _QuickActionButtonState();
}

class _QuickActionButtonState extends State<_QuickActionButton> {
  bool _hovered = false;

  @override
  Widget build(BuildContext context) {
    return MouseRegion(
      onEnter: (_) => setState(() => _hovered = true),
      onExit: (_) => setState(() => _hovered = false),
      cursor: SystemMouseCursors.click,
      child: GestureDetector(
        onTap: widget.onTap,
        child: Column(
          children: [
            AnimatedContainer(
              duration: const Duration(milliseconds: 150),
              width: 60,
              height: 60,
              decoration: BoxDecoration(
                color: _hovered
                    ? widget.color.withOpacity(0.15)
                    : widget.color.withOpacity(0.08),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: _hovered
                      ? widget.color.withOpacity(0.5)
                      : widget.color.withOpacity(0.15),
                ),
                boxShadow: _hovered
                    ? [
                        BoxShadow(
                          color: widget.color.withOpacity(0.2),
                          blurRadius: 12,
                          offset: const Offset(0, 4),
                        )
                      ]
                    : [],
              ),
              child: Icon(widget.icon, color: widget.color, size: 24),
            ),
            const SizedBox(height: 8),
            Text(
              widget.label,
              style: const TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w500,
                color: Color(0xFF475569),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String title;
  final String amount;
  final String change;
  final bool isPositive;
  final IconData icon;

  const _StatCard({
    required this.title,
    required this.amount,
    required this.change,
    required this.isPositive,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        boxShadow: [
          BoxShadow(
            color: const Color(0xFF1A3A6B).withOpacity(0.06),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(
                    fontSize: 13, color: Color(0xFF64748B)),
              ),
              Icon(
                icon,
                size: 16,
                color: isPositive
                    ? const Color(0xFF16A34A)
                    : const Color(0xFFDC2626),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            amount,
            style: const TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 4),
          Text(
            '$change this month',
            style: TextStyle(
              fontSize: 11,
              color: isPositive
                  ? const Color(0xFF16A34A)
                  : const Color(0xFFDC2626),
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
  }
}