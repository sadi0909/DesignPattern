import type { DeviceFamily } from "../../services/api";

type DeviceFamilySwitcherProps = {
  family: DeviceFamily;
  onFamilyChange: (family: DeviceFamily) => void;
  disabled?: boolean;
};

const families: { key: DeviceFamily; label: string }[] = [
  { key: "simulation", label: "Simulation" },
  { key: "edge", label: "Edge hardware" },
];

export function DeviceFamilySwitcher({
  family,
  onFamilyChange,
  disabled = false,
}: DeviceFamilySwitcherProps) {
  return (
    <div className="mb-4 flex flex-wrap items-center gap-2" role="group" aria-label="Device family">
      <span className="mr-1 text-sm font-medium text-slate-600">Family</span>
      {families.map((option) => (
        <button
          key={option.key}
          type="button"
          aria-pressed={family === option.key}
          onClick={() => onFamilyChange(option.key)}
          disabled={disabled}
          className={`rounded-md px-3 py-2 text-sm font-medium transition-colors disabled:opacity-50 ${
            family === option.key
              ? "bg-emerald-600 text-white"
              : "border border-slate-300 bg-white text-slate-700 hover:bg-slate-100"
          }`}
        >
          {option.label}
        </button>
      ))}
    </div>
  );
}
