import { Outlet, Link, useLocation } from "react-router-dom";
import { HealthStatus } from "./HealthStatus";

export function AppLayout() {
  const location = useLocation();

  return (
    <div className="min-h-screen flex flex-col">
      <header className="border-b border-slate-200 bg-white sticky top-0 z-10">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link to="/" className="text-xl font-bold text-emerald-600">
                Smart Greenhouse
              </Link>
              <nav className="hidden md:flex items-center gap-6">
                <Link
                  to="/"
                  className={`text-sm font-medium transition-colors ${
                    location.pathname === "/"
                      ? "text-emerald-600"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  Home
                </Link>
                <Link
                  to="/dashboard"
                  className={`text-sm font-medium transition-colors ${
                    location.pathname === "/dashboard"
                      ? "text-emerald-600"
                      : "text-slate-500 hover:text-slate-700"
                  }`}
                >
                  Dashboard
                </Link>
              </nav>
            </div>
            <HealthStatus />
          </div>
        </div>
      </header>
      <main className="flex-1">
        <Outlet />
      </main>
    </div>
  );
}