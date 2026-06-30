"use client";

import React from "react";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ResponsiveContainer,
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
    <div className="bg-slate-800/40 backdrop-blur-md border border-slate-700/50 rounded-2xl p-6 shadow-2xl transition-all duration-300 hover:border-slate-600/50 flex flex-col h-[350px]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-bold text-white tracking-tight">
          Risk Trends
        </h2>
        <span className="text-xs bg-slate-700/50 text-slate-300 px-2.5 py-1 rounded-full font-medium border border-slate-600/30">
          Hourly Incidents
        </span>
      </div>

      <div className="flex-grow w-full h-[250px] min-h-0">
        <ResponsiveContainer width="100%" height="100%">
          <AreaChart
            data={data}
            margin={{ top: 10, right: 10, left: -20, bottom: 0 }}
          >
            <defs>
              <linearGradient id="colorIncidents" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
                <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.0} />
              </linearGradient>
            </defs>
            <CartesianGrid strokeDasharray="3 3" stroke="#334155" opacity={0.3} />
            <XAxis 
              dataKey="hour" 
              stroke="#94a3b8" 
              fontSize={11}
              tickLine={false}
              axisLine={false}
              dy={10}
            />
            <YAxis 
              stroke="#94a3b8" 
              fontSize={11}
              tickLine={false}
              axisLine={false}
              dx={-5}
            />
            <Tooltip 
              contentStyle={{ 
                backgroundColor: 'rgba(15, 23, 42, 0.9)', 
                border: '1px solid rgba(71, 85, 105, 0.5)', 
                borderRadius: '12px', 
                color: '#f8fafc',
                backdropFilter: 'blur(8px)',
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.3)',
                fontSize: '12px'
              }}
              labelStyle={{ fontWeight: 'bold', color: '#94a3b8', marginBottom: '4px' }}
            />
            <Area
              type="monotone"
              dataKey="incidents"
              stroke="#f43f5e"
              strokeWidth={3}
              fillOpacity={1}
              fill="url(#colorIncidents)"
            />
          </AreaChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}