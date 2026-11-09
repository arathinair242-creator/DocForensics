"""
Visual Forensics Service.
Uses OpenCV, PIL, and scikit-image to analyze document images for suspicious anomalies.
All findings are observations, NOT confirmations of fraud.
"""
import os
import json
import numpy as np
from typing import List, Dict, Any

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image, ImageChops, ImageFilter, ImageEnhance
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from skimage import filters, measure
    SKIMAGE_AVAILABLE = True
except ImportError:
    SKIMAGE_AVAILABLE = False

try:
    import fitz
    PYMUPDF_AVAILABLE = True
except ImportError:
    PYMUPDF_AVAILABLE = False

ANNOTATED_DIR = "uploads/annotated"


def pdf_first_page_to_image(file_path: str, dpi: int = 150) -> np.ndarray:
    """Convert first page of PDF to numpy array."""
    if not PYMUPDF_AVAILABLE:
        return None
    try:
        doc = fitz.open(file_path)
        page = doc[0]
        mat = fitz.Matrix(dpi / 72, dpi / 72)
        pix = page.get_pixmap(matrix=mat, colorspace=fitz.csRGB)
        doc.close()
        img_array = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, 3)
        return img_array
    except Exception:
        return None


def load_image(file_path: str) -> np.ndarray:
    """Load image from file path as BGR numpy array."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".pdf":
        return pdf_first_page_to_image(file_path)
    if CV2_AVAILABLE:
        img = cv2.imread(file_path)
        return img
    if PIL_AVAILABLE:
        pil_img = Image.open(file_path).convert("RGB")
        return np.array(pil_img)[:, :, ::-1]  # RGB to BGR
    return None


def error_level_analysis(file_path: str) -> Dict:
    """
    Error Level Analysis (ELA): Re-save at lower quality and compute difference.
    High ELA values in specific regions may indicate localized resampling/insertion.
    OBSERVATION ONLY - not conclusive proof of manipulation.
    """
    if not PIL_AVAILABLE:
        return {"findings": [], "ela_map": None}

    ext = os.path.splitext(file_path)[1].lower()
    findings = []
    try:
        if ext == ".pdf":
            img_arr = pdf_first_page_to_image(file_path, dpi=100)
            if img_arr is None:
                return {"findings": [], "ela_map": None}
            pil_img = Image.fromarray(img_arr)
        else:
            pil_img = Image.open(file_path).convert("RGB")

        # Save at reduced quality and compute diff
        import io
        buffer = io.BytesIO()
        pil_img.save(buffer, "JPEG", quality=75)
        buffer.seek(0)
        recompressed = Image.open(buffer)

        ela_img = ImageChops.difference(pil_img, recompressed)
        ela_arr = np.array(ela_img)
        ela_enhanced = np.clip(ela_arr * 10, 0, 255).astype(np.uint8)

        # Find high-ELA regions
        mean_ela = float(np.mean(ela_arr))
        std_ela = float(np.std(ela_arr))
        threshold = mean_ela + 2.5 * std_ela

        if threshold > 0 and CV2_AVAILABLE:
            gray_ela = cv2.cvtColor(ela_enhanced, cv2.COLOR_RGB2GRAY)
            _, thresh = cv2.threshold(gray_ela, int(min(threshold * 10, 200)), 255, cv2.THRESH_BINARY)
            contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            suspicious_contours = [c for c in contours if cv2.contourArea(c) > 500]

            for i, cnt in enumerate(suspicious_contours[:3]):
                x, y, w, h = cv2.boundingRect(cnt)
                area = cv2.contourArea(cnt)
                img_area = pil_img.width * pil_img.height
                area_pct = area / img_area * 100

                if area_pct > 0.5:
                    findings.append({
                        "description": f"ELA detected a region with atypical resampling characteristics at position ({x},{y}), area {w}×{h}px. This may indicate localized image editing or insertion. Independent verification is required.",
                        "severity": "Medium" if area_pct > 2 else "Low",
                        "confidence": min(0.45 + area_pct * 0.05, 0.75),
                        "method": "Error Level Analysis (ELA)",
                        "bbox": [x, y, w, h],
                        "page": 1,
                        "evidence": f"ELA anomaly region #{i+1}: {w}×{h}px, area={area_pct:.1f}% of document"
                    })

        return {"findings": findings[:3]}

    except Exception as e:
        return {"findings": []}


def analyze_noise_uniformity(img_bgr: np.ndarray) -> List[Dict]:
    """
    Analyze noise distribution uniformity.
    Regions with significantly different noise levels may indicate splicing.
    """
    findings = []
    if not CV2_AVAILABLE or img_bgr is None:
        return findings
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        block_size = max(h // 4, 50)

        noise_map = []
        for row in range(0, h - block_size, block_size):
            for col in range(0, w - block_size, block_size):
                block = gray[row:row+block_size, col:col+block_size]
                lap = cv2.Laplacian(block.astype(np.float64), cv2.CV_64F)
                noise_map.append((float(np.std(lap)), row, col, block_size, block_size))

        if len(noise_map) >= 4:
            noise_values = [n[0] for n in noise_map]
            mean_noise = np.mean(noise_values)
            std_noise = np.std(noise_values)

            for noise_val, row, col, bw, bh in noise_map:
                if noise_val > mean_noise + 2.5 * std_noise and noise_val > 5:
                    findings.append({
                        "description": f"Region at ({col},{row}) exhibits significantly higher noise variance ({noise_val:.1f}) compared to document mean ({mean_noise:.1f}). This observation may warrant further examination.",
                        "severity": "Low",
                        "confidence": 0.45,
                        "method": "Noise Uniformity Analysis",
                        "bbox": [col, row, bw, bh],
                        "page": 1,
                        "evidence": f"Noise level {noise_val:.1f} vs mean {mean_noise:.1f} (σ={std_noise:.1f})"
                    })
    except Exception:
        pass
    return findings[:2]


def analyze_text_regions(img_bgr: np.ndarray) -> List[Dict]:
    """
    Detect unusual text region characteristics using edge detection and morphological ops.
    May indicate inconsistent font rendering or overwritten content.
    """
    findings = []
    if not CV2_AVAILABLE or img_bgr is None:
        return findings
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        # Apply Gaussian blur and edge detection
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 50, 150)

        # Morphological dilation to connect text regions
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 3))
        dilated = cv2.dilate(edges, kernel, iterations=1)

        contours, _ = cv2.findContours(dilated, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        text_regions = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            aspect_ratio = w / h if h > 0 else 0
            if w > 50 and h > 8 and h < 60 and aspect_ratio > 2:
                region_gray = gray[y:y+h, x:x+w]
                local_std = float(np.std(region_gray))
                text_regions.append((x, y, w, h, local_std))

        if len(text_regions) > 5:
            stds = [r[4] for r in text_regions]
            mean_std = np.mean(stds)
            std_std = np.std(stds)

            outliers = [(x, y, w, h, s) for x, y, w, h, s in text_regions
                        if s > mean_std + 2.0 * std_std]

            for x, y, w, h, local_std in outliers[:2]:
                findings.append({
                    "description": f"Text region at ({x},{y}) exhibits inconsistent pixel intensity characteristics (σ={local_std:.1f} vs document avg {mean_std:.1f}). This may indicate inconsistent font rendering, image overlay, or content modification.",
                    "severity": "Low",
                    "confidence": 0.4,
                    "method": "Text Region Analysis (Edge Detection)",
                    "bbox": [x, y, w, h],
                    "page": 1,
                    "evidence": f"Pixel intensity deviation: {local_std:.1f} (expected: {mean_std:.1f}±{std_std:.1f})"
                })
    except Exception:
        pass
    return findings


def analyze_alignment(img_bgr: np.ndarray) -> List[Dict]:
    """
    Detect alignment anomalies using Hough line detection.
    Documents with consistent fonts show regular line patterns.
    """
    findings = []
    if not CV2_AVAILABLE or img_bgr is None:
        return findings
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        _, binary = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
        lines = cv2.HoughLinesP(binary, 1, np.pi / 180, threshold=80,
                                 minLineLength=100, maxLineGap=10)
        if lines is not None and len(lines) > 3:
            angles = []
            for line in lines:
                x1, y1, x2, y2 = line[0]
                if x2 - x1 != 0:
                    angle = np.degrees(np.arctan2(y2 - y1, x2 - x1))
                    angles.append(angle)

            if angles:
                mean_angle = np.mean(angles)
                std_angle = np.std(angles)

                if std_angle > 3.0:  # > 3 degrees spread is unusual
                    findings.append({
                        "description": f"Document lines show angular variance of {std_angle:.1f}°. Typically, printed documents have consistent text alignment. High variance may indicate mixed source materials or document assembly from multiple sources.",
                        "severity": "Low",
                        "confidence": 0.4,
                        "method": "Hough Line Alignment Analysis",
                        "bbox": [],
                        "page": 1,
                        "evidence": f"Mean text angle: {mean_angle:.1f}°, Angular std deviation: {std_angle:.1f}°"
                    })
    except Exception:
        pass
    return findings


def detect_signature_regions(img_bgr: np.ndarray) -> List[Dict]:
    """
    Detect potential signature regions based on ink blob characteristics.
    """
    findings = []
    if not CV2_AVAILABLE or img_bgr is None:
        return findings
    try:
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        h, w = gray.shape
        lower_quarter = gray[int(h * 0.65):, :]
        _, binary = cv2.threshold(lower_quarter, 100, 255, cv2.THRESH_BINARY_INV)
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        sig_candidates = []
        for cnt in contours:
            x, y, cw, ch = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)
            if area > 500 and cw > 30 and ch > 10 and cw / ch < 10:
                hull = cv2.convexHull(cnt)
                hull_area = cv2.contourArea(hull)
                if hull_area > 0:
                    solidity = area / hull_area
                    if 0.2 < solidity < 0.8:
                        sig_candidates.append((x, y + int(h * 0.65), cw, ch, solidity))

        if sig_candidates:
            findings.append({
                "description": f"Detected {len(sig_candidates)} potential signature region(s) in the lower portion of the document. Signature placement and characteristics should be verified by an authorized investigator.",
                "severity": "Low",
                "confidence": 0.5,
                "method": "Signature Region Detection",
                "bbox": list(sig_candidates[0][:4]),
                "page": 1,
                "evidence": f"Signature-like region: {sig_candidates[0][2]}×{sig_candidates[0][3]}px, solidity={sig_candidates[0][4]:.2f}"
            })
    except Exception:
        pass
    return findings


def draw_annotations(img_bgr: np.ndarray, findings: List[Dict], doc_id: int) -> str:
    """Draw bounding boxes on image and save annotated version."""
    if not CV2_AVAILABLE or img_bgr is None:
        return ""
    try:
        annotated = img_bgr.copy()
        colors = {
            "Low": (0, 200, 255),      # Orange
            "Medium": (0, 100, 255),   # Orange-red
            "High": (0, 50, 220),      # Red
            "Critical": (0, 0, 180),   # Dark red
        }
        for finding in findings:
            bbox = finding.get("bbox", [])
            if len(bbox) == 4:
                x, y, w, h = [int(v) for v in bbox]
                color = colors.get(finding.get("severity", "Low"), (0, 200, 255))
                cv2.rectangle(annotated, (x, y), (x + w, y + h), color, 2)
                label = finding.get("method", "Anomaly")[:25]
                cv2.putText(annotated, label, (x, max(y - 5, 10)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)

        os.makedirs(ANNOTATED_DIR, exist_ok=True)
        out_path = os.path.join(ANNOTATED_DIR, f"annotated_{doc_id}.png")
        cv2.imwrite(out_path, annotated)
        return out_path
    except Exception:
        return ""


def analyze(file_path: str, doc_id: int) -> Dict:
    """
    Main visual forensics entry point.
    Returns findings (list of observations) and annotated image path.
    """
    all_findings = []
    annotated_path = ""

    try:
        img_bgr = load_image(file_path)

        if CV2_AVAILABLE and PIL_AVAILABLE:
            # ELA
            ela_results = error_level_analysis(file_path)
            all_findings.extend(ela_results.get("findings", []))

        if img_bgr is not None:
            # Noise analysis
            all_findings.extend(analyze_noise_uniformity(img_bgr))
            # Text region analysis
            all_findings.extend(analyze_text_regions(img_bgr))
            # Alignment
            all_findings.extend(analyze_alignment(img_bgr))
            # Signature detection
            all_findings.extend(detect_signature_regions(img_bgr))
            # Create annotated image
            annotated_path = draw_annotations(img_bgr, all_findings, doc_id)

    except Exception as e:
        pass

    # Cap findings to keep relevant only
    return {
        "findings": all_findings[:8],
        "annotated_path": annotated_path
    }
