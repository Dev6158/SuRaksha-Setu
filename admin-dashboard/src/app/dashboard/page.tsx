import Sidebar from "@/components/Sidebar";
import RiskDistributionChart from "@/components/RiskDistributionChart";

export default function DashboardPage() {
  return (
    <div className="flex min-h-screen bg-gray-100">
      <Sidebar />

      <div className="flex-1 p-8">
        <h1 className="text-3xl font-bold mb-8">
          Incident Command Dashboard
        </h1>

        <div className="grid md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">Total Incidents</h2>
            <p className="text-3xl font-bold">128</p>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">High Risk</h2>
            <p className="text-3xl font-bold text-red-500">22</p>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">Medium Risk</h2>
            <p className="text-3xl font-bold text-yellow-500">51</p>
          </div>

          <div className="bg-white rounded-xl shadow p-6">
            <h2 className="text-gray-500">Low Risk</h2>
            <p className="text-3xl font-bold text-green-500">55</p>
          </div>
        </div>

        <RiskDistributionChart />
      </div>
    </div>
  );
}