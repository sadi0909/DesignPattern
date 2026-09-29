import { useState } from "react";
import {
  createLocationConfig,
  type LocationConfigDto,
  type LocationConfigRequest,
  type ZoneConfigRequest,
} from "../../services/api";

type ZoneDraft = {
  key: number;
  name: string;
  moistureThresholdLow: string;
  moistureThresholdHigh: string;
  schedule: string;
};

type ZoneDraftErrors = {
  name?: string;
  thresholds?: string;
  schedule?: string;
};

type FormErrors = {
  locationName?: string;
  zones: Record<number, ZoneDraftErrors>;
  general?: string;
};

let nextDraftKey = 1;

function newZoneDraft(): ZoneDraft {
  return {
    key: nextDraftKey++,
    name: "",
    moistureThresholdLow: "0.2",
    moistureThresholdHigh: "0.45",
    schedule: "{}",
  };
}

function parseSchedule(value: string): Record<string, unknown> {
  const parsed: unknown = JSON.parse(value || "{}");
  if (parsed === null || Array.isArray(parsed) || typeof parsed !== "object") {
    throw new Error("Schedule must be a JSON object.");
  }
  return parsed as Record<string, unknown>;
}

export function LocationConfigWizard() {
  const [locationName, setLocationName] = useState("");
  const [zones, setZones] = useState<ZoneDraft[]>([newZoneDraft()]);
  const [errors, setErrors] = useState<FormErrors>({ zones: {} });
  const [apiError, setApiError] = useState<string | null>(null);
  const [createdConfig, setCreatedConfig] = useState<LocationConfigDto | null>(null);
  const [saving, setSaving] = useState(false);

  function updateZone(key: number, field: keyof Omit<ZoneDraft, "key">, value: string) {
    setZones((current) => current.map((zone) => (zone.key === key ? { ...zone, [field]: value } : zone)));
    setErrors((current) => ({ ...current, zones: { ...current.zones, [key]: {} } }));
  }

  function validateAndBuildRequest(): LocationConfigRequest | null {
    const nextErrors: FormErrors = { zones: {} };
    const trimmedLocationName = locationName.trim();
    if (!trimmedLocationName) {
      nextErrors.locationName = "Enter a location name.";
    }
    if (zones.length === 0) {
      nextErrors.general = "Add at least one zone before saving.";
    }

    const requestZones: ZoneConfigRequest[] = [];
    const zoneNames = new Set<string>();
    for (const zone of zones) {
      const zoneErrors: ZoneDraftErrors = {};
      const trimmedName = zone.name.trim();
      const normalizedName = trimmedName.toLocaleLowerCase();
      if (!trimmedName) {
        zoneErrors.name = "Enter a zone name.";
      } else if (zoneNames.has(normalizedName)) {
        zoneErrors.name = "Zone names must be unique within this location.";
      }
      if (trimmedName) zoneNames.add(normalizedName);

      const low = Number(zone.moistureThresholdLow);
      const high = Number(zone.moistureThresholdHigh);
      if (
        !zone.moistureThresholdLow.trim() ||
        !zone.moistureThresholdHigh.trim() ||
        !Number.isFinite(low) ||
        !Number.isFinite(high) ||
        low < 0 ||
        high > 1 ||
        low >= high
      ) {
        zoneErrors.thresholds = "Enter thresholds between 0 and 1, with low strictly less than high.";
      }

      let schedule: Record<string, unknown> = {};
      try {
        schedule = parseSchedule(zone.schedule);
      } catch {
        zoneErrors.schedule = "Enter a valid JSON object for the schedule.";
      }

      if (Object.keys(zoneErrors).length > 0) {
        nextErrors.zones[zone.key] = zoneErrors;
      } else {
        requestZones.push({
          name: trimmedName,
          moisture_threshold_low: low,
          moisture_threshold_high: high,
          schedule,
        });
      }
    }

    if (nextErrors.locationName || nextErrors.general || Object.keys(nextErrors.zones).length > 0) {
      setErrors(nextErrors);
      return null;
    }
    setErrors({ zones: {} });
    return { location_name: trimmedLocationName, zones: requestZones };
  }

  async function handleSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setApiError(null);
    setCreatedConfig(null);
    const request = validateAndBuildRequest();
    if (!request) return;

    try {
      setSaving(true);
      setCreatedConfig(await createLocationConfig(request));
    } catch (error) {
      setApiError(error instanceof Error ? error.message : "Unable to save this location configuration.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <form className="space-y-5" onSubmit={(event) => void handleSubmit(event)} noValidate>
        <div>
          <label htmlFor="location-name" className="mb-1 block text-sm font-medium text-slate-700">
            Location name
          </label>
          <input
            id="location-name"
            value={locationName}
            onChange={(event) => setLocationName(event.target.value)}
            maxLength={128}
            required
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            placeholder="Lab Site A"
          />
          {errors.locationName && <p className="mt-1 text-sm text-red-600">{errors.locationName}</p>}
        </div>

        <div className="space-y-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h3 className="font-semibold text-slate-800">Zones</h3>
            <button
              type="button"
              onClick={() => setZones((current) => [...current, newZoneDraft()])}
              className="rounded-md border border-emerald-600 px-3 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-50"
            >
              Add zone
            </button>
          </div>
          {errors.general && <p className="text-sm text-red-600">{errors.general}</p>}
          {zones.map((zone, index) => {
            const zoneErrors = errors.zones[zone.key];
            return (
              <fieldset key={zone.key} className="space-y-3 rounded-lg border border-slate-200 bg-white p-4">
                <legend className="px-1 text-sm font-semibold text-slate-700">Zone {index + 1}</legend>
                <div>
                  <label htmlFor={`zone-name-${zone.key}`} className="mb-1 block text-sm text-slate-600">
                    Zone name
                  </label>
                  <input
                    id={`zone-name-${zone.key}`}
                    value={zone.name}
                    onChange={(event) => updateZone(zone.key, "name", event.target.value)}
                    maxLength={128}
                    required
                    className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    placeholder="Bench 1"
                  />
                  {zoneErrors?.name && <p className="mt-1 text-sm text-red-600">{zoneErrors.name}</p>}
                </div>
                <div className="grid gap-3 sm:grid-cols-2">
                  <div>
                    <label htmlFor={`zone-low-${zone.key}`} className="mb-1 block text-sm text-slate-600">
                      Low moisture threshold (0–1)
                    </label>
                    <input
                      id={`zone-low-${zone.key}`}
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={zone.moistureThresholdLow}
                      onChange={(event) => updateZone(zone.key, "moistureThresholdLow", event.target.value)}
                      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                  <div>
                    <label htmlFor={`zone-high-${zone.key}`} className="mb-1 block text-sm text-slate-600">
                      High moisture threshold (0–1)
                    </label>
                    <input
                      id={`zone-high-${zone.key}`}
                      type="number"
                      min="0"
                      max="1"
                      step="0.01"
                      value={zone.moistureThresholdHigh}
                      onChange={(event) => updateZone(zone.key, "moistureThresholdHigh", event.target.value)}
                      className="w-full rounded-md border border-slate-300 px-3 py-2 text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    />
                  </div>
                </div>
                {zoneErrors?.thresholds && <p className="text-sm text-red-600">{zoneErrors.thresholds}</p>}
                <div>
                  <label htmlFor={`zone-schedule-${zone.key}`} className="mb-1 block text-sm text-slate-600">
                    Schedule (JSON object)
                  </label>
                  <textarea
                    id={`zone-schedule-${zone.key}`}
                    value={zone.schedule}
                    onChange={(event) => updateZone(zone.key, "schedule", event.target.value)}
                    rows={2}
                    className="w-full rounded-md border border-slate-300 px-3 py-2 font-mono text-sm focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
                    placeholder={'{"watering":"08:00"}'}
                  />
                  {zoneErrors?.schedule && <p className="mt-1 text-sm text-red-600">{zoneErrors.schedule}</p>}
                </div>
                <button
                  type="button"
                  onClick={() => setZones((current) => current.filter((item) => item.key !== zone.key))}
                  disabled={zones.length === 1}
                  className="text-sm font-medium text-red-600 hover:text-red-700 disabled:cursor-not-allowed disabled:opacity-40"
                >
                  Remove zone
                </button>
              </fieldset>
            );
          })}
        </div>

        {apiError && <p className="rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">{apiError}</p>}
        <button
          type="submit"
          disabled={saving}
          className="rounded-md bg-emerald-600 px-4 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
        >
          {saving ? "Saving configuration…" : "Save location configuration"}
        </button>
      </form>

      {createdConfig && (
        <section className="mt-6 rounded-lg border border-emerald-200 bg-emerald-50 p-4" aria-live="polite">
          <h3 className="font-semibold text-emerald-900">Configuration saved</h3>
          <p className="mt-1 text-sm text-emerald-900">
            {createdConfig.location.name} · ID: <code>{createdConfig.location.id}</code>
          </p>
          <ul className="mt-3 space-y-2">
            {createdConfig.zones.map((zone) => (
              <li key={zone.id} className="rounded-md bg-white p-3 text-sm text-slate-700">
                <p className="font-medium">{zone.name}</p>
                <p className="text-xs text-slate-500">Location ID: {zone.location_id}</p>
                <p className="text-xs text-slate-500">
                  Moisture range: {zone.moisture_threshold_low}–{zone.moisture_threshold_high}
                </p>
                <pre className="mt-1 overflow-x-auto text-xs">{JSON.stringify(zone.schedule, null, 2)}</pre>
              </li>
            ))}
          </ul>
        </section>
      )}
    </div>
  );
}
