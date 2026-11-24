

import fitz
import re
import unicodedata
from typing import Optional, List, Tuple
from dataclasses import dataclass


@dataclass
class ProcessingStats:
    """Track preprocessing statistics."""
    original_length: int = 0
    cleaned_length: int = 0
    spaced_fixes: int = 0
    hyphen_fixes: int = 0
    noise_removed: int = 0


class IndustryGradePDFPreprocessor:
    """
    Production-ready PDF text preprocessing.
    Handles severe OCR issues and messy academic PDFs.
    """
    
    def __init__(self, aggressive_mode: bool = True):
        self.aggressive_mode = aggressive_mode
        self.stats = ProcessingStats()
        
    def normalize_unicode(self, text: str) -> str:
        """Normalize unicode characters."""
        # Normalize to NFKC form (compatibility decomposition + canonical composition)
        text = unicodedata.normalize('NFKC', text)
        
        # Replace common unicode variants
        replacements = {
            '\u2019': "'",   # Right single quote
            '\u2018': "'",   # Left single quote
            '\u201c': '"',   # Left double quote
            '\u201d': '"',   # Right double quote
            '\u2013': '-',   # En dash
            '\u2014': '-',   # Em dash
            '\u00a0': ' ',   # Non-breaking space
            '\u2002': ' ',   # En space
            '\u2003': ' ',   # Em space
            '\u2009': ' ',   # Thin space
            '\u200b': '',    # Zero-width space
            '\ufeff': '',    # BOM
            '…': '...',      # Ellipsis
            '−': '-',        # Minus sign
            '×': 'x',        # Multiplication sign
            '·': '.',        # Middle dot
        }
        
        for old, new in replacements.items():
            text = text.replace(old, new)
        
        return text
    
    def detect_spaced_text(self, text: str) -> bool:
        """
        Detect if text has severe spacing issues.
        Returns True if text appears to have char-by-char spacing.
        """
        # Count single chars followed by spaces
        spaced_pattern = re.findall(r'[a-zA-Z] [a-zA-Z] [a-zA-Z]', text)
        total_alpha = len(re.findall(r'[a-zA-Z]', text))
        
        if total_alpha == 0:
            return False
        
        # If more than 20% of text matches spaced pattern, it's spaced
        spaced_ratio = len(spaced_pattern) * 3 / total_alpha
        return spaced_ratio > 0.15
    
    def fix_spaced_text_aggressive(self, text: str) -> str:
        """
        Aggressively fix char-by-char spaced text.
        Handles: 'R A G' -> 'RAG', 'r e t r i e v a l' -> 'retrieval'
        """
        original_len = len(text)
        
        # Split into lines for line-by-line processing
        lines = text.split('\n')
        fixed_lines = []
        
        for line in lines:
            if self.detect_spaced_text(line):
                # This line has spacing issues - fix aggressively
                fixed_line = self._collapse_spaced_line(line)
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        
        result = '\n'.join(fixed_lines)
        self.stats.spaced_fixes += original_len - len(result)
        return result
    
    def _collapse_spaced_line(self, line: str) -> str:
        """
        Collapse a line with spaced characters.
        'R A G   s y s t e m' -> 'RAG system'
        """
        # Method 1: Pattern-based collapse for sequences
        # Match: letter space letter space letter... (at least 2)
        
        def collapse_match(m):
            spaced = m.group(0)
            # Remove single spaces between single chars
            collapsed = ''
            i = 0
            while i < len(spaced):
                if spaced[i] != ' ':
                    collapsed += spaced[i]
                elif i + 1 < len(spaced) and spaced[i + 1] != ' ':
                    # Check if this is char-space-char pattern
                    # Keep space only if it's a word boundary (multiple spaces)
                    if i > 0 and i + 1 < len(spaced):
                        # Single space between letters - remove
                        pass
                    else:
                        collapsed += spaced[i]
                else:
                    collapsed += spaced[i]
                i += 1
            return collapsed
        
        # Pattern: sequences of "letter space" repeated
        # Matches things like "R A G" or "m o d e l"
        pattern = r'(?:[A-Za-z] ){2,}[A-Za-z]'
        result = re.sub(pattern, lambda m: m.group(0).replace(' ', ''), line)
        
        # Also handle mixed: "R A G systems" where only first word is spaced
        # Look for caps sequences specifically
        pattern2 = r'(?:[A-Z] ){1,}[A-Z](?= |$)'
        result = re.sub(pattern2, lambda m: m.group(0).replace(' ', ''), result)
        
        # Method 2: Statistical approach for remaining issues
        # If line still has high single-char-space ratio, collapse all
        if self.detect_spaced_text(result):
            # Nuclear option: remove all single spaces between letters
            result = re.sub(r'(?<=[a-zA-Z]) (?=[a-zA-Z])', '', result)
        
        # Clean up multiple spaces
        result = re.sub(r'  +', ' ', result)
        
        return result.strip()
    
    def fix_broken_hyphens(self, text: str) -> str:
        """Fix words broken across lines with hyphens."""
        original_len = len(text)
        
        # Pattern 1: hyphen-newline-word continuation
        # "infor-\nmation" -> "information"
        text = re.sub(r'(\w)-\s*\n\s*(\w)', r'\1\2', text)
        
        # Pattern 2: hyphen with spaces in middle of word
        # "infor- mation" -> "information"  
        text = re.sub(r'(\w)-\s+([a-z])', r'\1\2', text)
        
        # Pattern 3: Soft hyphen
        text = text.replace('\u00ad', '')
        
        self.stats.hyphen_fixes += original_len - len(text)
        return text
    
    def remove_page_artifacts(self, text: str) -> str:
        """Remove page numbers, headers, footers."""
        # Page numbers (standalone or with decoration)
        text = re.sub(r'^\s*[-–—]?\s*\d{1,4}\s*[-–—]?\s*$', '', text, flags=re.MULTILINE)
        text = re.sub(r'^\s*Page\s+\d+\s*(?:of\s+\d+)?\s*$', '', text, flags=re.MULTILINE | re.IGNORECASE)
        
        # Section navigation headers
        text = re.sub(
            r'^.*?(?:Sec(?:tion)?\.?\s*\d+\s*[:|]\s*\w+\s*\|?\s*)+.*$',
            '',
            text,
            flags=re.MULTILINE | re.IGNORECASE
        )
        
        return text
    
    def remove_academic_noise(self, text: str) -> str:
        """Remove academic paper noise."""
        patterns = [
            # Emails
            (r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ''),
            
            # arXiv IDs
            (r'arXiv:\s*\d+\.\d+(?:v\d+)?', ''),
            
            # DOIs
            (r'(?:doi:|DOI:?|https?://doi\.org/)\s*[\d./\w-]+', ''),
            
            # URLs  
            (r'https?://\S+', ''),
            (r'www\.\S+', ''),
            
            # Copyright
            (r'©\s*\d{4}[^\n]*', ''),
            (r'Copyright\s*©?[^\n]*', ''),
            
            # Conference headers
            (r'Proceedings of[^\n]{0,100}', ''),
            (r'(?:Published|Accepted|Submitted)[^\n]{0,80}\d{4}[^\n]*', ''),
            
            # Footnote markers on their own
            (r'^[\*†‡§¶‖]+\s*$', ''),
            
            # "Equal contribution" type footnotes
            (r'[\*†‡§]\s*(?:Equal|Corresponding|Work done)[^\n]*', ''),
        ]
        
        for pattern, replacement in patterns:
            text = re.sub(pattern, replacement, text, flags=re.IGNORECASE | re.MULTILINE)
        
        return text
    
    def remove_author_blocks(self, text: str) -> str:
        """Remove author name and affiliation blocks."""
        # Author lines with superscripts: "John Doe1,2, Jane Smith3"
        text = re.sub(
            r'^[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s*[,\d∗†‡§]+\s*)+(?:,\s*[A-Z][a-z]+(?:\s+[A-Z][a-z]+)+(?:\s*[,\d∗†‡§]+\s*)+)*\s*$',
            '',
            text,
            flags=re.MULTILINE
        )
        
        # Affiliation lines
        text = re.sub(
            r'^(?:\d+\s*)?(?:Department|School|Institute|University|Lab(?:oratory)?|'
            r'Research|Faculty|College|Center|Centre)[^\n]{0,150}$',
            '',
            text,
            flags=re.IGNORECASE | re.MULTILINE
        )
        
        return text
    
    def remove_references_section(self, text: str) -> str:
        """Remove references/bibliography section."""
        # Find "References" or "Bibliography" and remove everything after
        patterns = [
            r'\n\s*References\s*\n.*$',
            r'\n\s*Bibliography\s*\n.*$',
            r'\n\s*Works Cited\s*\n.*$',
        ]
        
        for pattern in patterns:
            text = re.sub(pattern, '\n', text, flags=re.DOTALL | re.IGNORECASE)
        
        return text
    
    def remove_figure_table_refs(self, text: str) -> str:
        """Remove figure/table captions and references."""
        # Full captions
        text = re.sub(
            r'(?:Figure|Fig\.|Table|Tab\.)\s*\d+[.:][^\n]{0,300}',
            '',
            text,
            flags=re.IGNORECASE
        )
        
        # In-text references like "(see Figure 3)"
        text = re.sub(
            r'\(?\s*(?:see\s+)?(?:Figure|Fig\.|Table|Tab\.)\s*\d+[a-z]?\s*\)?',
            '',
            text,
            flags=re.IGNORECASE
        )
        
        return text
    
    def clean_mathematical_notation(self, text: str) -> str:
        """Clean up mathematical notation."""
        # LaTeX inline math
        text = re.sub(r'\$[^$]+\$', ' [MATH] ', text)
        
        # LaTeX display math
        text = re.sub(r'\\\[[^\]]+\\\]', ' [MATH] ', text, flags=re.DOTALL)
        text = re.sub(r'\\begin\{equation\}.*?\\end\{equation\}', ' [MATH] ', text, flags=re.DOTALL)
        
        # Remove [MATH] placeholders (optional - can keep for context)
        text = re.sub(r'\s*\[MATH\]\s*', ' ', text)
        
        # Common math symbols that break text flow
        text = re.sub(r'[∑∏∫∂∇αβγδεζηθικλμνξπρστυφχψωΓΔΘΛΞΠΣΦΨΩ]+', ' ', text)
        
        return text
    
    def normalize_whitespace(self, text: str) -> str:
        """Final whitespace normalization."""
        # Replace tabs with spaces
        text = text.replace('\t', ' ')
        
        # Collapse multiple spaces
        text = re.sub(r'[ ]+', ' ', text)
        
        # Collapse multiple newlines (keep max 2)
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        # Remove leading/trailing whitespace from lines
        lines = [line.strip() for line in text.split('\n')]
        text = '\n'.join(lines)
        
        # Remove empty lines at start/end
        text = text.strip()
        
        return text
    
    def remove_short_lines(self, text: str, min_length: int = 10) -> str:
        """Remove very short lines (likely noise)."""
        lines = text.split('\n')
        filtered = []
        
        for line in lines:
            stripped = line.strip()
            # Keep empty lines (paragraph breaks) and lines with enough content
            if stripped == '' or len(stripped) >= min_length:
                filtered.append(line)
            # Also keep lines that are part of lists
            elif re.match(r'^[\d•\-\*]\s*\w', stripped):
                filtered.append(line)
        
        return '\n'.join(filtered)
    
    def extract_text_from_pdf(self, pdf_path: str) -> str:
        """Extract raw text from PDF."""
        doc = fitz.open(pdf_path)
        full_text = ""
        
        for page_num, page in enumerate(doc):
            # Try different extraction methods
            text = page.get_text("text")
            
            # If text is mostly spaced, try blocks method
            if self.detect_spaced_text(text):
                # Try with blocks - sometimes gives cleaner output
                blocks_text = ""
                blocks = page.get_text("blocks")
                for block in blocks:
                    if block[6] == 0:  # Text block
                        blocks_text += block[4] + "\n"
                
                # Use whichever is less spaced
                if not self.detect_spaced_text(blocks_text):
                    text = blocks_text
            
            full_text += text + "\n"
        
        doc.close()
        return full_text
    
    def process(self, pdf_path: str, 
                remove_refs: bool = True,
                remove_math: bool = True,
                remove_figures: bool = True,
                remove_authors: bool = True) -> str:
        """
        Main processing pipeline.
        
        Args:
            pdf_path: Path to PDF file
            remove_refs: Remove references section
            remove_math: Clean mathematical notation
            remove_figures: Remove figure/table references
            remove_authors: Remove author blocks
            
        Returns:
            Clean, preprocessed text ready for chunking
        """
        self.stats = ProcessingStats()
        
        # Step 1: Extract raw text
        text = self.extract_text_from_pdf(pdf_path)
        self.stats.original_length = len(text)
        
        # Step 2: Unicode normalization
        text = self.normalize_unicode(text)
        
        # Step 3: Fix OCR spacing issues (CRITICAL)
        text = self.fix_spaced_text_aggressive(text)
        
        # Step 4: Fix broken hyphens
        text = self.fix_broken_hyphens(text)
        
        # Step 5: Remove page artifacts
        text = self.remove_page_artifacts(text)
        
        # Step 6: Remove academic noise
        text = self.remove_academic_noise(text)
        
        # Step 7: Optional removals
        if remove_authors:
            text = self.remove_author_blocks(text)
        
        if remove_refs:
            text = self.remove_references_section(text)
        
        if remove_math:
            text = self.clean_mathematical_notation(text)
        
        if remove_figures:
            text = self.remove_figure_table_refs(text)
        
        # Step 8: Remove short noise lines
        text = self.remove_short_lines(text)
        
        # Step 9: Final whitespace cleanup
        text = self.normalize_whitespace(text)
        
        # Step 10: Final spaced text check (safety net)
        if self.detect_spaced_text(text):
            # Nuclear option if still spaced
            text = re.sub(r'(?<=[a-zA-Z]) (?=[a-zA-Z])', '', text)
            text = self.normalize_whitespace(text)
        
        self.stats.cleaned_length = len(text)
        return text
    
    def get_stats(self) -> dict:
        """Get processing statistics."""
        return {
            'original_length': self.stats.original_length,
            'cleaned_length': self.stats.cleaned_length,
            'reduction_percent': round(
                (1 - self.stats.cleaned_length / max(self.stats.original_length, 1)) * 100, 2
            ),
            'spaced_fixes': self.stats.spaced_fixes,
            'hyphen_fixes': self.stats.hyphen_fixes,
        }


