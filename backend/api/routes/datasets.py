"""
Dataset API Routes
==================
Endpoints for managing datasets: listing, downloading, and stats.
"""
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel

from database import crud

router = APIRouter()


class DownloadRequest(BaseModel):
    dataset_id: str = None


@router.get("/datasets")
async def list_datasets():
    """Get all datasets with their metadata and download status."""
    datasets = await crud.get_all_datasets()

    # If no datasets in DB, seed with registry defaults
    if not datasets:
        from data.downloader import DATASET_REGISTRY
        for name, info in DATASET_REGISTRY.items():
            await crud.upsert_dataset({
                "name": name,
                "display_name": info["display_name"],
                "description": info["description"],
                "num_features": info.get("num_features"),
                "num_classes": info.get("num_classes"),
                "class_labels": info.get("class_labels"),
                "status": "not_downloaded",
                "download_progress": 0,
            })
        datasets = await crud.get_all_datasets()

    return {"datasets": datasets}


@router.post("/datasets/{name}/download")
async def download_dataset(name: str, background_tasks: BackgroundTasks):
    """Trigger dataset download in the background."""
    from data.downloader import DATASET_REGISTRY, download_dataset as do_download

    if name not in DATASET_REGISTRY:
        raise HTTPException(status_code=404, detail=f"Unknown dataset: {name}")

    # Find or create dataset record
    datasets = await crud.get_all_datasets()
    dataset = next((d for d in datasets if d.get("name") == name), None)

    if not dataset:
        dataset = await crud.upsert_dataset({
            "name": name,
            "display_name": DATASET_REGISTRY[name]["display_name"],
            "description": DATASET_REGISTRY[name]["description"],
            "status": "downloading",
            "download_progress": 0,
        })
    else:
        await crud.update_dataset_status(dataset["id"], "downloading", 0)

    # Start background download
    background_tasks.add_task(do_download, name, dataset["id"])

    return {"status": "downloading", "dataset_id": dataset["id"]}


@router.get("/datasets/{dataset_id}/stats")
async def get_dataset_stats(dataset_id: str):
    """Get detailed statistics for a dataset."""
    dataset = await crud.get_dataset(dataset_id)
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    return {
        "dataset": dataset,
        "stats": dataset.get("stats", {}),
        "class_labels": dataset.get("class_labels", {}),
    }
