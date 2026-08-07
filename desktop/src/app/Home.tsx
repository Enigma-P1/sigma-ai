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
        <p>A guided Green Belt DMAIC flow. Pick up a project you've already started, or scope a new one.</p>
      </div>
      <div className="sigma-home__grid">
        <CreateProjectScreen onCreated={onProjectReady} />
        <OpenProjectScreen onOpened={onProjectReady} />
      </div>
    </div>
  );
}
