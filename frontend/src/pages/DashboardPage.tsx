import { CommandPanel } from "../components/commands/CommandPanel";
import { DeviceList } from "../components/devices/DeviceList";
import { ExecutionLog } from "../components/devices/ExecutionLog";
import { EventFeed } from "../components/events/EventFeed";
import { LocationConfigWizard } from "../components/config/LocationConfigWizard";
import { StrategyPanel } from "../features/automation/StrategyPanel";
import { SensorList } from "../features/sensors/SensorList";
import { SensorTrendPanel } from "../features/sensors/SensorTrendPanel";
import { OverviewPanel } from "../features/overview/OverviewPanel";

export function DashboardPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-8 text-3xl font-bold text-slate-900">Dashboard</h1>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <article id="overview" className="card">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Overview</h2>
          <p className="text-slate-500">Location status summary</p>
          <OverviewPanel />
        </article>
        <article id="sensors" className="card">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Sensors</h2>
          <p className="text-slate-500">Create and monitor greenhouse sensors</p>
          <SensorList />
        </article>
        <article id="devices" className="card">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Devices</h2>
          <p className="text-slate-500">Provision and browse a coherent device family</p>
          <DeviceList />
        </article>
        <article id="trends" className="card lg:col-span-3">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Moisture trend</h2>
          <p className="text-slate-500">
            Historical sensor readings from PostgreSQL, plotted over a selectable time range.
          </p>
          <SensorTrendPanel />
        </article>
        <article id="config" className="card">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Configuration</h2>
          <p className="text-slate-500">Build a validated location configuration with zones</p>
          <LocationConfigWizard />
        </article>
        <article id="automation" className="card">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Automation</h2>
          <p className="text-slate-500">Choose a strategy per location and evaluate its recommendation</p>
          <StrategyPanel />
        </article>
        <article id="controls" className="card lg:col-span-3">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Controls</h2>
          <p className="text-slate-500">
            Commands are checked against the current state, executed through the decorated
            actuator port, and retained in the command history.
          </p>
          <CommandPanel />
        </article>
        <article id="executions" className="card lg:col-span-3">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Execution log</h2>
          <p className="text-slate-500">
            Every decorated actuator attempt, including blocked policy checks
          </p>
          <ExecutionLog />
        </article>
        <article id="events" className="card lg:col-span-3">
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Events</h2>
          <p className="text-slate-500">
            Persisted alerts from the in-process event bus. The feed survives refresh
            because alerts live in PostgreSQL.
          </p>
          <EventFeed />
        </article>
      </div>
    </div>
  );
}
