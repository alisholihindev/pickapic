import cv2


def compute_blur_score(path: str) -> float | None:
    """Laplacian variance — lower = blurrier. Returns None on error."""
    try:
        img = cv2.imread(path, cv2.IMREAD_GRAYSCALE)
        if img is None:
            return None
        return float(cv2.Laplacian(img, cv2.CV_64F).var())
    except Exception:
        return None


def is_blurry(score: float | None, threshold: float) -> bool:
    if score is None:
        return False
    return score < threshold
