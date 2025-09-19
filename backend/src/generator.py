# src/generator.py
import os
import logging
import time
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions

logger = logging.getLogger()

try:
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("Missing GEMINI_API_KEY or GOOGLE_API_KEY environment variable.")
    
    genai.configure(api_key=api_key)
    
    MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")
    model = genai.GenerativeModel(MODEL_NAME)
    logger.info(f"Successfully loaded and configured Gemini model: {MODEL_NAME}")

except Exception as e:
    logger.critical(f"Fatal error during Gemini initialization: {e}")
    logger.critical("The application cannot function without a valid model. Please check your API key and model name.")
    raise

def call_gemini(prompt: str, max_retries: int = 3, min_response_length: int = 10) -> str:
    """
    Sends a prompt to the globally configured Gemini model and returns the text response.
    Includes robust retry logic with exponential backoff for API errors.
    """
    for attempt in range(max_retries):
        try:
            logger.debug(f"Calling Gemini API (Attempt {attempt + 1}/{max_retries}). Prompt snippet: {prompt[:250]}...")
            
            response = model.generate_content(prompt)
            
            if not response.parts:
                text = ""
            else:
                text = "".join(part.text for part in response.parts if hasattr(part, 'text')).strip()

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                reason = response.prompt_feedback.block_reason_message or "Content policy violation"
                logger.error(f"Prompt blocked by Gemini safety settings on attempt {attempt + 1}. Reason: {reason}")
                return f"Error: The prompt was blocked by the safety filter. Reason: {reason}"

            if len(text) < min_response_length:
                logger.warning(f"Gemini returned an empty or short response (len: {len(text)}). Retrying...")
                if attempt == max_retries - 1:
                    logger.error(f"Gemini API call failed after {max_retries} retries: Response consistently too short.")
                    return "Error: Failed to generate a valid response from the AI model after multiple retries."
                time.sleep(2 ** attempt)  # Exponential backoff
                continue

            logger.debug(f"Successfully received response from Gemini. Snippet: {text[:250]}...")
            return text

        except (google_exceptions.ResourceExhausted, google_exceptions.ServiceUnavailable, google_exceptions.DeadlineExceeded) as e:
            logger.warning(f"API rate limit or availability error on attempt {attempt + 1}: {e}. Retrying with backoff...")
            if attempt == max_retries - 1:
                logger.error(f"API calls failed after {max_retries} retries due to persistent API errors.")
                return f"Error: The AI service is currently unavailable or overloaded. Please try again later. Details: {str(e)}"
            time.sleep(2 ** attempt)

        except Exception as e:
            logger.error(f"An unexpected error occurred calling Gemini API on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"All {max_retries} retry attempts failed.")
                return f"Error: An unexpected issue occurred while communicating with the AI model. Details: {str(e)}"
            time.sleep(2 ** attempt)
    
    
    return "Error: AI generation failed after all retry attempts."

call_gemini("say 1 2 3 vive la tunisie")