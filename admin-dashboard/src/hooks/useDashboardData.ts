"use client";

import { useEffect, useState } from "react";
import {
  getAccountSummary,
  getRiskDistribution,
  getMonthlyStats,
  getTransactions,
} from "@/lib/api";

type AccountSummary = {
  userId: string;
  username: string;
  email: string;
  roles: string[];
  documentsUploaded: number;
  highRiskEvents: number;
  accountStatus: string;
};

type RiskDistribution = {
  low: number;
  medium: number;
  high: number;
  total: number;
  buckets: {
    label: string;
    count: number;
  }[];
};

type MonthlyStat = {
  month: string;
  documentsUploaded: number;
  highRiskEvents: number;
};

type Transaction = {
  id: string;
  type: string;
  documentName: string;
  contentType: string;
  sha256Hash: string;
  riskScore: number;
  riskDecision: string;
  createdAt: string;
};

export function useDashboardData() {
  const [summary, setSummary] = useState<AccountSummary | null>(null);

  const [riskDistribution, setRiskDistribution] =
    useState<RiskDistribution | null>(null);

  const [monthlyStats, setMonthlyStats] =
    useState<MonthlyStat[]>([]);

  const [transactions, setTransactions] =
    useState<Transaction[]>([]);

  useEffect(() => {
    async function loadData() {
      try {
        const [
          summaryData,
          distributionData,
          monthlyData,
          transactionData,
        ] = await Promise.all([
          getAccountSummary(),
          getRiskDistribution(),
          getMonthlyStats(),
          getTransactions(),
        ]);

        setSummary(summaryData);
        setRiskDistribution(distributionData);
        setMonthlyStats(monthlyData);
        setTransactions(transactionData);
      } catch (error) {
        console.error("Dashboard data loading failed:", error);
      }
    }

    loadData();

    const interval = setInterval(loadData, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    summary,
    riskDistribution,
    monthlyStats,
    transactions,
  };
}