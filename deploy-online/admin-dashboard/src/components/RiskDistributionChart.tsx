export default function RiskDistributionChart() {
  return (
    <div className="bg-white shadow rounded-xl p-6">
      <h2 className="text-xl font-semibold mb-4">
        Risk Distribution
      </h2>

      <div className="space-y-4">
        <div>
          <p>Low Risk</p>
          <div className="h-3 bg-green-500 rounded w-4/5"></div>
        </div>

        <div>
          <p>Medium Risk</p>
          <div className="h-3 bg-yellow-500 rounded w-2/3"></div>
        </div>

        <div>
          <p>High Risk</p>
          <div className="h-3 bg-red-500 rounded w-1/3"></div>
        </div>
      </div>
    </div>
  );
}