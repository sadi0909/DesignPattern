import { useEffect, useState } from "react";
import {
  ACTIVE_LOCATION_STORAGE_KEY,
  evaluateAutomation,
  fetchAutomationRule,
  saveAutomationStrategy,
  type AutomationRuleDto,
  type RecommendationDto,
} from "../../services/api";

const strategyLabels: Record<string, string> = {
  conservative: "Conservative: irrigate only below the low threshold",
  aggressive: "Aggressive: irrigate below the high threshold",
};

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

function actionBadgeClasses(action: string): string {
  return action === "irrigate" ? "bg-sky-100 text-sky-800" : "bg-emerald-100 text-emerald-800";
}

export function StrategyPanel() {
  const [draftLocationId, setDraftLocationId] = useState(
    () => window.localStorage.getItem(ACTIVE_LOCATION_STORAGE_KEY) ?? "",
  );
  const [activeLocationId, setActiveLocationId] = useState(draftLocationId.trim());
  const [rule, setRule] = useState<AutomationRuleDto | null>(null);
  const [selectedKey, setSelectedKey] = useState("");
  const [recommendation, setRecommendation] = useState<RecommendationDto | null>(null);
  const [loading, setLoading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [evaluating, setEvaluating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    if (!activeLocationId) {
      setRule(null);
      return;
    }
    let cancelled = false;
    async function loadRule() {
      try {
        setLoading(true);
        setError(null);
        setRecommendation(null);
        const loaded = await fetchAutomationRule(activeLocationId);
        if (!cancelled) {
          setRule(loaded);
          setSelectedKey(loaded.strategy_key);
        }
      } catch (err) {
        if (!cancelled) {
          setRule(null);
          setError(errorMessage(err, "Unable to load the strategy for this location."));
        }
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    }
    void loadRule();
    return () => {
      cancelled = true;
    };
  }, [activeLocationId]);

  function handleLoad(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setSuccess(null);
    setActiveLocationId(draftLocationId.trim());
  }

  async function handleSave() {
    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      const saved = await saveAutomationStrategy(activeLocationId, selectedKey);
      setRule(saved);
      setRecommendation(null);
      setSuccess("Strategy saved for this location.");
    } catch (err) {
      setError(errorMessage(err, "Unable to save the strategy."));
    } finally {
      setSaving(false);
    }
  }

  async function handleEvaluate() {
    try {
      setEvaluating(true);
      setError(null);
      setSuccess(null);
      setRecommendation(await evaluateAutomation(activeLocationId));
    } catch (err) {
      setError(errorMessage(err, "Unable to evaluate this location."));
    } finally {
      setEvaluating(false);
    }
  }

  const unsaved = rule !== null && selectedKey !== rule.strategy_key;

  return (
    <div className="mt-4 rounded-lg bg-slate-50 p-4">
      <form className="mb-4 flex flex-wrap items-end gap-2" onSubmit={handleLoad}>
        <div className="min-w-0 flex-1">
          <label htmlFor="automation-location-id" className="mb-1 block text-sm font-medium text-slate-700">
            Location ID
          </label>
          <input
            id="automation-location-id"
            value={draftLocationId}
            onChange={(event) => setDraftLocationId(event.target.value)}
            className="w-full rounded-md border border-slate-300 bg-white px-3 py-2 font-mono text-xs text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
            placeholder="Paste the ID from a saved location configuration"
          />
        </div>
        <button
          type="submit"
          className="rounded-md border border-emerald-600 px-3 py-2 text-sm font-medium text-emerald-700 hover:bg-emerald-50"
        >
          Load location
        </button>
      </form>

      {!activeLocationId ? (
        <p className="text-sm text-slate-500">
          Save a location configuration first, or paste an existing location ID above.
        </p>
      ) : loading ? (
        <p className="text-sm text-slate-500">Loading strategy…</p>
      ) : rule ? (
        <div className="space-y-4">
          <div>
            <label htmlFor="automation-strategy" className="mb-1 block text-sm font-medium text-slate-700">
              Strategy
            </label>
            <div className="flex flex-wrap gap-2">
              <select
                id="automation-strategy"
                value={selectedKey}
                onChange={(event) => setSelectedKey(event.target.value)}
                className="min-w-0 flex-1 rounded-md border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500"
              >
                {rule.available_strategies.map((key) => (
                  <option key={key} value={key}>
                    {strategyLabels[key] ?? key}
                  </option>
                ))}
              </select>
              <button
                type="button"
                onClick={() => void handleSave()}
                disabled={saving || !unsaved}
                className="rounded-md bg-emerald-600 px-3 py-2 text-sm font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
              >
                {saving ? "Saving…" : "Save strategy"}
              </button>
            </div>
            <p className="mt-1 text-xs text-slate-500">
              {rule.is_default
                ? "Using the default strategy until you save one."
                : `Saved strategy: ${rule.strategy_key}`}
            </p>
          </div>

          <button
            type="button"
            onClick={() => void handleEvaluate()}
            disabled={evaluating}
            className="rounded-md bg-sky-600 px-3 py-2 text-sm font-medium text-white hover:bg-sky-700 disabled:opacity-50"
          >
            {evaluating ? "Evaluating…" : "Evaluate"}
          </button>

          {recommendation && (
            <section className="rounded-md border border-slate-200 bg-white p-3" aria-live="polite">
              <div className="flex flex-wrap items-center gap-2">
                <span
                  className={`rounded-full px-2 py-0.5 text-xs font-semibold capitalize ${actionBadgeClasses(recommendation.action)}`}
                >
                  {recommendation.action}
                </span>
                <span className="text-xs text-slate-500">Strategy: {recommendation.strategy_key}</span>
              </div>
              <p className="mt-2 text-sm text-slate-700">{recommendation.reason}</p>
            </section>
          )}
        </div>
      ) : null}

      {error && (
        <p className="mt-3 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          {error}
        </p>
      )}
      {success && (
        <p className="mt-3 rounded-md bg-emerald-50 p-3 text-sm text-emerald-800" role="status">
          {success}
        </p>
      )}
    </div>
  );
}
