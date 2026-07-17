from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.scanner import ScanHistoryDetailResponse, ScanHistoryListResponse, ScanRequest, ScanResponse
from app.services.scanner import ScannerHistoryService, ScannerService

router = APIRouter(prefix="/scanner")


@router.post("/scan", response_model=ScanResponse)
def scan(payload: ScanRequest, db: Session = Depends(get_db)) -> ScanResponse:
    return ScannerService(db).scan(payload)


@router.get("/history", response_model=ScanHistoryListResponse)
def scan_history(
    limit: int = Query(default=10, ge=1, le=100),
    db: Session = Depends(get_db),
) -> ScanHistoryListResponse:
    return ScannerHistoryService(db).list_runs(limit)


@router.get("/history/{run_id}", response_model=ScanHistoryDetailResponse)
def scan_history_detail(run_id: int, db: Session = Depends(get_db)) -> ScanHistoryDetailResponse:
    result = ScannerHistoryService(db).get_run(run_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"Scan history run '{run_id}' was not found")
    return result
