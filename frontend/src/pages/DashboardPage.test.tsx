import { render, screen } from "@testing-library/react";
import { vi } from "vitest";

import { DashboardPage } from "./DashboardPage";

vi.mock("../components/BackendStatusCard", () => ({
  BackendStatusCard: () => <div>Backend status card</div>,
}));

describe("DashboardPage", () => {
  it("renders the phase 1 heading", () => {
    render(<DashboardPage />);
    expect(screen.getByText("OptionScanner Local Dashboard")).toBeInTheDocument();
  });
});
