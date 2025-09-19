# src/toc.py
import logging
import json
from typing import List, Dict, Any

# Configure logging
logger = logging.getLogger()

def generate_toc( # This function is not strictly needed anymore as \tableofcontents is used.
    sections: List[Dict[str, Any]],
    output_file: str = "toc.tex"
) -> str:
    logger.info(f"Generating TOC file (legacy) for {len(sections)} sections: {output_file}")
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("\\tableofcontents\n\\newpage\n")
    return output_file

def _clean_toc_response(response_text: str) -> str:
    response_text = response_text.strip()
    if response_text.startswith("```json"):
        response_text = response_text[len("```json"):].strip()
    elif response_text.startswith("```"):
        response_text = response_text[len("```"):].strip()
    
    if response_text.endswith("```"):
        response_text = response_text[:-len("```")].strip()
    
    last_brace = response_text.rfind(']')
    last_curly = response_text.rfind('}')
    end_index = max(last_brace, last_curly)
    if end_index != -1 and end_index < len(response_text) -1:
        char_after = response_text[end_index+1:].strip()
        if char_after and not char_after.startswith(","):
            logger.warning(f"TOC response might have trailing text after JSON. Trimming. Original end: '{response_text[end_index:end_index+20]}...'")
            response_text = response_text[:end_index+1]

    return response_text

def generate_toc_from_query(query: str, from_generator_func=None) -> List[Dict[str, Any]]:
    """
    Generate a table of contents structure from a user query using an AI model.
    """
    if not from_generator_func:
        from generator import call_gemini
        from_generator_func = call_gemini
        
    prompt = f"""
    Based on the following report description, create a table of contents with main sections and optional subsections.
    Return ONLY a JSON array of sections. Each section object must have a "title" (string) and an optional "subsections" (array of strings or array of objects with "title" field).
    
    **CRITICAL INSTRUCTIONS FOR TITLES:**
    - **TITLES MUST BE PLAIN TEXT STRINGS.**
    - **DO NOT include any special characters like '/', '\', '%', '$', '#', '_', '^', '~', '<', '>' or other formatting/LaTeX commands directly in the title strings.** For example, a title should be "Introduction", NOT "{{Introduction}}", "Introduction {{Details}}".
    - Keep titles concise and relevant to the report description.
    - Do not generate sections for "Abstract", "Acknowledgements", "References", or "Appendices" here; those are handled separately or automatically.
    
    Limit to a maximum of 5-7 main sections. Ensure each main section has a unique title.

    REPORT DESCRIPTION:
    {query}
    
    EXAMPLE RESPONSE FORMAT (return only this JSON without explanation or other text):
    [
      {{
        "title": "Introduction",
        "subsections": ["Background", "Project Objectives", "Scope of Report"]
      }},
      {{
        "title": "Literature Review"
      }},
      {{
        "title": "Methodology",
        "subsections": [ 
            {{ "title": "Data Collection" }}, 
            {{ "title": "System Architecture" }}, 
            {{ "title": "Evaluation Metrics" }}
        ]
      }},
      {{
        "title": "Results and Analysis"
      }},
      {{
        "title": "Discussion"
      }},
      {{
        "title": "Conclusion and Future Work",
        "subsections": ["Summary of Findings", "Limitations", "Recommendations for Future Research"]
      }}
    ]
    """
    
    raw_response = ""
    try:
        raw_response = from_generator_func(prompt)
        if not raw_response:
            logger.error("Received empty response from LLM for TOC generation.")
            raise ValueError("Empty response for TOC")

        cleaned_response = _clean_toc_response(raw_response)
        logger.debug(f"Cleaned TOC response from LLM: {cleaned_response[:500]}...")
        sections = json.loads(cleaned_response)
        
        if not isinstance(sections, list):
            logger.error(f"Parsed TOC is not a list, but {type(sections)}. Raw: {raw_response[:300]}")
            raise ValueError("TOC is not a list")
        
        valid_sections = []
        seen_titles = set()
        for sec_idx, sec_data in enumerate(sections):
            if not isinstance(sec_data, dict):
                logger.warning(f"TOC item at index {sec_idx} is not a dictionary, skipping: {sec_data}")
                continue

            title = sec_data.get("title")
            if not title or not isinstance(title, str) or not title.strip():
                logger.warning(f"TOC item at index {sec_idx} has missing, invalid, or empty title, skipping: {sec_data}")
                continue
            
            title = title.strip() # Basic strip for safety, main_content.clean_title_for_latex_command does heavy lifting

            if title in seen_titles:
                logger.warning(f"Duplicate section title '{title}' found and skipped.")
                continue
            
            processed_section = {"title": title}
            seen_titles.add(title)

            subsections_data = sec_data.get("subsections")
            if isinstance(subsections_data, list):
                processed_subsections = []
                seen_sub_titles = set()
                for sub_idx, sub_item in enumerate(subsections_data):
                    sub_title = None
                    if isinstance(sub_item, str):
                        sub_title = sub_item.strip()
                    elif isinstance(sub_item, dict) and "title" in sub_item and isinstance(sub_item["title"], str):
                        sub_title = sub_item["title"].strip()
                    
                    if sub_title and sub_title not in seen_sub_titles:
                        # For simplicity in current structure, subsections are just titles.
                        # If sub_item was a dict, we could carry `subsubsections` here.
                        # The example shows subsections as strings or objects with title.
                        # main_content.py handles nested structure based on this.
                        if isinstance(sub_item, dict): # if it was a dict, pass it along
                            processed_subsections.append({"title": sub_title, **sub_item})
                        else: # if it was a string
                            processed_subsections.append({"title": sub_title})
                        seen_sub_titles.add(sub_title)
                    elif sub_title: # Duplicate sub_title
                        logger.warning(f"Duplicate subsection title '{sub_title}' in section '{title}' skipped.")
                if processed_subsections:
                    processed_section["subsections"] = processed_subsections
            
            valid_sections.append(processed_section)
        
        if not valid_sections:
            logger.error("No valid sections found after parsing and validation. Using fallback TOC.")
            raise ValueError("No valid sections after cleanup.")

        logger.info(f"Generated TOC structure with {len(valid_sections)} main sections.")
        return valid_sections
        
    except json.JSONDecodeError as je:
        logger.error(f"Error decoding JSON for TOC: {je}")
        logger.error(f"Problematic cleaned response snippet for TOC: {cleaned_response[:500]}...")
        logger.error(f"Original raw response snippet for TOC: {raw_response[:500]}...")
    except Exception as e:
        logger.error(f"Error generating or parsing TOC structure: {e}")
        logger.error(f"Raw response for TOC (if available): {raw_response[:500]}...")
        
    # Fallback TOC if any error occurs
    return [
        {"title": "Introduction", "subsections": [{"title": "Background"}, {"title": "Objectives"}]},
        {"title": "Literature Review"},
        {"title": "Methodology"},
        {"title": "Results"},
        {"title": "Discussion"},
        {"title": "Conclusion"}
    ]

if __name__ == "__main__":
    # Test function
    # logging.basicConfig(level=logging.DEBUG)
    # from generator import call_gemini # Assuming call_gemini is accessible
    # test_query = "A report about AI in autonomous vehicles, focusing on sensor fusion and ethical considerations"
    # generated_sections = generate_toc_from_query(test_query, call_gemini)
    # print(json.dumps(generated_sections, indent=2))
    pass