# Singleton instance
preprocessor = IndustryGradePDFPreprocessor(aggressive_mode=True)


def extract_pdf_text(pdf_path: str) -> str:
    """Main extraction function for backward compatibility."""
    return preprocessor.process(pdf_path)


# PDF files to process
files = [
    'AttentionIsAllYouNeed.pdf', 
    'Build a Large Language Model (From Scratch).pdf', 
    'HybridRAG Integrating Knowledge Graphs and Vector Retrieval.pdf', 
    'Modular RAG Yunfan Gao, Yun Xiong, Meng Wang, Haofen Wang.pdf', 
    'RAG_Reasearch Paper.pdf', 
    'VL-JEPA Research Paper.pdf'
]


def get_all_text() -> str:
    """Extract and preprocess text from all PDFs."""
    all_text = ""
    for file in files:
        print(f"Processing: {file}")
        text = extract_pdf_text(f"./data/{file}")
        stats = preprocessor.get_stats()
        print(f"  Original: {stats['original_length']:,} chars -> Cleaned: {stats['cleaned_length']:,} chars ({stats['reduction_percent']}% reduction)")
        all_text += '\n\n' + text
    return all_text.strip()


def test_spaced_text_fix():
    """Test the spaced text fixer."""
    test_cases = [
        "V L - J E P A",
        "r e t r i e v a l",
        "R A G   s y s t e m s",
        "m o d u l a r i t y   o f   R A G",
        "The RAG system works well",  # Should not change
        "p r o v i d i n g   a   f r e s h   p e r s p e c t i v e",
    ]
    
    print("=== Spaced Text Fix Tests ===")
    for test in test_cases:
        fixed = preprocessor._collapse_spaced_line(test)
        print(f"  '{test[:50]}...' -> '{fixed}'")


if __name__ == "__main__":
    test_spaced_text_fix()
    
    print("\n=== Processing Sample PDF ===")
    if files:
        sample_text = extract_pdf_text(f"./data/{files[3]}")  # Modular RAG paper
        print(f"\nFirst 2000 chars of cleaned text:\n{sample_text[:2000]}")
        print(f"\nStats: {preprocessor.get_stats()}")