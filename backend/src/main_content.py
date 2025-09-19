import logging
import re
from typing import List, Dict, Any, Optional
from latex_utils import process_llm_output_for_latex, escape_latex_special_chars, clean_title_for_latex_command
import time
logger = logging.getLogger()

def generate_section_content(section_title: str, full_query: str, from_generator_func) -> str:
    prompt = f"""You are an academic writer for a LaTeX report on: "{full_query}". Write the content for the section: "{section_title}".
INSTRUCTIONS: Use simple markdown for formatting (`**bold**`, `*italic*`, `- list item`). DO NOT use any raw LaTeX commands. Write only the body text."""
    try:
        raw_output = from_generator_func(prompt)
        return process_llm_output_for_latex(raw_output)
    except Exception as e:
        logger.error(f"Error generating content for section '{section_title}': {e}")
        return f"\\textbf{{Error: Could not generate content for this section.}}"

def generate_user_figure_latex(basename: str, caption: str) -> str:
    escaped_caption = escape_latex_special_chars(caption or "User-provided figure.")
    safe_label = re.sub(r'[^a-zA-Z0-9]', '', basename)[:20]
    return f"""\\begin{{figure}}[htbp] \\centering
    \\includegraphics[width=0.8\\textwidth,keepaspectratio]{{{basename}}}
    \\caption{{{escaped_caption}}} \\label{{fig:{safe_label}}}
\\end{{figure}}"""

def generate_main_content(sections: List[Dict[str, Any]], query: str, output_file: str, from_generator_func, use_rag: bool, user_figure_basename: Optional[str], user_figure_caption: Optional[str]):
    all_content = []
    if user_figure_basename:
        all_content.append(generate_user_figure_latex(user_figure_basename, user_figure_caption))

    for section in sections:
        title = section.get("title")
        if not title: continue
        
        cleaned_title = clean_title_for_latex_command(title)
        all_content.append(f"\\section{{{escape_latex_special_chars(cleaned_title)}}}")
        all_content.append(generate_section_content(cleaned_title, query, from_generator_func))
        time.sleep(2.0)
        for sub_item in section.get("subsections", []):
            sub_title = sub_item.get("title") if isinstance(sub_item, dict) else sub_item
            if not sub_title or not isinstance(sub_title, str): continue
            
            cleaned_sub_title = clean_title_for_latex_command(sub_title)
            all_content.append(f"\\subsection{{{escape_latex_special_chars(cleaned_sub_title)}}}")
            all_content.append(generate_section_content(f"{cleaned_title} - {cleaned_sub_title}", query, from_generator_func))

    with open(output_file, "w", encoding="utf-8") as f: f.write("\n\n".join(all_content))
    logger.info(f"Main content successfully written to {output_file}")