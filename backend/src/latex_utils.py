# backend/src/latex_utils.py

import logging
import re

logger = logging.getLogger(__name__)

def escape_latex_special_chars(text: str) -> str:
    """Escapes only the special LaTeX characters from a given string of plain text."""
    if not text:
        return ""
    # Order is important: backslash must be first.
    escape_map = {
        '\\': r'\textbackslash{}',
        '&': r'\&', '%': r'\%', '$': r'\$', '#': r'\#', '_': r'\_',
        '{': r'\{', '}': r'\}', '~': r'\textasciitilde{}', '^': r'\textasciicircum{}',
    }
    regex = re.compile('([%s])' % re.escape(''.join(escape_map.keys())))
    return regex.sub(lambda mo: escape_map[mo.string[mo.start():mo.end()]], text)

def _process_inline_markdown_and_escape(text: str) -> str:
    """Processes bold/italic markdown first, then escapes the rest of the line."""
    # Temporarily replace markdown with unique placeholders
    bold_items = re.findall(r'\*\*(.*?)\*\*', text)
    italic_items = re.findall(r'\*(.*?)\*', text)
    
    for i, item in enumerate(bold_items):
        text = text.replace(f'**{item}**', f'__BOLD_PLACEHOLDER_{i}__', 1)
    for i, item in enumerate(italic_items):
        text = text.replace(f'*{item}*', f'__ITALIC_PLACEHOLDER_{i}__', 1)

    # Now that markdown is protected, escape everything else
    escaped_text = escape_latex_special_chars(text)

    # Restore the LaTeX commands, escaping the content *inside* them
    for i, item in enumerate(bold_items):
        escaped_item = escape_latex_special_chars(item)
        escaped_text = escaped_text.replace(f'__BOLD_PLACEHOLDER_{i}__', f'\\textbf{{{escaped_item}}}', 1)
    for i, item in enumerate(italic_items):
        escaped_item = escape_latex_special_chars(item)
        escaped_text = escaped_text.replace(f'__ITALIC_PLACEHOLDER_{i}__', f'\\textit{{{escaped_item}}}', 1)

    return escaped_text

def process_llm_output_for_latex(raw_text: str) -> str:
    """
    The master processing function. It uses a line-by-line state machine to correctly
    convert markdown to LaTeX and escape all content safely.
    """
    if not raw_text:
        return ""
    
    lines = raw_text.split('\n')
    output_lines = []
    in_list = False

    for line in lines:
        stripped_line = line.lstrip()

        # Determine line type and process accordingly, avoiding reprocessing.

        # 1. Handle Headers
        if stripped_line.startswith('### '):
            if in_list: output_lines.append(r'\end{itemize}'); in_list = False
            title = _process_inline_markdown_and_escape(stripped_line[4:].strip())
            output_lines.append(f"\\subsubsection*{{{title}}}")
            continue
        elif stripped_line.startswith('## '):
            if in_list: output_lines.append(r'\end{itemize}'); in_list = False
            title = _process_inline_markdown_and_escape(stripped_line[3:].strip())
            output_lines.append(f"\\subsection*{{{title}}}")
            continue
        elif stripped_line.startswith('# '):
            if in_list: output_lines.append(r'\end{itemize}'); in_list = False
            title = _process_inline_markdown_and_escape(stripped_line[2:].strip())
            output_lines.append(f"\\section*{{{title}}}")
            continue

        # 2. Handle List Items
        if stripped_line.startswith(("- ", "* ")):
            if not in_list:
                output_lines.append(r'\begin{itemize}')
                in_list = True
            item_content = stripped_line[2:]
            processed_item = _process_inline_markdown_and_escape(item_content)
            output_lines.append(f'  \\item {processed_item}')
            continue

        # 3. Handle Plain Paragraph Lines (or empty lines)
        if in_list:
            output_lines.append(r'\end{itemize}')
            in_list = False
        
        # Process any markdown in the paragraph and escape the rest
        processed_line = _process_inline_markdown_and_escape(line)
        output_lines.append(processed_line)

    # Close any list that might be open at the end of the text
    if in_list:
        output_lines.append(r'\end{itemize}')
        
    return '\n'.join(output_lines)

def clean_title_for_latex_command(title: str) -> str:
    """Strips outer braces from titles."""
    if not title: return "Untitled"
    cleaned = title.strip()
    while len(cleaned) > 1 and cleaned.startswith('{') and cleaned.endswith('}'):
        cleaned = cleaned[1:-1].strip()
    return cleaned if cleaned else "Untitled"