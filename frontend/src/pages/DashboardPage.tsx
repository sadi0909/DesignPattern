import { SensorList } from "../features/sensors/SensorList";

const sections = [
  { id: "config", title: "Configuration", description: "Device and threshold settings" },
  { id: "automation", title: "Automation", description: "Rules and schedules" },
  { id: "overview", title: "Overview", description: "System status summary" },
  { id: "controls", title: "Controls", description: "Manual actuator control" },
  { id: "events", title: "Events", description: "Alerts and activity log" },
];

export function DashboardPage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      <h1 className="mb-8 text-3xl font-bold text-slate-900">Dashboard</h1>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        <article
          id="sensors"
          className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
        >
          <h2 className="mb-2 text-lg font-semibold text-slate-900">Sensors</h2>
          <p className="text-slate-500">Create and monitor greenhouse sensors</p>
          <SensorList />
        </article>
        {sections.map((section) => (
          <article
            key={section.id}
            id={section.id}
            className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm hover:shadow-md transition-shadow"
          >
            <h2 className="mb-2 text-lg font-semibold text-slate-900">{section.title}</h2>
            <p className="text-slate-500">{section.description}</p>
            <div className="mt-4 h-24 rounded-lg bg-slate-50" />
          </article>
        ))}
      </div>
    </div>
  );
}
