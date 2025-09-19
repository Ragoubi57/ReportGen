import os
import logging
import traceback
import shutil
from typing import List, Optional, Annotated # Make sure Annotated is here
import colorlog

from fastapi import FastAPI, File, UploadFile, Form, HTTPException # Removed Depends as it's not used directly here
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))
try:
    from src.orchestrator import ReportGenerator
except ImportError as e:
    print(f"ERROR: Could not import ReportGenerator. Ensure 'src' is in PYTHONPATH or accessible. Details: {e}")
    sys.exit(1)
except RuntimeError as e:
    print(f"ERROR: Initialization error (likely API key). Details: {e}")
    sys.exit(1)

app = FastAPI(
    title="AI Report Generator API",
    description="API to generate LaTeX reports using Gemini and RAG.",
    version="1.0.0"
)

origins = [
    "http://localhost:4200",
    "http://127.0.0.1:4200",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

log_level_str = os.getenv("LOG_LEVEL", "INFO").upper()
log_level = getattr(logging, log_level_str, logging.INFO)

console_handler = colorlog.StreamHandler(sys.stdout)
console_handler.setFormatter(colorlog.ColoredFormatter(
    fmt='%(log_color)s%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    log_colors={
        'DEBUG':    'cyan',
        'INFO':     'green',
        'WARNING':  'yellow',
        'ERROR':    'red',
        'CRITICAL': 'bold_red',
    }
))

file_handler = logging.FileHandler("api_report_generator.log", mode='w')
file_handler.setFormatter(logging.Formatter(
    fmt='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s'
))

logging.basicConfig(
    level=log_level,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("api_report_generator.log", mode='w')
    ]
)

logger = logging.getLogger(__name__)
logger.setLevel(log_level)
logger.addHandler(console_handler)
logger.addHandler(file_handler)

REPORTS_OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "build")
API_TEMP_UPLOADS_DIR = os.path.join(REPORTS_OUTPUT_DIR, "api_temp_uploads")

os.makedirs(REPORTS_OUTPUT_DIR, exist_ok=True)
os.makedirs(API_TEMP_UPLOADS_DIR, exist_ok=True)

