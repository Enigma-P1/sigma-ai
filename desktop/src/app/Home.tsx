import { CreateProjectScreen } from "./project/CreateProjectScreen";
import { OpenProjectScreen } from "./project/OpenProjectScreen";
import "./Home.css";

export interface HomeProps {
  onProjectReady: (projectId: string) => void;
}

/** Landing screen: create a project or open an existing one (M1 brief). */
export function Home({ onProjectReady }: HomeProps) {
  return (
    <div className="sigma-home">
      <div className="sigma-home__intro">
        <h1>Sigma AI</h1>
        {/* The old line was "A guided Green Belt DMAIC flow." Both testers in
          * the 2026-08-12 UAT met it as their first sentence and neither knew
          * what either term meant -- one asked plainly what "Green Belt" and
          * "DMAIC" were "without having somebody explain it". The method is
          * still what this is; it just cannot be the greeting. Say what the
          * software does for you, then name the method it uses, in that
          * order, because only one of those is a reason to keep reading. */}
        <p>
          Work out what's really causing a problem at work, and prove whether your fix worked. Step by step,
          with the statistics done for you.
        </p>
        <p className="sigma-home__method">
          It follows DMAIC — Define, Measure, Analyze, Improve, Control — the standard five-stage improvement
          method taught at Six Sigma Green Belt level. You don't need to know it; the app walks you through.
        </p>
      </div>
      <div className="sigma-home__grid">
        <CreateProjectScreen onCreated={onProjectReady} />
        <OpenProjectScreen onOpened={onProjectReady} />
      </div>
    </div>
  );
}
