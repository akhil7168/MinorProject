"""
Severity Classifier
===================
Maps attack type + confidence to severity levels.
"""


def classify_severity(attack_type: str, confidence: float) -> str:
    """Classify alert severity based on attack type and model confidence."""
    SEVERITY_MAP = {
        "DoS": {"high_conf": "critical", "low_conf": "high"},
        "DDoS": {"high_conf": "critical", "low_conf": "high"},
        "Botnet": {"high_conf": "high", "low_conf": "high"},
        "R2L": {"high_conf": "high", "low_conf": "medium"},
        "BruteForce": {"high_conf": "high", "low_conf": "medium"},
        "PortScan": {"high_conf": "medium", "low_conf": "low"},
        "Probe": {"high_conf": "medium", "low_conf": "low"},
        "WebAttack": {"high_conf": "high", "low_conf": "medium"},
        "U2R": {"high_conf": "critical", "low_conf": "high"},
    }

    threshold = 0.95
    conf_key = "high_conf" if confidence >= threshold else "low_conf"

    if attack_type in SEVERITY_MAP:
        return SEVERITY_MAP[attack_type][conf_key]

    # Default severity based on confidence alone
    if confidence >= 0.95:
        return "high"
    elif confidence >= 0.85:
        return "medium"
    return "low"
