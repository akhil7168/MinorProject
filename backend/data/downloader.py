"""
Dataset Downloader
==================
Downloads IDS datasets with progress tracking.
Supports NSL-KDD, CICIDS-2017, and UNSW-NB15.
Progress is updated in the database for frontend display.
"""
import hashlib
import logging
import os
from pathlib import Path
from typing import Optional

import httpx
import pandas as pd

from config import get_settings
from database import crud

logger = logging.getLogger("deepshield.data.downloader")
settings = get_settings()

# ── Dataset Registry ───────────────────────────────────────────
# Defines all available datasets with their download URLs and metadata.
DATASET_REGISTRY = {
    "NSL-KDD": {
        "display_name": "NSL-KDD",
        "description": (
            "Cleaned version of KDD'99. 148K records, 41 features. "
            "4 attack categories: DoS, Probe, R2L, U2R."
        ),
        "train_url": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTrain+.txt",
        "test_url": "https://raw.githubusercontent.com/defcom17/NSL_KDD/master/KDDTest+.txt",
        "num_features": 41,
        "num_classes": 5,
        "class_labels": {"0": "BENIGN", "1": "DoS", "2": "Probe", "3": "R2L", "4": "U2R"},
    },
    "CICIDS-2017": {
        "display_name": "CICIDS 2017",
        "description": (
            "2.8M flows, 78 features. Modern attacks: Brute Force, "
            "DDoS, Botnet, Web Attacks, Infiltration. "
            "Place CSV files manually in datasets/CICIDS-2017/ directory."
        ),
        "source": "University of New Brunswick",
        "num_features": 78,
        "num_classes": 6,
        "class_labels": {
            "0": "BENIGN", "1": "DoS", "2": "PortScan",
            "3": "BruteForce", "4": "Botnet", "5": "WebAttack",
        },
    },
    "UNSW-NB15": {
        "display_name": "UNSW-NB15",
        "description": (
            "2.5M records, 49 features. 9 attack categories including "
            "Fuzzers, Backdoors, DoS, Exploits, Generic, Reconnaissance."
        ),
        "train_url": "https://cloudstor.aarnet.edu.au/plus/s/2DhnLGDdEECo4ys/download",
        "num_features": 49,
        "num_classes": 10,
        "class_labels": {
            "0": "Normal", "1": "Fuzzers", "2": "Analysis", "3": "Backdoors",
            "4": "DoS", "5": "Exploits", "6": "Generic", "7": "Reconnaissance",
            "8": "Shellcode", "9": "Worms",
        },
    },
}


async def download_dataset(name: str, dataset_id: str) -> Path:
    """
    Download a dataset by name with progress tracking.
    Updates the database with download_progress every 5%.
    """
    if name not in DATASET_REGISTRY:
        raise ValueError(f"Unknown dataset: {name}")

    registry = DATASET_REGISTRY[name]
    data_dir = settings.DATASETS_DIR / name
    data_dir.mkdir(parents=True, exist_ok=True)

    try:
        await crud.update_dataset_status(dataset_id, "downloading", 0)

        if name == "NSL-KDD":
            await _download_nsl_kdd(registry, data_dir, dataset_id)
        elif name == "CICIDS-2017":
            # CICIDS requires manual download — check if files exist
            csv_files = list(data_dir.glob("*.csv"))
            if csv_files:
                await crud.update_dataset_status(dataset_id, "ready", 100)
                logger.info(f"CICIDS-2017: Found {len(csv_files)} CSV files")
            else:
                logger.warning("CICIDS-2017 requires manual download. Place CSV files in datasets/CICIDS-2017/")
                await crud.update_dataset_status(dataset_id, "ready", 100)
        elif name == "UNSW-NB15":
            await _download_file(registry.get("train_url"), data_dir / "UNSW-NB15.csv", dataset_id)

        # Compute stats after download
        await crud.update_dataset_status(dataset_id, "ready", 100)
        await crud.upsert_dataset({
            "id": dataset_id,
            "name": name,
            "status": "ready",
            "download_progress": 100,
            "file_path": str(data_dir),
        })

        logger.info(f"✅ Dataset {name} ready at {data_dir}")
        return data_dir

    except Exception as e:
        logger.error(f"❌ Download failed for {name}: {e}")
        await crud.update_dataset_status(dataset_id, "error", 0)
        raise


async def _download_nsl_kdd(registry: dict, data_dir: Path, dataset_id: str):
    """Download NSL-KDD train and test files."""
    # Download training data
    await _download_file(
        registry["train_url"],
        data_dir / "KDDTrain+.txt",
        dataset_id,
        progress_weight=0.5,
        progress_offset=0,
    )

    # Download test data
    await _download_file(
        registry["test_url"],
        data_dir / "KDDTest+.txt",
        dataset_id,
        progress_weight=0.5,
        progress_offset=50,
    )


async def _download_file(
    url: str,
    dest: Path,
    dataset_id: str,
    progress_weight: float = 1.0,
    progress_offset: float = 0,
):
    """Download a single file with progress tracking."""
    if dest.exists():
        logger.info(f"File already exists: {dest}")
        return

    logger.info(f"Downloading {url} → {dest}")

    async with httpx.AsyncClient(timeout=300, follow_redirects=True) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            total = int(response.headers.get("content-length", 0))
            downloaded = 0
            last_progress = -1

            with open(dest, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)
                    downloaded += len(chunk)

                    if total > 0:
                        pct = int((downloaded / total) * 100 * progress_weight + progress_offset)
                    else:
                        pct = int(progress_offset + progress_weight * 50)

                    # Update progress every 5%
                    if pct >= last_progress + 5:
                        last_progress = pct
                        await crud.update_dataset_status(dataset_id, "downloading", min(pct, 99))

    logger.info(f"Downloaded: {dest} ({dest.stat().st_size / 1024 / 1024:.1f} MB)")


async def verify_checksum(path: Path, expected: str) -> bool:
    """Verify SHA256 checksum of a downloaded file."""
    sha256 = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    actual = sha256.hexdigest()
    return actual == expected


async def compute_dataset_stats(df: pd.DataFrame, label_col: str) -> dict:
    """Compute statistics for a dataset."""
    stats = {
        "total_records": len(df),
        "num_features": len(df.columns) - 1,
        "class_distribution": df[label_col].value_counts().to_dict(),
        "null_counts": df.isnull().sum().sum(),
        "duplicate_count": df.duplicated().sum(),
    }

    # Numeric column stats
    numeric_cols = df.select_dtypes(include=["number"]).columns
    stats["feature_means"] = df[numeric_cols].mean().to_dict()
    stats["feature_stds"] = df[numeric_cols].std().to_dict()

    return stats