@app.post("/generate-report", response_class=FileResponse)
async def generate_report_endpoint(
    title: Annotated[str, Form()],
    query: Annotated[str, Form()],
    authors_str_from_form: Annotated[str, Form(alias="authors")],
    date: Annotated[Optional[str], Form()] = None,
    mentors_str_from_form: Annotated[Optional[str], Form(alias="mentors")] = "",
    university: Annotated[Optional[str], Form()] = None,
    logo: Annotated[Optional[UploadFile], File()] = None,
    color: Annotated[Optional[str], Form()] = None,
    no_rag: Annotated[Optional[bool], Form()] = False,
    # --- NEW PARAMETERS for user figure ---
    user_figure: Annotated[Optional[UploadFile], File(description="User-uploaded figure for the report")] = None,
    user_figure_caption: Annotated[Optional[str], Form(description="Caption for the user-uploaded figure")] = ""
    # --- END NEW PARAMETERS ---
):
    logger.info(f"--- Stage 0: /generate-report ENDPOINT HIT for title: '{title}' ---")
    abs_logo_path: Optional[str] = None
    abs_user_figure_path: Optional[str] = None # For user-uploaded figure

    try:
        logger.info(f"--- Stage 1: Handling logo upload if present ---")
        if logo and logo.filename:
            safe_logo_filename = "".join(c for c in logo.filename if c.isalnum() or c in ['.', '_', '-']).strip()
            if not safe_logo_filename: safe_logo_filename = f"uploaded_logo{os.path.splitext(logo.filename)[1]}"
            abs_logo_path = os.path.join(API_TEMP_UPLOADS_DIR, safe_logo_filename)
            with open(abs_logo_path, "wb") as buffer:
                shutil.copyfileobj(logo.file, buffer)
            logger.info(f"--- Stage 1B: Logo saved to: {abs_logo_path} ---")
        else:
            logger.info(f"--- Stage 1B: No logo uploaded or filename empty. ---")

        # --- NEW: Handle User Figure Upload ---
        logger.info(f"--- Stage 1.5: Handling user figure upload if present ---")
        if user_figure and user_figure.filename:
            safe_figure_filename = "".join(c for c in user_figure.filename if c.isalnum() or c in ['.', '_', '-']).strip()
            if not safe_figure_filename:
                safe_figure_filename = f"user_uploaded_figure{os.path.splitext(user_figure.filename)[1]}"
            abs_user_figure_path = os.path.join(API_TEMP_UPLOADS_DIR, safe_figure_filename)
            with open(abs_user_figure_path, "wb") as buffer:
                shutil.copyfileobj(user_figure.file, buffer)
            logger.info(f"--- Stage 1.5B: User figure saved to: {abs_user_figure_path} ---")
        else:
            logger.info(f"--- Stage 1.5B: No user figure uploaded or filename empty. ---")
        # --- END NEW ---

        logger.info(f"--- Stage 2: Parsing authors and mentors ---")
        authors_list = [a.strip() for a in authors_str_from_form.split(',') if a.strip()] if authors_str_from_form else []
        mentors_list = [m.strip() for m in mentors_str_from_form.split(',') if m.strip()] if mentors_str_from_form else []
        logger.info(f"--- Stage 2B: Parsed authors: {authors_list}, Parsed mentors: {mentors_list} ---")

        logger.info(f"--- Stage 3: PRE-INITIALIZATION of ReportGenerator ---")
        report_generator_instance = ReportGenerator(
            output_dir=REPORTS_OUTPUT_DIR,
            temp_dir_name="api_orchestrator_temp",
            use_rag=not no_rag
        )
        logger.info(f"--- Stage 3B: POST-INITIALIZATION of ReportGenerator ---")

        logger.info(f"--- Stage 4: PRE-CALL to report_generator_instance.generate_report ---")
        final_report_path = report_generator_instance.generate_report(
            query=query,
            report_title=title,
            authors=authors_list,
            date=date,
            mentors=mentors_list,
            university=university,
            logo_path=abs_logo_path,
            primary_color=color,
            # --- NEW ARGUMENTS to pass to orchestrator ---
            user_figure_path=abs_user_figure_path,
            user_figure_caption=user_figure_caption
            # --- END NEW ARGUMENTS ---
        )
        logger.info(f"--- Stage 4B: POST-CALL to report_generator_instance.generate_report --- Path: {final_report_path}")

        if os.path.exists(final_report_path):
            base_filename = os.path.basename(final_report_path)
            safe_download_title = "".join(c for c in title if c.isalnum() or c in [' ', '_', '-']).strip().replace(' ', '_')
            if not safe_download_title: safe_download_title = "report"
            download_filename = f"{safe_download_title}{os.path.splitext(base_filename)[1]}"
            media_type = 'application/pdf' if final_report_path.endswith('.pdf') else 'application/x-tex'
            
            logger.info(f"Report generation successful. Sending file: {final_report_path} as {download_filename} with type {media_type}")
            return FileResponse(path=final_report_path, filename=download_filename, media_type=media_type)
        else:
            logger.error(f"Report generation failed post-call: Output file not found at {final_report_path}")
            raise HTTPException(status_code=500, detail="Report generation completed but output file not found on server.")

    except HTTPException as http_exc:
        logger.error(f"HTTPException during report generation: {http_exc.detail} (Status: {http_exc.status_code})")
        raise
    except Exception as e:
        logger.error(f"--- Stage X: UNEXPECTED ERROR in generate_report_endpoint: {e} ---")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"An unexpected error occurred on the server: {str(e)}")
    finally:
        logger.info(f"--- Stage Y: FINALLY block for generate_report_endpoint ---")
        if abs_logo_path and os.path.exists(abs_logo_path):
            try:
                os.remove(abs_logo_path)
                logger.info(f"Cleaned up temporary logo: {abs_logo_path}")
            except Exception as e_clean_logo:
                logger.warning(f"Could not clean up temporary logo {abs_logo_path}: {e_clean_logo}")
        # --- NEW: Cleanup user figure ---
        if abs_user_figure_path and os.path.exists(abs_user_figure_path):
            try:
                os.remove(abs_user_figure_path)
                logger.info(f"Cleaned up temporary user figure: {abs_user_figure_path}")
            except Exception as e_clean_fig:
                logger.warning(f"Could not clean up temporary user figure {abs_user_figure_path}: {e_clean_fig}")
        # --- END NEW ---

@app.get("/health", status_code=200)
async def health_check():
    logger.debug("Health check endpoint called")
    return {"status": "healthy"}

if __name__ == "__main__":
    logger.info("Starting FastAPI app directly using Uvicorn from __main__ (for debugging)")
    import uvicorn
    if not (os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")):
        logger.critical("CRITICAL ERROR: GEMINI_API_KEY or GOOGLE_API_KEY not set. API cannot start.")
        sys.exit(1)
    uvicorn.run("main_api:app", host="0.0.0.0", port=5000, reload=True, log_level="debug")