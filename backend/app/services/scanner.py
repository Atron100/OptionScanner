from datetime import date, datetime, timezone

from app.repositories.scanner import ScannerRepository
from app.schemas.scanner import (
    RankedScanResult,
    ScanHistoryDetailResponse,
    ScanHistoryListResponse,
    ScanHistorySummary,
    ScanRequest,
    ScanResponse,
)
from app.services.market_data import MarketDataQueryService
from app.services.strategies import StrategyService
from app.strategies.cash_secured_put import CashSecuredPutStrategy
from app.strategies.iron_condor import IronCondorStrategy


class ScannerService:
    def __init__(self, db) -> None:
        self.repository = ScannerRepository(db)
        self.market_data = MarketDataQueryService(db)

    def scan(self, request: ScanRequest) -> ScanResponse:
        candidates = []
        warnings: list[str] = []

        for symbol in request.symbols:
            chain = self.market_data.get_latest_chain(symbol)
            if chain is None:
                warnings.append(f"No chain snapshot found for symbol '{symbol}'.")
                continue
            for strategy_name in request.strategies:
                strategy = self._strategy(strategy_name)
                candidates.extend(strategy.generate(chain))

        total_candidates = len(candidates)
        filtered = [candidate for candidate in candidates if self._matches(candidate, request)]
        filtered.sort(key=self._ranking_key)
        selected = filtered[: request.limit]

        response = ScanResponse(
            generated_at=datetime.now(timezone.utc),
            symbols=request.symbols,
            strategies=request.strategies,
            total_candidates=total_candidates,
            eligible_candidate_count=len(filtered),
            filtered_out_count=total_candidates - len(filtered),
            result_count=len(selected),
            warnings=warnings,
            results=[
                RankedScanResult(
                    rank=index,
                    expected_value=self.expected_value(candidate),
                    candidate=StrategyService.candidate_to_response(candidate),
                )
                for index, candidate in enumerate(selected, start=1)
            ],
        )
        self.repository.create_run(request, response)
        return response

    @staticmethod
    def _strategy(name: str):
        if name == "cash_secured_put":
            return CashSecuredPutStrategy()
        if name == "iron_condor":
            return IronCondorStrategy()
        raise ValueError(f"Unsupported scanner strategy: {name}")

    @classmethod
    def _matches(cls, candidate, request: ScanRequest) -> bool:
        expected_value = cls.expected_value(candidate)
        below_pop = request.minimum_probability_of_profit is not None and (
            candidate.probability_of_profit is None
            or candidate.probability_of_profit < request.minimum_probability_of_profit
        )
        below_roc = request.minimum_return_on_capital is not None and (
            candidate.return_on_capital is None
            or candidate.return_on_capital < request.minimum_return_on_capital
        )
        below_score = request.minimum_score is not None and candidate.score < request.minimum_score
        below_ev = request.minimum_expected_value is not None and (
            expected_value is None or expected_value < request.minimum_expected_value
        )
        above_max_loss = request.maximum_loss is not None and candidate.max_loss > request.maximum_loss
        days_to_expiration = (candidate.expiration_date - date.today()).days
        below_minimum_dte = days_to_expiration < request.minimum_days_to_expiration
        above_maximum_dte = (
            request.maximum_days_to_expiration is not None
            and days_to_expiration > request.maximum_days_to_expiration
        )
        below_credit = candidate.credit < request.minimum_credit
        below_open_interest = request.minimum_open_interest > 0 and (
            candidate.open_interest is None or candidate.open_interest < request.minimum_open_interest
        )
        below_volume = request.minimum_volume > 0 and (
            candidate.volume is None or candidate.volume < request.minimum_volume
        )
        return not any(
            (
                below_pop,
                below_roc,
                below_score,
                below_ev,
                above_max_loss,
                below_minimum_dte,
                above_maximum_dte,
                below_credit,
                below_open_interest,
                below_volume,
            )
        )

    @staticmethod
    def expected_value(candidate) -> float | None:
        if candidate.probability_of_profit is None:
            return None
        probability = candidate.probability_of_profit
        return round(probability * candidate.max_profit - (1 - probability) * candidate.max_loss, 6)

    @classmethod
    def _ranking_key(cls, candidate) -> tuple:
        probability = candidate.probability_of_profit if candidate.probability_of_profit is not None else -1
        return_on_capital = candidate.return_on_capital if candidate.return_on_capital is not None else -1
        expected_value = cls.expected_value(candidate)
        return (
            -candidate.score,
            -(expected_value if expected_value is not None else float("-inf")),
            -probability,
            -return_on_capital,
            candidate.symbol,
            candidate.expiration_date,
            candidate.strike,
        )


class ScannerHistoryService:
    def __init__(self, db) -> None:
        self.repository = ScannerRepository(db)

    def list_runs(self, limit: int) -> ScanHistoryListResponse:
        runs = [
            ScanHistorySummary(
                id=run.id,
                generated_at=run.generated_at,
                symbols=run.symbols.split(",") if run.symbols else [],
                strategies=run.strategies.split(",") if run.strategies else [],
                total_candidates=run.total_candidates,
                result_count=run.result_count,
            )
            for run in self.repository.list_runs(limit)
        ]
        return ScanHistoryListResponse(count=len(runs), runs=runs)

    def get_run(self, run_id: int) -> ScanHistoryDetailResponse | None:
        run = self.repository.get_run(run_id)
        if run is None:
            return None
        return ScanHistoryDetailResponse(
            id=run.id,
            request=ScanRequest.model_validate_json(run.request_json),
            response=ScanResponse.model_validate_json(run.response_json),
        )
