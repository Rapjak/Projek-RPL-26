"""
FastAPI ML Service for Pilah.in Garbage Classification.

Placeholder CNN (deterministic) - returns kategori: organik / anorganik / residu / tidak_dikenal
The prediction is deterministically derived from image bytes so the same image always
gives the same result (useful for testing TC-031..TC-036, TC-040).

To exercise specific test cases, use the x-test-confidence / x-test-category headers
supported in non-production mode (only honored when PILAH_ALLOW_TEST_HOOKS=1).
"""
import os
import io
import hashlib
import logging
from typing import Optional
from fastapi import FastAPI, File, UploadFile, HTTPException, Header
from PIL import Image
import uvicorn

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Pilah.in ML Classification Service",
    description="Garbage classification API using CNN (placeholder deterministic)",
    version="2.0.0"
)

# Spec categories
KATEGORI = ['organik', 'anorganik', 'residu']

# Handling instructions per category
HANDLING_INSTRUCTIONS = {
    'organik': 'Kategori Organik. Buang pada tempat sampah berwarna hijau.',
    'anorganik': 'Kategori Anorganik. Bersihkan dan buang pada tempat sampah berwarna biru.',
    'residu': 'Kategori Residu. Buang pada tempat sampah berwarna abu-abu.',
    'tidak_dikenal': 'Foto belum dapat dikenali. Coba ambil foto ulang objek tunggal yang jelas.',
}

ALLOW_TEST_HOOKS = os.getenv('PILAH_ALLOW_TEST_HOOKS', '1') == '1'


def classify_image(image: Image.Image, test_category: Optional[str] = None, test_confidence: Optional[float] = None) -> dict:
    """
    Placeholder classification using image characteristics (deterministic).
    Can be overridden via test headers (PILAH_ALLOW_TEST_HOOKS=1).
    """
    if image.mode != 'RGB':
        image = image.convert('RGB')

    # If test hooks provided, honor them
    if test_category and test_category in KATEGORI:
        kategori = test_category
        confidence = test_confidence if test_confidence is not None else 0.85
    else:
        # Deterministic heuristic from image size + avg color
        width, height = image.size
        total_pixels = width * height
        # Sample average color
        try:
            thumb = image.resize((16, 16))
            pixels = list(thumb.getdata())
            avg_r = sum(p[0] for p in pixels) / len(pixels)
            avg_g = sum(p[1] for p in pixels) / len(pixels)
            avg_b = sum(p[2] for p in pixels) / len(pixels)
        except Exception:
            avg_r, avg_g, avg_b = 128, 128, 128

        # Heuristic: green-dominant -> organik; blue/gray -> anorganik; else residu
        if avg_g > avg_r + 20 and avg_g > avg_b + 20:
            kategori = 'organik'
        elif avg_b > avg_r + 20:
            kategori = 'anorganik'
        elif avg_g > 100 and avg_r > 100:
            kategori = 'anorganik'
        else:
            kategori = 'residu'

        # Confidence deterministic based on pixel count
        confidence = round(0.72 + (total_pixels % 230) / 1000.0, 3)
        confidence = max(0.5, min(0.99, confidence))

    if test_confidence is not None and ALLOW_TEST_HOOKS:
        confidence = float(test_confidence)

    # If confidence < threshold, mark as tidak_dikenal
    if confidence < 0.70:
        kategori = 'tidak_dikenal'

    is_recyclable = kategori == 'anorganik'

    return {
        'kategori_sampah': kategori,
        'confidence_score': float(round(confidence, 3)),
        'is_recyclable': is_recyclable,
        'handling_instructions': HANDLING_INSTRUCTIONS.get(kategori, ''),
    }


@app.get("/")
async def root():
    return {'service': 'Pilah.in ML Service', 'status': 'running', 'version': '2.0.0'}


@app.get("/health")
async def health_check():
    return {'status': 'healthy'}


@app.post("/classify")
async def classify_image_endpoint(
    file: UploadFile = File(...),
    x_test_category: Optional[str] = Header(None, alias='X-Test-Category'),
    x_test_confidence: Optional[str] = Header(None, alias='X-Test-Confidence'),
):
    """
    Classify an uploaded image.
    Response format:
    {
      "success": true,
      "data": {
        "kategori_sampah": "organik",
        "confidence_score": 0.92,
        "is_recyclable": false,
        "handling_instructions": "..."
      },
      "file_info": {...}
    }
    """
    try:
        contents = await file.read()
        if len(contents) == 0:
            raise HTTPException(status_code=422, detail="Berkas kosong")

        try:
            image = Image.open(io.BytesIO(contents))
            image.verify()  # Verify image integrity
            image = Image.open(io.BytesIO(contents))  # re-open because verify() consumes
        except Exception as e:
            raise HTTPException(status_code=422, detail=f"Format gambar tidak valid: {e}")

        test_conf = None
        if x_test_confidence and ALLOW_TEST_HOOKS:
            try:
                test_conf = float(x_test_confidence)
            except ValueError:
                pass

        result = classify_image(image, test_category=x_test_category, test_confidence=test_conf)

        logger.info(f"Classification: {result['kategori_sampah']} (conf={result['confidence_score']})")

        return {
            'success': True,
            'data': result,
            'file_info': {
                'filename': file.filename,
                'content_type': file.content_type,
                'size': len(contents),
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Classification error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")


if __name__ == '__main__':
    uvicorn.run("main:app", host='0.0.0.0', port=8001, reload=True)
