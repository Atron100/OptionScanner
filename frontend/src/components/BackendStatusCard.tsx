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
    <section className="status-card">
      <h2>Backend Status</h2>
      <p>
        API health: <strong>{health}</strong>
      </p>
      {systemInfo ? (
        <dl className="status-grid">
          <div>
            <dt>App</dt>
            <dd>{systemInfo.app_name}</dd>
          </div>
          <div>
            <dt>Environment</dt>
            <dd>{systemInfo.environment}</dd>
          </div>
          <div>
            <dt>Database</dt>
            <dd>{systemInfo.database_exists ? "ready" : "missing"}</dd>
          </div>
        </dl>
      ) : null}
      {error ? <p className="error-text">{error}</p> : null}
    </section>
  );
}
