import 'api_service.dart';

// ---------------------------------------------------------------------------
// Models
// ---------------------------------------------------------------------------

class AccountSummary {
  final String accountId;
  final String displayName;
  final String maskedAccountNumber;
  final double availableBalance;
  final double ledgerBalance;
  final String accountType;
  final String ifscCode;
  final int unreadNotifications;
  final String avatarInitials;

  const AccountSummary({
    required this.accountId,
    required this.displayName,
    required this.maskedAccountNumber,
    required this.availableBalance,
    required this.ledgerBalance,
    required this.accountType,
    required this.ifscCode,
    required this.unreadNotifications,
    required this.avatarInitials,
  });

  factory AccountSummary.fromJson(Map<String, dynamic> json) => AccountSummary(
        accountId: json['account_id'] as String,
        displayName: json['display_name'] as String,
        maskedAccountNumber: json['masked_account_number'] as String,
        availableBalance: (json['available_balance'] as num).toDouble(),
        ledgerBalance: (json['ledger_balance'] as num).toDouble(),
        accountType: json['account_type'] as String,
        ifscCode: json['ifsc_code'] as String,
        unreadNotifications: json['unread_notifications'] as int? ?? 0,
        avatarInitials: json['avatar_initials'] as String,
      );
}

enum TransactionType { credit, debit }

enum TransactionStatus { success, pending, failed }

class Transaction {
  final String id;
  final String title;
  final String subtitle;
  final double amount;
  final TransactionType type;
  final TransactionStatus status;
  final DateTime date;
  final String category;
  final String? utrNumber;

  const Transaction({
    required this.id,
    required this.title,
    required this.subtitle,
    required this.amount,
    required this.type,
    required this.status,
    required this.date,
    required this.category,
    this.utrNumber,
  });

  bool get isCredit => type == TransactionType.credit;

  factory Transaction.fromJson(Map<String, dynamic> json) => Transaction(
        id: json['id'] as String,
        title: json['title'] as String,
        subtitle: json['subtitle'] as String,
        amount: (json['amount'] as num).toDouble(),
        type: json['type'] == 'credit'
            ? TransactionType.credit
            : TransactionType.debit,
        status: _parseStatus(json['status'] as String),
        date: DateTime.parse(json['date'] as String),
        category: json['category'] as String,
        utrNumber: json['utr_number'] as String?,
      );

  static TransactionStatus _parseStatus(String s) {
    switch (s) {
      case 'success':
        return TransactionStatus.success;
      case 'pending':
        return TransactionStatus.pending;
      default:
        return TransactionStatus.failed;
    }
  }
}

class MonthlyStats {
  final double totalIncome;
  final double totalExpenses;
  final double incomeChangePercent;
  final double expenseChangePercent;

  const MonthlyStats({
    required this.totalIncome,
    required this.totalExpenses,
    required this.incomeChangePercent,
    required this.expenseChangePercent,
  });

  factory MonthlyStats.fromJson(Map<String, dynamic> json) => MonthlyStats(
        totalIncome: (json['total_income'] as num).toDouble(),
        totalExpenses: (json['total_expenses'] as num).toDouble(),
        incomeChangePercent: (json['income_change_percent'] as num).toDouble(),
        expenseChangePercent:
            (json['expense_change_percent'] as num).toDouble(),
      );
}

// ---------------------------------------------------------------------------
// DashboardService
// ---------------------------------------------------------------------------

class DashboardService {
  static final DashboardService _instance = DashboardService._internal();
  factory DashboardService() => _instance;
  DashboardService._internal();

  final _api = ApiService();

  Future<ApiResponse<AccountSummary>> getAccountSummary() async {
    final response = await _api.get('/api/v1/account/summary');
    if (!response.isSuccess) {
      return ApiResponse.failure(response.error);
    }
    try {
      return ApiResponse.success(AccountSummary.fromJson(response.data!));
    } catch (_) {
      return const ApiResponse.failure('Failed to parse account data.');
    }
  }

  Future<ApiResponse<List<Transaction>>> getRecentTransactions({
    int limit = 10,
    int offset = 0,
  }) async {
    final response = await _api.get(
      '/api/v1/transactions?limit=$limit&offset=$offset',
    );
    if (!response.isSuccess) {
      return ApiResponse.failure(response.error);
    }
    try {
      final list = (response.data!['transactions'] as List)
          .map((e) => Transaction.fromJson(e as Map<String, dynamic>))
          .toList();
      return ApiResponse.success(list);
    } catch (_) {
      return const ApiResponse.failure('Failed to parse transactions.');
    }
  }

  Future<ApiResponse<MonthlyStats>> getMonthlyStats() async {
    final response = await _api.get('/api/v1/account/monthly-stats');
    if (!response.isSuccess) {
      return ApiResponse.failure(response.error);
    }
    try {
      return ApiResponse.success(MonthlyStats.fromJson(response.data!));
    } catch (_) {
      return const ApiResponse.failure('Failed to parse stats.');
    }
  }
}