from sqlalchemy import select

from app.db.models import ScanRun
from app.schemas.scanner import ScanRequest, ScanResponse


class ScannerRepository:
    def __init__(self, db) -> None:
        self.db = db

    def create_run(self, request: ScanRequest, response: ScanResponse) -> ScanRun:
        run = ScanRun(
            generated_at=response.generated_at,
            symbols=",".join(response.symbols),
            strategies=",".join(response.strategies),
            total_candidates=response.total_candidates,
            result_count=response.result_count,
            request_json=request.model_dump_json(exclude_none=True),
            response_json=response.model_dump_json(),
        )
        self.db.add(run)
        self.db.commit()
        self.db.refresh(run)
        return run

    def list_runs(self, limit: int) -> list[ScanRun]:
        statement = select(ScanRun).order_by(ScanRun.generated_at.desc(), ScanRun.id.desc()).limit(limit)
        return list(self.db.execute(statement).scalars())

    def get_run(self, run_id: int) -> ScanRun | None:
        return self.db.get(ScanRun, run_id)
