import { Routes, Route } from "react-router-dom";
import { AppLayout } from "./components/AppLayout";
import { DashboardPage } from "./pages/DashboardPage";

function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-16 text-center">
      <h1 className="mb-4 text-4xl font-bold text-emerald-600">Smart Greenhouse</h1>
      <p className="mb-8 text-lg text-slate-600">Monitor and control your greenhouse environment</p>
      <a
        href="/dashboard"
        className="inline-flex items-center justify-center rounded-lg bg-emerald-600 px-6 py-3 text-base font-medium text-white hover:bg-emerald-700 transition-colors"
      >
        Go to Dashboard
      </a>
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<AppLayout />}>
        <Route index element={<HomePage />} />
        <Route path="dashboard" element={<DashboardPage />} />
      </Route>
    </Routes>
  );
}