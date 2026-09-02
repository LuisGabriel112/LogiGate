import os


def vlm_enabled() -> bool:
    return os.getenv("VLM_ENABLED", "true").lower() == "true"
