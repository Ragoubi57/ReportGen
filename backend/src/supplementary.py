# backend/src/supplementary.py

import logging
from typing import List, Dict, Optional

from latex_utils import process_llm_output_for_latex

logger = logging.getLogger(__name__)

def generate_bibliography(query: str, sections: List[Dict], output_file: str, from_generator_func):
    """Generates the bibliography section with a robust prompt for \bibitem entries."""
    
    
    prompt = f"""You are an academic assistant. Generate a list of 5-7 complete bibliography entries for a report on "{query}".

CRITICAL FORMATTING RULES:
1.  Every entry MUST start with a LaTeX `\\bibitem{{key}}` command on a new line.
2.  The `key` inside the braces must be simple and alphanumeric (e.g., `{{Smith2023}}`).
3.  The content of the reference should follow the key.
4.  Use simple markdown for book or journal titles (e.g., `*The Journal of AI*`).

EXAMPLE:
\\bibitem{{Vaswani2017}}
Vaswani, A., Shazeer, N., Parmar, N., Uszkoreit, J., Jones, L., Gomez, A. N., ... & Polosukhin, I. (2017). *Attention is all you need*. Advances in neural information processing systems, 30.

\\bibitem{{LeCun2015}}
LeCun, Y., Bengio, Y., & Hinton, G. (2015). *Deep learning*. Nature, 521(7553), 436-444.
"""
    try:
        raw_bib_list = from_generator_func(prompt)
        processed_bib_content = process_llm_output_for_latex(raw_bib_list)

        final_content = f"""\\addcontentsline{{toc}}{{section}}{{References}}
\\begin{{thebibliography}}{{99}}
{processed_bib_content}
\\end{{thebibliography}}"""
        
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)
        logger.info(f"Bibliography written to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error in generate_bibliography: {e}")
        # Provide a safe fallback
        with open(output_file, "w", encoding="utf-8") as f:
            f.write("\\addcontentsline{toc}{section}{References}\\begin{thebibliography}{99}\\item Error generating bibliography.\\end{thebibliography}")
        return output_file

def generate_appendices(query: str, sections: List[Dict], output_file: str, from_generator_func) -> Optional[str]:
    """Generates the appendices section with a softened decision prompt."""
    
    decision_prompt = f"""Based on the report topic "{query}", would an appendix section for extra data, source code, or a glossary be beneficial? Please respond with a full sentence, starting with YES or NO."""
    try:
        decision = from_generator_func(decision_prompt)
        if "YES" not in decision.upper():
            logger.info("Appendices not deemed necessary by LLM.")
            return None
    except Exception as e:
        logger.warning(f"Appendix decision-making failed: {e}. Skipping appendices.")
        return None

    logger.info("Generating appendices content...")
    content_prompt = f"""Generate content for an appendix section of a report on "{query}".
FORMAT: Use simple markdown. Start each new appendix with a markdown header (`## Appendix A: Title`). Then provide the content for that appendix.
Example:
## Appendix A: Raw Data Tables
... content for appendix A ...

## Appendix B: Glossary of Terms
... content for appendix B ..."""
    try:
        raw_content = from_generator_func(content_prompt)
        if not raw_content.strip():
            logger.info("LLM returned empty content for appendix.")
            return None
            
        processed_content = process_llm_output_for_latex(raw_content)

        final_content = f"""\\appendix
\\clearpage
\\addcontentsline{{toc}}{{section}}{{Appendices}}
{processed_content}"""

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(final_content)
        logger.info(f"Appendices written to {output_file}")
        return output_file
    except Exception as e:
        logger.error(f"Error in generate_appendices: {e}")
        return None