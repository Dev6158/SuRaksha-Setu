import 'package:flutter/material.dart';

/// A single stat card showing a title, amount, and change percentage.
class StatsCard extends StatelessWidget {
  final String title;
  final String amount;
  final String change;
  final bool isPositive;
  final IconData icon;
  final Color? accentColor;

  const StatsCard({
    super.key,
    required this.title,
    required this.amount,
    required this.change,
    required this.isPositive,
    required this.icon,
    this.accentColor,
  });

  @override
  Widget build(BuildContext context) {
    final color = accentColor ??
        (isPositive ? const Color(0xFF16A34A) : const Color(0xFFDC2626));

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
              Container(
                padding: const EdgeInsets.all(6),
                decoration: BoxDecoration(
                  color: color.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(icon, size: 14, color: color),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Text(
            amount,
            style: const TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const SizedBox(height: 4),
          Row(
            children: [
              Icon(
                isPositive ? Icons.arrow_upward : Icons.arrow_downward,
                size: 12,
                color: color,
              ),
              const SizedBox(width: 3),
              Text(
                '$change this month',
                style: TextStyle(
                  fontSize: 11,
                  color: color,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }
}

/// Income vs Expenses bar chart — pure Flutter, no external chart library.
class IncomeExpenseBarChart extends StatelessWidget {
  final double totalIncome;
  final double totalExpenses;
  final double incomeChangePercent;
  final double expenseChangePercent;

  const IncomeExpenseBarChart({
    super.key,
    required this.totalIncome,
    required this.totalExpenses,
    required this.incomeChangePercent,
    required this.expenseChangePercent,
  });

  @override
  Widget build(BuildContext context) {
    final double maxVal =
        totalIncome > totalExpenses ? totalIncome : totalExpenses;

    return Container(
      padding: const EdgeInsets.all(18),
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
          const Text(
            'Income vs Expenses',
            style: TextStyle(
              fontSize: 14,
              fontWeight: FontWeight.w700,
              color: Color(0xFF0F172A),
            ),
          ),
          const Text(
            'This month',
            style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
          ),
          const SizedBox(height: 20),

          Row(
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              // Income bar
              Expanded(
                child: _Bar(
                  label: 'Income',
                  value: totalIncome,
                  maxValue: maxVal,
                  color: const Color(0xFF16A34A),
                  changePercent: incomeChangePercent,
                ),
              ),
              const SizedBox(width: 16),
              // Expenses bar
              Expanded(
                child: _Bar(
                  label: 'Expenses',
                  value: totalExpenses,
                  maxValue: maxVal,
                  color: const Color(0xFFDC2626),
                  changePercent: expenseChangePercent,
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Legend
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              _LegendDot(color: const Color(0xFF16A34A), label: 'Income'),
              const SizedBox(width: 20),
              _LegendDot(color: const Color(0xFFDC2626), label: 'Expenses'),
            ],
          ),
        ],
      ),
    );
  }
}

class _Bar extends StatelessWidget {
  final String label;
  final double value;
  final double maxValue;
  final Color color;
  final double changePercent;

  const _Bar({
    required this.label,
    required this.value,
    required this.maxValue,
    required this.color,
    required this.changePercent,
  });

  String _formatAmount(double v) {
    if (v >= 100000) return '₹${(v / 100000).toStringAsFixed(1)}L';
    if (v >= 1000) return '₹${(v / 1000).toStringAsFixed(1)}K';
    return '₹${v.toStringAsFixed(0)}';
  }

  @override
  Widget build(BuildContext context) {
    final double ratio = maxValue > 0 ? (value / maxValue).clamp(0.0, 1.0) : 0;
    final bool positive = changePercent >= 0;

    return Column(
      children: [
        Text(
          _formatAmount(value),
          style: TextStyle(
            fontSize: 13,
            fontWeight: FontWeight.w700,
            color: color,
          ),
        ),
        const SizedBox(height: 6),
        LayoutBuilder(builder: (context, constraints) {
          return Container(
            width: constraints.maxWidth,
            height: 120,
            decoration: BoxDecoration(
              color: const Color(0xFFF1F5F9),
              borderRadius: BorderRadius.circular(8),
            ),
            alignment: Alignment.bottomCenter,
            child: AnimatedContainer(
              duration: const Duration(milliseconds: 600),
              curve: Curves.easeOut,
              width: constraints.maxWidth,
              height: 120 * ratio,
              decoration: BoxDecoration(
                color: color,
                borderRadius: BorderRadius.circular(8),
                gradient: LinearGradient(
                  begin: Alignment.topCenter,
                  end: Alignment.bottomCenter,
                  colors: [color.withOpacity(0.7), color],
                ),
              ),
            ),
          );
        }),
        const SizedBox(height: 6),
        Text(
          label,
          style: const TextStyle(
            fontSize: 12,
            color: Color(0xFF64748B),
            fontWeight: FontWeight.w500,
          ),
        ),
        const SizedBox(height: 2),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              positive ? Icons.arrow_upward : Icons.arrow_downward,
              size: 10,
              color: positive ? const Color(0xFF16A34A) : const Color(0xFFDC2626),
            ),
            Text(
              '${changePercent.abs().toStringAsFixed(1)}%',
              style: TextStyle(
                fontSize: 10,
                fontWeight: FontWeight.w600,
                color: positive
                    ? const Color(0xFF16A34A)
                    : const Color(0xFFDC2626),
              ),
            ),
          ],
        ),
      ],
    );
  }
}

class _LegendDot extends StatelessWidget {
  final Color color;
  final String label;
  const _LegendDot({required this.color, required this.label});

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Container(
          width: 10,
          height: 10,
          decoration:
              BoxDecoration(color: color, shape: BoxShape.circle),
        ),
        const SizedBox(width: 5),
        Text(label,
            style: const TextStyle(
                fontSize: 12, color: Color(0xFF64748B))),
      ],
    );
  }
}