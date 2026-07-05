import { BackendStatusCard } from "../components/BackendStatusCard";

export function DashboardPage() {
  return (
    <main className="page-shell">
      <section className="hero-panel">
        <p className="eyebrow">Phase 1</p>
        <h1>OptionScanner Local Dashboard</h1>
        <p className="hero-copy">
          This first milestone proves the local web stack, configuration, and
          database wiring before we add broker integrations and scan logic.
        </p>
      </section>
      <BackendStatusCard />
    </main>
  );
}

