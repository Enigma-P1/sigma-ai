import { useCallback, useEffect, useState } from "react";

/** Hand-rolled hash router -- no routing library in package.json to pull
 * in, and the app only ever has three top-level places to be. */
export type Route = { kind: "home" } | { kind: "project"; projectId: string } | { kind: "diagnostics" };

export function routeToHash(route: Route): string {
  switch (route.kind) {
    case "home":
      return "#/";
    case "diagnostics":
      return "#/diagnostics";
    case "project":
      return `#/project/${encodeURIComponent(route.projectId)}`;
  }
}

export function hashToRoute(hash: string): Route {
  const path = hash.replace(/^#/, "") || "/";
  if (path === "/diagnostics") return { kind: "diagnostics" };
  const projectMatch = /^\/project\/([^/]+)/.exec(path);
  if (projectMatch) return { kind: "project", projectId: decodeURIComponent(projectMatch[1]) };
  return { kind: "home" };
}

export function useHashRoute(): [Route, (route: Route) => void] {
  const [route, setRoute] = useState<Route>(() => hashToRoute(window.location.hash));

  useEffect(() => {
    function onHashChange() {
      setRoute(hashToRoute(window.location.hash));
    }
    window.addEventListener("hashchange", onHashChange);
    return () => window.removeEventListener("hashchange", onHashChange);
  }, []);

  const navigate = useCallback((next: Route) => {
    const nextHash = routeToHash(next);
    if (window.location.hash !== nextHash) {
      window.location.hash = nextHash;
    } else {
      setRoute(next);
    }
  }, []);

  return [route, navigate];
}
