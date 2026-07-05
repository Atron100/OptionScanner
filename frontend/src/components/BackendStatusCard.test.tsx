import { render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";

import { BackendStatusCard } from "./BackendStatusCard";

vi.stubGlobal(
  "fetch",
  vi.fn((input: RequestInfo | URL) => {
    const url = input.toString();
    if (url.endsWith("/api/v1/health")) {
      return Promise.resolve(
        new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
      );
    }
    return Promise.resolve(
      new Response(
        JSON.stringify({
          app_name: "OptionScanner API",
          environment: "development",
          database_url: "sqlite:///./data/optionscanner.db",
          database_exists: "true",
        }),
        { status: 200 },
      ),
    );
  }),
);

describe("BackendStatusCard", () => {
  it("renders backend health information", async () => {
    render(<BackendStatusCard />);

    await waitFor(() => {
      expect(screen.getByText(/API health:/)).toBeInTheDocument();
      expect(screen.getByText("ok")).toBeInTheDocument();
      expect(screen.getByText("OptionScanner API")).toBeInTheDocument();
    });
  });
});

