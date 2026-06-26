"use client";

import Sidebar from "@/components/Sidebar";
import RiskDistributionChart from "@/components/RiskDistributionChart";
import RiskTrendChart from "@/components/RiskTrendChart";
import { useDashboardData } from "@/hooks/useDashboardData";

export default function DashboardPage() {
  const {
    summary,
    riskDistribution,
    monthlyStats,
    transactions,
  } = useDashboardData();

  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar />

      <div className="flex-1 p-8">
        <h1 className="text-3xl font-bold mb-8">
          Incident Command Dashboard
        </h1>

        <div className="grid md:grid-cols-4 gap-6 mb-8">

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">Documents Uploaded</h2>
            <p className="text-3xl font-bold">
              {summary?.documentsUploaded ?? 0}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">High Risk Events</h2>
            <p className="text-3xl font-bold text-red-500">
              {summary?.highRiskEvents ?? 0}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">Account Status</h2>
            <p className="text-2xl font-bold text-blue-500">
              {summary?.accountStatus ?? "N/A"}
            </p>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">Role</h2>
            <p className="text-lg font-bold">
              {summary?.roles?.join(", ") ?? "N/A"}
            </p>
          </div>

        </div>

        <RiskDistributionChart
          data={riskDistribution}
        />

        <RiskTrendChart
          data={monthlyStats}
        />
      </div>
    </div>
  );
}