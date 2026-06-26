"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
} from "recharts";

type MonthlyStat = {
  month: string;
  documentsUploaded: number;
  highRiskEvents: number;
};

type RiskTrendChartProps = {
  data: MonthlyStat[];
};

export default function RiskTrendChart({
  data,
}: RiskTrendChartProps) {
  if (!data || data.length === 0) {
    return (
      <div className="bg-white rounded-xl shadow p-6 mt-6">
        <h2 className="text-2xl font-bold mb-4">
          Monthly Statistics
        </h2>

        <p>Loading...</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-xl shadow p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4">
        Monthly Statistics
      </h2>

      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data}>
          <CartesianGrid strokeDasharray="3 3" />

          <XAxis dataKey="month" />

          <YAxis />

          <Tooltip />

          <Line
            type="monotone"
            dataKey="documentsUploaded"
            stroke="#2563eb"
            strokeWidth={3}
            name="Documents Uploaded"
          />

          <Line
            type="monotone"
            dataKey="highRiskEvents"
            stroke="#ef4444"
            strokeWidth={3}
            name="High Risk Events"
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}