# backend/src/cover.py

import os
import logging
from typing import List, Optional
from latex_utils import escape_latex_special_chars

logger = logging.getLogger()

def generate_cover_page(
    report_title: str,
    authors: List[str],
    date: str,
    mentors: List[str],
    university: str,
    logo_path: Optional[str],
    primary_color: str,
    output_path: str,
    main_tex_output_dir: str
):
    """
    Generates the LaTeX content for the cover page with the corrected layout and escaping.
    """
    logger.info(f"Generating cover page for '{report_title}' -> writing to '{output_path}'")

    escaped_title = escape_latex_special_chars(report_title)
    escaped_university = escape_latex_special_chars(university)
    escaped_date = escape_latex_special_chars(date)
    
    authors_latex = "\\\\ \n".join([f"\\Large {escape_latex_special_chars(author)}" for author in authors])
    mentors_latex = "\\\\ \n".join([f"\\Large {escape_latex_special_chars(mentor)}" for mentor in mentors]) if mentors else ""

    logo_filename = os.path.basename(logo_path) if logo_path and os.path.exists(logo_path) else None
    logo_cmd = f"\\includegraphics[width=0.3\\textwidth,keepaspectratio]{{{logo_filename}}}" if logo_filename else ""

    cover_content = f"""
\\begin{{titlepage}}
    \\centering
    
    % Logo at the top
    {logo_cmd}
    \\vspace{{1.5cm}}
    
    % Report Title
    {{\\Huge\\bfseries\\color{{primarycolor}} {escaped_title} \\par}}
    
    \\vspace{{2.5cm}}
    
    % Authors Block
    {{\\LARGE\\textbf{{Authors:}} \\par}}
    \\vspace{{0.5cm}}
    {authors_latex}
    \\par
    
    % Mentors Block (only if mentors exist)
    {f'''\\vspace{{1.5cm}}
    {{\\LARGE\\textbf{{Mentors:}} \\par}}
    \\vspace{{0.5cm}}
    {mentors_latex}
    \\par''' if mentors_latex else ''}
    
    % This pushes the following content to the bottom of the page
    \\vfill 
    
    % University and Date at the bottom
    {{\\Large {escaped_university} \\par}}
    \\vspace{{0.5cm}}
    {{\\Large {escaped_date} \\par}}

\\end{{titlepage}}
"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(cover_content)
    logger.info(f"Successfully wrote cover.tex to {output_path}")
    return output_path