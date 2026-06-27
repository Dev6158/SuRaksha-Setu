export default function Sidebar() {
  return (
    <div className="w-64 bg-slate-900 text-white p-6">
      <h1 className="text-2xl font-bold mb-8">
        SuRaksha Setu
      </h1>

      <ul className="space-y-4">
        <li className="hover:text-blue-400 cursor-pointer">
          Dashboard
        </li>

        <li className="hover:text-blue-400 cursor-pointer">
          Analytics
        </li>

        <li className="hover:text-blue-400 cursor-pointer">
          Documents
        </li>

        <li className="hover:text-blue-400 cursor-pointer">
          Settings
        </li>
      </ul>
    </div>
  );
}