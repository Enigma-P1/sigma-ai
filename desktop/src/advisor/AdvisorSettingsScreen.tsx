import { useEffect, useState } from "react";
import { Button, Field, Panel, TextInput, VerdictBanner, YesNoToggle } from "../design/components";
import { getAdvisorSettings, putAdvisorSettings } from "../api/client";
import { ApiError } from "../api/errors";
import { ADVISOR_PRIVACY_STATEMENT } from "./privacyStatement";
import "./AdvisorSettingsScreen.css";

export interface AdvisorSettingsScreenProps {
  onBack: () => void;
}

type LoadState = { phase: "loading" } | { phase: "loaded" } | { phase: "error"; message: string };
type SaveState = "idle" | "saving" | "saved" | "error";

/** App-level route (same idiom as DiagnosticsView, src/app/navigation.ts) --
 * API key input (never rendered back; masked last-4 from the GET), an
 * enabled toggle, a "Remove key" affordance (M5 exit critic, Fix 1 -- see
 * handleRemoveKey), and the shared privacy statement (privacyStatement.ts,
 * Fix 2). */
export function AdvisorSettingsScreen({ onBack }: AdvisorSettingsScreenProps) {
  const [loadState, setLoadState] = useState<LoadState>({ phase: "loading" });
  const [apiKeyMasked, setApiKeyMasked] = useState<string | null>(null);
  const [apiKeyInput, setApiKeyInput] = useState("");
  const [baseUrl, setBaseUrl] = useState("");
  const [enabled, setEnabled] = useState(true);
  const [saveState, setSaveState] = useState<SaveState>("idle");
  const [saveError, setSaveError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    getAdvisorSettings()
      .then((s) => {
        if (cancelled) return;
        setApiKeyMasked(s.api_key_masked);
        setBaseUrl(s.base_url ?? "");
        setEnabled(s.enabled);
        setLoadState({ phase: "loaded" });
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setLoadState({ phase: "error", message: err instanceof ApiError ? err.message : "Could not load advisor settings." });
      });
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSave() {
    setSaveState("saving");
    setSaveError(null);
    try {
      const result = await putAdvisorSettings({
        // Blank input means "leave the stored key unchanged" -- never send
        // an empty string as a deliberate clear (routes/advisor.py's
        // contract: omit/"" both mean unchanged).
        api_key: apiKeyInput.trim() ? apiKeyInput.trim() : null,
        base_url: baseUrl.trim() ? baseUrl.trim() : null,
        enabled,
      });
      setApiKeyMasked(result.api_key_masked);
      setApiKeyInput("");
      setSaveState("saved");
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Could not save advisor settings.");
      setSaveState("error");
    }
  }

  /** M5 exit critic, severity 1: before this existed there was NO in-app
   * way to remove a stored key -- api_key="" already means "leave
   * unchanged" (handleSave's own comment), so the only path was hand-
   * editing settings.json, which is exactly the road to the truncated/
   * corrupt-file case load() now has to survive. clear_api_key: true is
   * the explicit, safe removal path (routes/advisor.py's
   * AdvisorSettingsUpdateRequest). */
  async function handleRemoveKey() {
    setSaveState("saving");
    setSaveError(null);
    try {
      const result = await putAdvisorSettings({
        clear_api_key: true,
        base_url: baseUrl.trim() ? baseUrl.trim() : null,
        enabled,
      });
      setApiKeyMasked(result.api_key_masked);
      setApiKeyInput("");
      setSaveState("saved");
    } catch (err) {
      setSaveError(err instanceof ApiError ? err.message : "Could not remove the stored key.");
      setSaveState("error");
    }
  }

  return (
    <div className="sigma-advisor-settings">
      <button
        type="button"
        className="sigma-advisor-settings__back"
        onClick={onBack}
        data-testid="advisor-settings-back"
      >
        ← Back
      </button>
      <h1>Advisor settings</h1>
      <p className="sigma-advisor-settings__subtitle">
        The Layer 2 advisor is optional. Layer 1 (every tool, all math, every chart) works fully without any of this.
      </p>

      <Panel title="Privacy" className="sigma-advisor-settings__panel">
        <p data-testid="advisor-privacy-statement">{ADVISOR_PRIVACY_STATEMENT}</p>
      </Panel>

      <Panel title="Configuration" className="sigma-advisor-settings__panel">
        {loadState.phase === "loading" && <p>Loading…</p>}
        {loadState.phase === "error" && <VerdictBanner tone="fail" headline="Could not load settings" detail={loadState.message} />}

        {loadState.phase !== "loading" && (
          <div className="sigma-advisor-settings__form">
            <Field
              label="API key"
              htmlFor="advisor-api-key"
              helper={apiKeyMasked ? `Currently set: ${apiKeyMasked}` : "No key stored yet -- the advisor stays off until one is set."}
            >
              <TextInput
                id="advisor-api-key"
                type="password"
                autoComplete="off"
                placeholder={apiKeyMasked ? "Enter a new key to replace it" : "sk-ant-..."}
                value={apiKeyInput}
                onChange={(e) => setApiKeyInput(e.target.value)}
                data-testid="advisor-api-key-input"
              />
              {apiKeyMasked && (
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={handleRemoveKey}
                  disabled={saveState === "saving"}
                  data-testid="advisor-remove-key"
                >
                  Remove key
                </Button>
              )}
            </Field>

            <Field label="Base URL (optional)" htmlFor="advisor-base-url" helper="Leave blank to use the default Anthropic API endpoint.">
              <TextInput
                id="advisor-base-url"
                autoComplete="off"
                placeholder="https://api.anthropic.com"
                value={baseUrl}
                onChange={(e) => setBaseUrl(e.target.value)}
                data-testid="advisor-base-url-input"
              />
            </Field>

            <Field label="Enabled" helper="Turn the advisor off entirely, even if a key is set.">
              <YesNoToggle name="advisor-enabled" value={enabled} onChange={setEnabled} />
            </Field>

            <div className="sigma-advisor-settings__actions">
              <Button variant="primary" onClick={handleSave} disabled={saveState === "saving"} data-testid="advisor-settings-save">
                {saveState === "saving" ? "Saving…" : "Save"}
              </Button>
              {saveState === "saved" && (
                <div data-testid="advisor-settings-saved">
                  <VerdictBanner tone="pass" headline="Saved" />
                </div>
              )}
              {saveState === "error" && <VerdictBanner tone="fail" headline="Could not save" detail={saveError} />}
            </div>
          </div>
        )}
      </Panel>
    </div>
  );
}
