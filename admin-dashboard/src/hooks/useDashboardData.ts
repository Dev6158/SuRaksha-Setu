"use client";

import { useEffect, useState } from "react";
import {
  getAccountSummary,
  getHourlyRiskTrends,
} from "@/lib/api";

export function useDashboardData() {
  const [summary, setSummary] = useState(null);
  const [trendData, setTrendData] = useState([]);

  useEffect(() => {
    async function loadData() {
      try {
        const now = new Date();
        const yesterday = new Date(
          now.getTime() - 24 * 60 * 60 * 1000
        );

        const start = yesterday.toISOString();
        const end = now.toISOString();

        const summaryData =
          await getAccountSummary();

        const trendResponse =
          await getHourlyRiskTrends(start, end);

        setSummary(summaryData);
        setTrendData(trendResponse);
      } catch (error) {
        console.error(error);
      }
    }

    loadData();

    const interval = setInterval(loadData, 30000);

    return () => clearInterval(interval);
  }, []);

  return {
    summary,
    trendData,
  };
}