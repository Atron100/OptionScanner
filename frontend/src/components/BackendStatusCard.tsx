import { useEffect, useState } from "react";

import { getJson } from "../api/client";

type HealthResponse = {
  status: string;
};

type SystemInfoResponse = {
  app_name: string;
  environment: string;
  database_url: string;
  database_exists: boolean;
};

export function BackendStatusCard() {
  const [health, setHealth] = useState<string>("checking");
  const [systemInfo, setSystemInfo] = useState<SystemInfoResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;

    async function load() {
      try {
        const [healthResponse, systemResponse] = await Promise.all([
          getJson<HealthResponse>("/api/v1/health"),
          getJson<SystemInfoResponse>("/api/v1/system/info"),
        ]);
        if (!active) {
          return;
        }
        setHealth(healthResponse.status);
        setSystemInfo(systemResponse);
      } catch (loadError) {
        if (!active) {
          return;
        }
        setHealth("unreachable");
        setError(
          loadError instanceof Error
            ? loadError.message
            : "Unknown backend error",
        );
      }
    }

    load();

    return () => {
      active = false;
    };
  }, []);

  return (
    <section className="status-card" aria-label="Backend status" title={error ?? undefined}>
      <span className={`status-dot status-${health}`} aria-hidden="true" />
      <div><span>Local API</span><strong>{health}</strong></div>
      {systemInfo ? <div><span>Database</span><strong>{systemInfo.database_exists ? "ready" : "missing"}</strong></div> : null}
      {error ? <span className="sr-only">{error}</span> : null}
    </section>
  );
}
