type RiskDistributionProps = {
  data: {
    low: number;
    medium: number;
    high: number;
    total: number;
  } | null;
};

export default function RiskDistributionChart({
  data,
}: RiskDistributionProps) {
  if (!data) {
    return (
      <div className="bg-white shadow rounded-xl p-6">
        <h2 className="text-xl font-semibold mb-4">
          Risk Distribution
        </h2>

        <p>Loading...</p>
      </div>
    );
  }

  const lowWidth = (data.low / data.total) * 100;
  const mediumWidth = (data.medium / data.total) * 100;
  const highWidth = (data.high / data.total) * 100;

  return (
    <div className="bg-white shadow rounded-xl p-6">
      <h2 className="text-xl font-semibold mb-4">
        Risk Distribution
      </h2>

      <div className="space-y-5">

        <div>
          <div className="flex justify-between mb-1">
            <span>Low Risk</span>
            <span>{data.low}</span>
          </div>

          <div className="w-full bg-gray-200 rounded h-3">
            <div
              className="bg-green-500 h-3 rounded"
              style={{ width: `${lowWidth}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1">
            <span>Medium Risk</span>
            <span>{data.medium}</span>
          </div>

          <div className="w-full bg-gray-200 rounded h-3">
            <div
              className="bg-yellow-500 h-3 rounded"
              style={{ width: `${mediumWidth}%` }}
            />
          </div>
        </div>

        <div>
          <div className="flex justify-between mb-1">
            <span>High Risk</span>
            <span>{data.high}</span>
          </div>

          <div className="w-full bg-gray-200 rounded h-3">
            <div
              className="bg-red-500 h-3 rounded"
              style={{ width: `${highWidth}%` }}
            />
          </div>
        </div>

      </div>
    </div>
  );
}