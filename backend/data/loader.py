"""
Dataset Loader
==============
Loads and unifies all IDS datasets into a common schema.
Each dataset has different column formats — this module normalizes them all.

Common output: (X: np.ndarray float32, y: np.ndarray int32, feature_names: list[str])
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

logger = logging.getLogger("deepshield.data.loader")

# ── Unified Label Mapping ──────────────────────────────────────
# Maps all attack labels across datasets to consistent integer classes.
UNIFIED_LABELS = {
    "BENIGN": 0,
    "Normal": 0,
    "normal": 0,
    # DoS variants → 1
    "DoS": 1,
    "DDoS": 1,
    "dos": 1,
    "DoS Hulk": 1,
    "DoS GoldenEye": 1,
    "DoS slowloris": 1,
    "DoS Slowhttptest": 1,
    "Heartbleed": 1,
    # Probe/Scan → 2
    "Probe": 2,
    "PortScan": 2,
    "probe": 2,
    "Reconnaissance": 2,
    # R2L/BruteForce → 3
    "R2L": 3,
    "BruteForce": 3,
    "r2l": 3,
    "FTP-Patator": 3,
    "SSH-Patator": 3,
    "Infiltration": 3,
    # Botnet/Malware → 4
    "Botnet": 4,
    "Bot": 4,
    "Generic": 4,
    "Backdoors": 4,
    "Backdoor": 4,
    "Shellcode": 4,
    "Worms": 4,
    "Fuzzers": 4,
    "Exploits": 4,
    "Analysis": 4,
    # WebAttack/U2R → 5
    "WebAttack": 5,
    "Web Attack – Brute Force": 5,
    "Web Attack – XSS": 5,
    "Web Attack – Sql Injection": 5,
    "U2R": 5,
    "u2r": 5,
}

CLASS_NAMES = {0: "BENIGN", 1: "DoS", 2: "Probe", 3: "R2L", 4: "Botnet", 5: "WebAttack"}

# NSL-KDD specific attack to category mapping
NSL_KDD_ATTACKS = {
    "normal": "normal",
    "back": "DoS", "land": "DoS", "neptune": "DoS", "pod": "DoS",
    "smurf": "DoS", "teardrop": "DoS", "mailbomb": "DoS", "apache2": "DoS",
    "processtable": "DoS", "udpstorm": "DoS",
    "ipsweep": "Probe", "nmap": "Probe", "portsweep": "Probe", "satan": "Probe",
    "mscan": "Probe", "saint": "Probe",
    "ftp_write": "R2L", "guess_passwd": "R2L", "imap": "R2L", "multihop": "R2L",
    "phf": "R2L", "spy": "R2L", "warezclient": "R2L", "warezmaster": "R2L",
    "sendmail": "R2L", "named": "R2L", "snmpgetattack": "R2L", "snmpguess": "R2L",
    "xlock": "R2L", "xsnoop": "R2L", "worm": "R2L",
    "buffer_overflow": "U2R", "loadmodule": "U2R", "perl": "U2R",
    "rootkit": "U2R", "httptunnel": "U2R", "ps": "U2R",
    "sqlattack": "U2R", "xterm": "U2R",
}

# NSL-KDD column names (the dataset has no header)
NSL_KDD_COLUMNS = [
    "duration", "protocol_type", "service", "flag", "src_bytes", "dst_bytes",
    "land", "wrong_fragment", "urgent", "hot", "num_failed_logins", "logged_in",
    "num_compromised", "root_shell", "su_attempted", "num_root",
    "num_file_creations", "num_shells", "num_access_files", "num_outbound_cmds",
    "is_host_login", "is_guest_login", "count", "srv_count", "serror_rate",
    "srv_serror_rate", "rerror_rate", "srv_rerror_rate", "same_srv_rate",
    "diff_srv_rate", "srv_diff_host_rate", "dst_host_count", "dst_host_srv_count",
    "dst_host_same_srv_rate", "dst_host_diff_srv_rate", "dst_host_same_src_port_rate",
    "dst_host_srv_diff_host_rate", "dst_host_serror_rate", "dst_host_srv_serror_rate",
    "dst_host_rerror_rate", "dst_host_srv_rerror_rate", "label", "difficulty_level",
]


def load_nsl_kdd(data_dir: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load NSL-KDD dataset.
    Handles: categorical encoding of protocol_type, service, flag columns.
    """
    train_path = data_dir / "KDDTrain+.txt"
    test_path = data_dir / "KDDTest+.txt"

    dfs = []
    for path in [train_path, test_path]:
        if path.exists():
            df = pd.read_csv(path, header=None, names=NSL_KDD_COLUMNS)
            dfs.append(df)

    if not dfs:
        raise FileNotFoundError(f"No NSL-KDD data files found in {data_dir}")

    df = pd.concat(dfs, ignore_index=True)

    # Drop difficulty level column (not a feature)
    df = df.drop("difficulty_level", axis=1)

    # Map attack names to categories
    df["label"] = df["label"].str.strip().map(
        lambda x: NSL_KDD_ATTACKS.get(x, "normal")
    )
    df["label"] = df["label"].map(UNIFIED_LABELS).fillna(0).astype(int)

    # One-hot encode categorical features
    categorical_cols = ["protocol_type", "service", "flag"]
    df = pd.get_dummies(df, columns=categorical_cols, drop_first=False)

    # Separate features and labels
    y = df["label"].values.astype(np.int32)
    X = df.drop("label", axis=1).values.astype(np.float32)
    feature_names = [c for c in df.columns if c != "label"]

    logger.info(f"Loaded NSL-KDD: {X.shape[0]} samples, {X.shape[1]} features, {len(np.unique(y))} classes")
    return X, y, feature_names


