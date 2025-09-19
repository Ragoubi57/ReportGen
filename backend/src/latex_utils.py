# backend/src/latex_utils.py

import logging
import re

logger = logging.getLogger(__name__)

ESCAPE_MAP = {
    '\\': r'\textbackslash{}',
    '&': r'\&',
    '%': r'\%',
    '$': r'\$',
    '#': r'\#',
    '_': r'\_',
    '{': r'\{',
    '}': r'\}',
    '~': r'\textasciitilde{}',
    '^': r'\textasciicircum{}',
    '<': r'\textless{}',
    '>': r'\textgreater{}',
}
ESCAPE_REGEX = re.compile(r'(?<!\\)([%s])' % re.escape(''.join(ESCAPE_MAP.keys())))

def escape_latex_special_chars(text: str) -> str:
    """
    Escapes special LaTeX characters in a given string using a pre-compiled regex.
    """
    if not isinstance(text, str) or not text:
        return ""
    return ESCAPE_REGEX.sub(lambda mo: ESCAPE_MAP[mo.group(0)], text)

def process_llm_output_for_latex(raw_text: str) -> str:
    """
    A robust, regex-based master processing function to convert LLM markdown
    output to safe LaTeX.
    
    Handles:
    - Code blocks (```...```) -> verbatim
    - Headers (#, ##, ###)
    - Lists (* or -)
    - Bold (**...**) and Italic (*...*)
    - Blockquotes (> ...)
    - Escaping of all special characters in plain text.
    """
    if not isinstance(raw_text, str) or not raw_text:
        return ""

    def replace_code_block(match):
        code = match.group(1).strip()
        return f"\\begin{{verbatim}}\n{code}\n\\end{{verbatim}}"
    
    processed_text = re.sub(r'```(?:\w+)?\n(.*?)\n```', replace_code_block, raw_text, flags=re.DOTALL)

    lines = processed_text.split('\n')
    output_lines = []
    in_list = False

    for line in lines:
        if r'\begin{verbatim}' in line or r'\end{verbatim}' in line:
            output_lines.append(line)
            continue
            
        stripped_line = line.strip()

        if in_list and not (stripped_line.startswith(("- ")) or stripped_line.startswith(("* "))):
            output_lines.append(r'\end{itemize}')
            in_list = False

        if stripped_line.startswith('# '):
            title = escape_latex_special_chars(stripped_line[2:].strip())
            output_lines.append(f"\\section*{{{title}}}")
        elif stripped_line.startswith('## '):
            title = escape_latex_special_chars(stripped_line[3:].strip())
            output_lines.append(f"\\subsection*{{{title}}}")
        elif stripped_line.startswith('### '):
            title = escape_latex_special_chars(stripped_line[4:].strip())
            output_lines.append(f"\\subsubsection*{{{title}}}")
        elif stripped_line.startswith('> '):
            quote = escape_latex_special_chars(stripped_line[2:].strip())
            output_lines.append(f"\\begin{{quote}}{quote}\\end{{quote}}")
        elif stripped_line.startswith(("- ")) or stripped_line.startswith(("* ")):
            if not in_list:
                output_lines.append(r'\begin{itemize}')
                in_list = True
            item_content = escape_latex_special_chars(stripped_line[2:].strip())
            output_lines.append(f'  \\item {item_content}')
        else:
            output_lines.append(escape_latex_special_chars(line))

    if in_list:
        output_lines.append(r'\end{itemize}')

    final_text = '\n'.join(output_lines)
    
    final_text = re.sub(r'\*\*(.*?)\*\*', r'\\textbf{\1}', final_text)
    final_text = re.sub(r'\*(.*?)\*', r'\\textit{\1}', final_text)
    final_text = re.sub(r'`(.*?)`', r'\\texttt{\1}', final_text)

    return final_text

def clean_title_for_latex_command(title: str) -> str:
    """Strips outer braces and leading/trailing whitespace from titles."""
    if not title: return "Untitled"
    cleaned = title.strip()
    while len(cleaned) > 1 and cleaned.startswith('{') and cleaned.endswith('}'):
        cleaned = cleaned[1:-1].strip()
    return cleaned if cleaned else "Untitled"