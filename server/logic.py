import os
import logging
from pdf_engine import process_pdf

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def process_pdf_translation(input_path: str, output_path: str, source_lang: str = 'PL', target_lang: str = 'UK') -> None:
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Missing file: {input_path}")

    logger.info(f"START: {input_path} -> {target_lang}")
    try:
        process_pdf(input_path, output_path, source_lang, target_lang)
        logger.info("DONE")
    except Exception as e:
        logger.error(f"ENGINE FAIL: {e}")
        raise RuntimeError(str(e))