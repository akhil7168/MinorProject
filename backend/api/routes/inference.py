"""
Inference / Analysis API Routes
================================
Endpoints for file upload analysis and session results retrieval.
"""
import logging
import tempfile
import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from config import get_settings

from database import crud

logger = logging.getLogger("deepshield.api.inference")
router = APIRouter()
settings = get_settings()


@router.post("/analyze/file")
async def analyze_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    models: str = Form(default="ensemble"),
):
    """
    Upload a PCAP or CSV file for analysis.
    Returns session_id immediately — processing runs in background.
    """
    # Validate file type
    allowed_extensions = {".pcap", ".pcapng", ".csv"}
    ext = Path(file.filename).suffix.lower()
    if ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {ext}. Allowed: {allowed_extensions}",
        )

    # Save uploaded file
    upload_dir = settings.DATASETS_DIR / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)
    file_path = upload_dir / file.filename

    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)

    # Determine session type
    session_type = "file_upload" if ext in {".pcap", ".pcapng"} else "batch_csv"

    # Create analysis session
    session = await crud.create_session(
        session_type=session_type,
        filename=file.filename,
    )

    # Parse model selection
    model_list = [m.strip() for m in models.split(",")]

    # Run analysis in background
    background_tasks.add_task(
        _run_analysis, session["id"], str(file_path), model_list, ext
    )

    return {
        "session_id": session["id"],
        "status": "processing",
        "filename": file.filename,
    }


async def _run_analysis(session_id: str, file_path: str, model_list: list, ext: str):
    """Run file analysis in background."""
    try:
        await crud.update_session(session_id, {"status": "processing"})

        from inference.engine import inference_engine

        if ext == ".csv":
            from inference.batch_inferrer import BatchInferrer
            inferrer = BatchInferrer(inference_engine)
            results = await inferrer.analyze_csv(file_path, session_id)
        else:
            from capture.pcap_reader import PcapReader
            reader = PcapReader()
            flows = reader.read_pcap(file_path)
            from inference.batch_inferrer import BatchInferrer
            inferrer = BatchInferrer(inference_engine)
            results = await inferrer.analyze_flows(flows, session_id)

        # Update session with results
        total = results.get("total_flows", 0)
        attacks = results.get("attack_count", 0)
        await crud.update_session(session_id, {
            "status": "completed",
            "total_flows": total,
            "benign_count": total - attacks,
            "attack_count": attacks,
            "attack_breakdown": results.get("attack_breakdown", {}),
            "completed_at": __import__("datetime").datetime.now(
                __import__("datetime").timezone.utc
            ).isoformat(),
        })

    except Exception as e:
        logger.error(f"Analysis failed for session {session_id}: {e}")
        await crud.update_session(session_id, {
            "status": "failed",
            "error_message": str(e),
        })


@router.get("/analyze/{session_id}/results")
async def get_analysis_results(session_id: str, page: int = 1, limit: int = 100):
    """Get paginated detection results for an analysis session."""
    session = await crud.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    detections = await crud.get_session_detections(session_id, page=page, limit=limit)
    breakdown = await crud.get_attack_breakdown(session_id)

    return {
        "session": session,
        "detections": detections,
        "attack_breakdown": breakdown,
        "page": page,
        "limit": limit,
    }


@router.get("/analyze/sessions")
async def list_analysis_sessions(limit: int = 20):
    """List all analysis sessions."""
    sessions = await crud.list_sessions(limit=limit)
    return {"sessions": sessions}
