import { useCallback } from "react";
import { AdvisorSettingsScreen } from "./advisor/AdvisorSettingsScreen";
import { Home } from "./app/Home";
import { ProjectWorkspace } from "./app/ProjectWorkspace";
import { DiagnosticsView } from "./diagnostics/DiagnosticsView";
import { EngineGate } from "./app/EngineGate";
import { useEngineReadiness } from "./app/useEngineReadiness";
import { useHashRoute } from "./app/navigation";
import "./design/global.css";

/** Top-level router: home (create/open project) / an open project's
 * workspace / diagnostics (M1 brief: "keep the NIST smoke view working,
 * move to a /diagnostics route or menu item") / advisor settings (M5
 * brief, same App-level-route idiom as diagnostics). Hand-rolled hash
 * routing -- no router library in package.json. */
function App() {
  // Engine-readiness gate (Tauri runtime only; a no-op in browser/dev). Held
  // above the router so no route renders until the local engine answers
  // /health -- otherwise every action would just fail with "Failed to fetch"
  // while the sidecar is still self-extracting on first launch.
  const { state: engine, retry: retryEngine } = useEngineReadiness();
  const [route, navigate] = useHashRoute();

  const goHome = useCallback(() => navigate({ kind: "home" }), [navigate]);
  const openDiagnostics = useCallback(() => navigate({ kind: "diagnostics" }), [navigate]);
  const openAdvisorSettings = useCallback(() => navigate({ kind: "advisor-settings" }), [navigate]);
  const openProject = useCallback((projectId: string) => navigate({ kind: "project", projectId }), [navigate]);

  if (engine.phase !== "ready") {
    return <EngineGate state={engine} onRetry={retryEngine} />;
  }

  if (route.kind === "diagnostics") {
    return <DiagnosticsView onBack={goHome} />;
  }
  if (route.kind === "advisor-settings") {
    return <AdvisorSettingsScreen onBack={goHome} />;
  }
  if (route.kind === "project") {
    return (
      <ProjectWorkspace
        projectId={route.projectId}
        onGoHome={goHome}
        onOpenDiagnostics={openDiagnostics}
        onOpenAdvisorSettings={openAdvisorSettings}
      />
    );
  }
  return <Home onProjectReady={openProject} />;
}

export default App;
