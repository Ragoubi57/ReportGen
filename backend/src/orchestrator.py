import os
import logging
import subprocess
import re
import shutil
import time
from typing import List, Optional, Dict, Any

from latex_utils import escape_latex_special_chars
from cover import generate_cover_page
from toc import generate_toc_from_query
from main_content import generate_main_content
from supplementary import generate_bibliography, generate_appendices
from generator import call_gemini
import logging

logger = logging.getLogger()

class ReportGenerator:
    def __init__(self, output_dir: str = "build", temp_dir_name: str = "api_orchestrator_temp", use_rag: bool = True):
        self.output_dir = os.path.abspath(output_dir)
        self.temp_dir = os.path.join(self.output_dir, temp_dir_name)
        self.use_rag = use_rag
        
        os.makedirs(self.temp_dir, exist_ok=True)

        self.cover_path = os.path.join(self.temp_dir, "cover.tex")
        self.main_content_path = os.path.join(self.temp_dir, "main_content.tex")
        self.bibliography_path = os.path.join(self.temp_dir, "bibliography.tex")
        self.appendices_path = os.path.join(self.temp_dir, "appendices.tex")
        logger.info(f"ReportGenerator initialized. RAG enabled: {self.use_rag}. Temp Dir: {self.temp_dir}")

    def _get_safe_filename(self, title: str) -> str:
        safe = re.sub(r'[^\w\s-]', '', title).strip()
        return re.sub(r'[-\s]+', '-', safe).lower() or "report"

    def generate_report(
        self, query: str, report_title: str, authors: List[str], date: str,
        mentors: Optional[List[str]], university: Optional[str], logo_path: Optional[str],
        primary_color: str, user_figure_path: Optional[str], user_figure_caption: Optional[str]
    ) -> str:
        safe_filename = self._get_safe_filename(report_title)
        final_tex_path = os.path.join(self.output_dir, f"{safe_filename}_report.tex")
        final_pdf_path = os.path.join(self.output_dir, f"{safe_filename}_report.pdf")

        # Copy assets to the compilation directory
        local_logo_path = None
        if logo_path and os.path.exists(logo_path):
            basename = os.path.basename(logo_path)
            local_logo_path = os.path.join(self.temp_dir, basename)
            shutil.copy2(logo_path, local_logo_path)

        user_figure_basename = None
        if user_figure_path and os.path.exists(user_figure_path):
            basename = os.path.basename(user_figure_path)
            shutil.copy2(user_figure_path, os.path.join(self.temp_dir, basename))
            user_figure_basename = basename

        logger.info("Step 1: Generating TOC...")
        sections = generate_toc_from_query(query, call_gemini)
        
        logger.info("Step 2: Generating Cover...")
        generate_cover_page(
            report_title=report_title, authors=authors, date=date, mentors=mentors or [],
            university=university, logo_path=local_logo_path,
            primary_color=primary_color,
            output_path=self.cover_path, main_tex_output_dir=self.output_dir
        )

        logger.info("Step 3: Generating Main Content...")
        generate_main_content(
            sections=sections, query=query, output_file=self.main_content_path,
            from_generator_func=call_gemini, use_rag=self.use_rag,
            user_figure_basename=user_figure_basename, user_figure_caption=user_figure_caption
        )
        
        logger.info("Step 4: Generating Bibliography...")
        generate_bibliography(query, sections, self.bibliography_path, call_gemini)
        
        logger.info("Step 5: Generating Appendices...")
        has_appendices = generate_appendices(query, sections, self.appendices_path, call_gemini) is not None

        logger.info("Step 6: Combining .tex files...")
        self._combine_latex_files(final_tex_path, report_title, has_appendices, primary_color)
        
        logger.info("Step 7: Compiling PDF...")
        if self._compile_pdf(final_tex_path):
            return final_pdf_path
        return final_tex_path

    def _combine_latex_files(self, final_path: str, title: str, has_appendices: bool, color: str):
        temp_dir_basename = os.path.basename(self.temp_dir).replace('\\', '/')
        metadata_title = escape_latex_special_chars(title)
        
        content = f"""\\documentclass[11pt,a4paper]{{article}}
\\usepackage[utf8]{{inputenc}} \\usepackage[T1]{{fontenc}} \\usepackage{{lmodern}} \\usepackage{{textcomp}}
\\usepackage{{graphicx}} \\usepackage{{amsmath,amssymb}} \\usepackage{{xcolor}} \\usepackage{{geometry}}
\\usepackage{{hyperref}} \\usepackage{{sectsty}} \\usepackage{{url}} \\usepackage{{booktabs}} \\usepackage{{float}}
\\geometry{{margin=1in}} \\graphicspath{{ {{{temp_dir_basename}/}} }} \\urlstyle{{same}}
\\definecolor{{primarycolor}}{{RGB}}{{{color}}}
\\hypersetup{{colorlinks=true, linkcolor=primarycolor, urlcolor=primarycolor, pdftitle={{{metadata_title}}}}}
\\sectionfont{{\\color{{primarycolor}}\\Large\\bfseries}} \\subsectionfont{{\\color{{primarycolor}}\\large\\bfseries}}
\\begin{{document}}
\\input{{{temp_dir_basename}/{os.path.basename(self.cover_path)}}}
\\tableofcontents \\newpage
\\input{{{temp_dir_basename}/{os.path.basename(self.main_content_path)}}} \\clearpage
\\input{{{temp_dir_basename}/{os.path.basename(self.bibliography_path)}}}
{'\\clearpage \\input{{{_t}/{_a}}}'.format(_t=temp_dir_basename, _a=os.path.basename(self.appendices_path)) if has_appendices else ''}
\\end{{document}}"""
        with open(final_path, "w", encoding="utf-8") as f: f.write(content)
        logger.info(f"Combined LaTeX into '{final_path}'")

    def _compile_pdf(self, tex_path: str) -> bool:
        compile_dir, tex_filename = os.path.split(tex_path)
        original_cwd = os.getcwd()
        try:
            os.chdir(compile_dir)
            cmd = ["pdflatex", "-interaction=nonstopmode", "-halt-on-error", tex_filename]
            for i in range(3):
                logger.info(f"Running pdflatex pass {i + 1}/3...")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=180, encoding='utf-8', errors='ignore')
                if result.returncode != 0:
                    log_path = tex_path.replace('.tex', '.log')
                    if os.path.exists(log_path):
                        with open(log_path, 'r', encoding='utf-8', errors='ignore') as log_file:
                            logger.error(f"pdflatex failed on pass {i+1}. Log tail:\\n{log_file.read()[-2000:]}")
                    break
            pdf_path = tex_path.replace('.tex', '.pdf')
            if os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 1024:
                logger.info("PDF compilation successful.")
                return True
            else:
                logger.error("PDF compilation failed or produced an empty file.")
                return False
        except Exception as e:
            logger.error(f"An exception occurred during PDF compilation: {e}")
            return False
        finally:
            os.chdir(original_cwd)