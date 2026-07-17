import { render, screen } from "@testing-library/react";

import { PayoffChart } from "./PayoffChart";

describe("PayoffChart", () => {
  it("formats complete axis values and separates profit from loss", () => {
    const { container } = render(
      <PayoffChart
        symbol="TEST"
        breakEven={34}
        upperBreakEven={null}
        points={[
          { underlying_price: 30, profit_loss: -13 },
          { underlying_price: 34, profit_loss: 0 },
          { underlying_price: 38, profit_loss: 13 },
        ]}
      />,
    );

    expect(screen.getAllByText("34.00").length).toBeGreaterThan(0);
    expect(screen.getByText("13.00")).toBeInTheDocument();
    expect(screen.getByText("-13.00")).toBeInTheDocument();
    expect(screen.getByText("0.00")).toBeInTheDocument();
    expect(container.querySelector(".payoff-profit-line")).toBeInTheDocument();
    expect(container.querySelector(".payoff-loss-line")).toBeInTheDocument();
  });
});
