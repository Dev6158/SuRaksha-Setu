"use client";

import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from "recharts";

const data = [
  { hour: "08:00", incidents: 5 },
  { hour: "09:00", incidents: 12 },
  { hour: "10:00", incidents: 9 },
  { hour: "11:00", incidents: 18 },
  { hour: "12:00", incidents: 22 },
  { hour: "13:00", incidents: 15 },
];

export default function RiskTrendChart() {
  return (
    <div className="bg-white rounded-xl shadow p-6 mt-6">
      <h2 className="text-2xl font-bold mb-4">
        Risk Trends
      </h2>

      <LineChart
        width={900}
        height={300}
        data={data}
      >
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="hour" />
        <YAxis />
        <Tooltip />
        <Line
          type="monotone"
          dataKey="incidents"
          stroke="#ef4444"
          strokeWidth={3}
        />
      </LineChart>
    </div>
  );
}