def load_cicids2017(data_dir: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load CICIDS-2017 dataset from multiple CSV files.
    Handles: whitespace in column names, NaN/Inf values, label mapping.
    """
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding="utf-8", low_memory=False)
            dfs.append(df)
            logger.info(f"  Loaded {csv_file.name}: {len(df)} rows")
        except Exception as e:
            logger.warning(f"  Failed to load {csv_file.name}: {e}")

    df = pd.concat(dfs, ignore_index=True)

    # Strip whitespace from column names (CICIDS has leading spaces)
    df.columns = df.columns.str.strip()

    # Identify the label column
    label_col = None
    for col in ["Label", "label", " Label"]:
        if col in df.columns:
            label_col = col
            break
    if label_col is None:
        raise ValueError("Could not find label column in CICIDS-2017 data")

    # Drop non-feature columns
    drop_cols = ["Flow ID", "Source IP", "Src IP", "Destination IP", "Dst IP",
                 "Timestamp", "Source Port", "Destination Port"]
    for col in drop_cols:
        if col in df.columns:
            df = df.drop(col, axis=1)

    # Map labels
    df[label_col] = df[label_col].str.strip().map(
        lambda x: UNIFIED_LABELS.get(x, 0)
    )

    # Handle infinities and NaN
    df = df.replace([np.inf, -np.inf], np.nan)
    df = df.dropna()

    y = df[label_col].values.astype(np.int32)
    X = df.drop(label_col, axis=1)

    # Convert all to numeric
    for col in X.columns:
        X[col] = pd.to_numeric(X[col], errors="coerce")
    X = X.fillna(0)

    feature_names = list(X.columns)
    X = X.values.astype(np.float32)

    logger.info(f"Loaded CICIDS-2017: {X.shape[0]} samples, {X.shape[1]} features, {len(np.unique(y))} classes")
    return X, y, feature_names


def load_unsw_nb15(data_dir: Path) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """Load UNSW-NB15 dataset."""
    csv_files = sorted(data_dir.glob("*.csv"))
    if not csv_files:
        raise FileNotFoundError(f"No CSV files found in {data_dir}")

    dfs = []
    for csv_file in csv_files:
        try:
            df = pd.read_csv(csv_file, encoding="utf-8", low_memory=False)
            dfs.append(df)
        except Exception as e:
            logger.warning(f"Failed to load {csv_file.name}: {e}")

    df = pd.concat(dfs, ignore_index=True)
    df.columns = df.columns.str.strip()

    # Find label column
    label_col = None
    for col in ["attack_cat", "label", "Label"]:
        if col in df.columns:
            label_col = col
            break

    if label_col is None:
        # Use binary label column if available
        if "label" in df.columns:
            label_col = "label"
        else:
            raise ValueError("No label column found in UNSW-NB15")

    # Map labels
    if df[label_col].dtype == object:
        df[label_col] = df[label_col].str.strip().map(
            lambda x: UNIFIED_LABELS.get(x, 0)
        )
    else:
        # Binary: 0 = normal, 1 = attack
        pass

    # Drop non-feature columns
    drop_cols = ["id", "attack_cat", "label"] if label_col == "attack_cat" else ["id"]
    for col in drop_cols:
        if col in df.columns and col != label_col:
            df = df.drop(col, axis=1)

    # One-hot encode categorical
    cat_cols = df.select_dtypes(include=["object"]).columns.tolist()
    if label_col in cat_cols:
        cat_cols.remove(label_col)
    if cat_cols:
        df = pd.get_dummies(df, columns=cat_cols, drop_first=False)

    df = df.replace([np.inf, -np.inf], np.nan).dropna()

    y = df[label_col].values.astype(np.int32)
    X = df.drop(label_col, axis=1)
    feature_names = list(X.columns)
    X = X.values.astype(np.float32)

    logger.info(f"Loaded UNSW-NB15: {X.shape[0]} samples, {X.shape[1]} features")
    return X, y, feature_names


def load_dataset(name: str, data_dir: Path = None) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Dispatcher: Load a dataset by name.
    Returns (X, y, feature_names) in the unified format.
    """
    if data_dir is None:
        from config import get_settings
        data_dir = get_settings().DATASETS_DIR / name

    loaders = {
        "NSL-KDD": load_nsl_kdd,
        "CICIDS-2017": load_cicids2017,
        "UNSW-NB15": load_unsw_nb15,
    }

    if name not in loaders:
        raise ValueError(f"Unknown dataset: {name}. Available: {list(loaders.keys())}")

    return loaders[name](data_dir)


def load_combined(names: list[str], data_dir: Path = None) -> tuple[np.ndarray, np.ndarray, list[str]]:
    """
    Load multiple datasets, align feature spaces, concatenate.
    Only keeps features common to all selected datasets.
    """
    all_X, all_y, all_features = [], [], []

    for name in names:
        X, y, features = load_dataset(name, data_dir)
        all_X.append((X, features))
        all_y.append(y)
        all_features.append(set(features))

    # Find common features
    common = set.intersection(*all_features) if all_features else set()

    if not common:
        logger.warning("No common features across datasets. Using first dataset only.")
        return all_X[0][0], all_y[0], list(all_X[0][1])

    common_list = sorted(list(common))

    # Align all datasets to common features
    aligned_X = []
    for X, features in all_X:
        feature_idx = [features.index(f) for f in common_list if f in features]
        aligned_X.append(X[:, feature_idx])

    X_combined = np.concatenate(aligned_X, axis=0)
    y_combined = np.concatenate(all_y, axis=0)

    logger.info(f"Combined {len(names)} datasets: {X_combined.shape[0]} samples, {len(common_list)} common features")
    return X_combined, y_combined, common_list
