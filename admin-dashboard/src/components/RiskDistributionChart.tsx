"use client";

import React from "react";

interface RiskDistributionChartProps {
  summary?: {
    total: number;
    high: number;
    medium: number;
    low: number;
  };
}

export default function RiskDistributionChart({ summary = { total: 20, high: 12, medium: 0, low: 8 } }: RiskDistributionChartProps) {
  const { total, high, medium, low } = summary;
  
  // Calculate percentages safely
  const calculatePercent = (value: number) => {
    if (!total || total === 0) return 0;
    return Math.round((value / total) * 100);
  };

  const highPercent = calculatePercent(high);
  const mediumPercent = calculatePercent(medium);
  const lowPercent = calculatePercent(low);

  return (
    <div className="bg-slate-800/40 backdrop-blur-md border border-slate-700/50 rounded-2xl p-6 shadow-2xl transition-all duration-300 hover:border-slate-600/50">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-lg font-bold text-white tracking-tight">
          Risk Distribution
        </h2>
        <span className="text-xs bg-slate-700/50 text-slate-300 px-2.5 py-1 rounded-full font-medium border border-slate-600/30">
          Real-time Audit
        </span>
      </div>

      <div className="space-y-6">
        {/* Low Risk / Authentic */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm font-semibold">
            <span className="text-emerald-400 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-emerald-400 animate-pulse"></span>
              Authentic (Low Risk)
            </span>
            <span className="text-slate-300">{low} ({lowPercent}%)</span>
          </div>
          <div className="h-2.5 bg-slate-900/60 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-emerald-500 to-teal-400 rounded-full shadow-[0_0_12px_rgba(16,185,129,0.3)] transition-all duration-1000 ease-out" 
              style={{ width: `${lowPercent}%` }}
            ></div>
          </div>
        </div>

        {/* Medium Risk */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm font-semibold">
            <span className="text-amber-400 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-amber-400"></span>
              Suspicious (Medium Risk)
            </span>
            <span className="text-slate-300">{medium} ({mediumPercent}%)</span>
          </div>
          <div className="h-2.5 bg-slate-900/60 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-amber-500 to-orange-400 rounded-full shadow-[0_0_12px_rgba(245,158,11,0.3)] transition-all duration-1000 ease-out" 
              style={{ width: `${mediumPercent}%` }}
            ></div>
          </div>
        </div>

        {/* High Risk */}
        <div className="space-y-2">
          <div className="flex justify-between text-sm font-semibold">
            <span className="text-rose-500 flex items-center gap-1.5">
              <span className="h-2 w-2 rounded-full bg-rose-500"></span>
              Fraudulent (High Risk)
            </span>
            <span className="text-slate-300">{high} ({highPercent}%)</span>
          </div>
          <div className="h-2.5 bg-slate-900/60 rounded-full overflow-hidden border border-slate-800">
            <div 
              className="h-full bg-gradient-to-r from-rose-600 to-red-500 rounded-full shadow-[0_0_12px_rgba(239,68,68,0.3)] transition-all duration-1000 ease-out" 
              style={{ width: `${highPercent}%` }}
            ></div>
          </div>
        </div>
      </div>
    </div>
  );
}