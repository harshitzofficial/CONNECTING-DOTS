# Outline extraction module (see previous chat for full code)
"""
Outline extraction module for Round 1A
Extracts hierarchical document structure from PDFs
"""

import fitz  # PyMuPDF
import logging
import statistics
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import re

logger = logging.getLogger(__name__)

class OutlineExtractor:
    """Extracts hierarchical outline from PDF documents"""
    
    def __init__(self):
        self.min_title_font_ratio = 1.8
        self.min_heading_font_ratio = 1.0
        self.min_h1_font_ratio = 1.4
        self.min_h2_font_ratio = 1.2
        
    def extract_outline(self, pdf_path: Path) -> Dict:
        """Extract outline from PDF file"""
        try:
            doc = fitz.open(pdf_path)
            
            if len(doc) == 0:
                raise ValueError("PDF has no pages")
            
            # Extract text blocks with formatting
            all_blocks = []
            for page_num in range(len(doc)):
                page = doc[page_num]
                blocks = self._extract_page_blocks(page, page_num + 1)
                all_blocks.extend(blocks)
            
            doc.close()
            
            # Analyze font sizes
            font_sizes = [block['fontsize'] for block in all_blocks if block['fontsize'] > 0]
            if not font_sizes:
                raise ValueError("No text with font size information found")
            
            median_fontsize = statistics.median(font_sizes)
            mean_fontsize = statistics.mean(font_sizes)
            std_fontsize = statistics.stdev(font_sizes) if len(font_sizes) > 1 else 1
            
            # Extract title
            title = self._extract_title(all_blocks, median_fontsize, std_fontsize)
            
            # Extract headings
            outline = self._extract_headings(all_blocks, median_fontsize, std_fontsize)
            
            result = {
                "title": title,
                "outline": outline
            }
            
            logger.info(f"Extracted outline with {len(outline)} headings")
            return result
            
        except Exception as e:
            logger.error(f"Error extracting outline: {str(e)}")
            raise
    
    def _extract_page_blocks(self, page, page_num: int) -> List[Dict]:
        """Extract text blocks from a single page"""
        blocks = []
        
        try:
            # Get text with formatting information
            text_dict = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)
            
            for block in text_dict.get("blocks", []):
                if "lines" not in block:
                    continue
                    
                for line in block["lines"]:
                    line_text = ""
                    fontsize = 0
                    fontname = ""
                    flags = 0
                    bbox = None
                    
                    for span in line.get("spans", []):
                        if span.get("text", "").strip():
                            line_text += span["text"]
                            fontsize = max(fontsize, span.get("size", 0))
                            fontname = span.get("font", "")
                            flags = span.get("flags", 0)
                            
                            if bbox is None:
                                bbox = span["bbox"]
                            else:
                                # Merge bounding boxes
                                bbox = [
                                    min(bbox[0], span["bbox"][0]),
                                    min(bbox[1], span["bbox"][1]),
                                    max(bbox[2], span["bbox"][2]),
                                    max(bbox[3], span["bbox"][3])
                                ]
                    
                    line_text = line_text.strip()
                    if line_text and bbox:
                        blocks.append({
                            "text": line_text,
                            "fontsize": fontsize,
                            "fontname": fontname,
                            "flags": flags,
                            "bbox": bbox,
                            "page": page_num,
                            "is_bold": self._is_bold(fontname, flags),
                            "y_position": bbox[1],
                            "x_position": bbox[0],
                            "width": bbox[2] - bbox[0],
                            "height": bbox[3] - bbox[1]
                        })
        
        except Exception as e:
            logger.warning(f"Error extracting blocks from page {page_num}: {str(e)}")
        
        return blocks
    
    def _is_bold(self, fontname: str, flags: int) -> bool:
        """Check if text is bold based on font name and flags"""
        if "bold" in fontname.lower():
            return True
        # Check flags for bold (bit 4)
        return bool(flags & 2**4)
    
    def _extract_title(self, blocks: List[Dict], median_fontsize: float, std_fontsize: float) -> str:
        """Extract document title from first page"""
        if not blocks:
            return ""
        
        # Look for title on first page
        first_page_blocks = [b for b in blocks if b["page"] == 1]
        if not first_page_blocks:
            return ""
        
        # Find blocks with large font size
        title_candidates = []
        for block in first_page_blocks:
            font_ratio = block["fontsize"] / median_fontsize
            if font_ratio >= self.min_title_font_ratio:
                title_candidates.append(block)
        
        if not title_candidates:
            # Fallback: largest font on first page
            title_candidates = [max(first_page_blocks, key=lambda x: x["fontsize"])]
        
        # Select the topmost candidate
        title_block = min(title_candidates, key=lambda x: x["y_position"])
        return title_block["text"]
    
    def _extract_headings(self, blocks: List[Dict], median_fontsize: float, std_fontsize: float) -> List[Dict]:
        """Extract hierarchical headings from blocks"""
        headings = []
        
        for block in blocks:
            if self._is_heading_candidate(block, median_fontsize, std_fontsize):
                level = self._determine_heading_level(block, median_fontsize)
                
                headings.append({
                    "level": level,
                    "text": block["text"],
                    "page": block["page"]
                })
        
        # Sort by page and position
        headings.sort(key=lambda x: (x["page"], blocks[blocks.index(next(b for b in blocks if b["text"] == x["text"]))]["y_position"]))
        
        return headings
    
    def _is_heading_candidate(self, block: Dict, median_fontsize: float, std_fontsize: float) -> bool:
        """Check if block is a heading candidate"""
        font_ratio = block["fontsize"] / median_fontsize
        
        # Check various criteria
        criteria = [
            font_ratio >= self.min_heading_font_ratio,
            block["is_bold"],
            self._is_centered(block),
            self._is_capitalized(block["text"]),
            self._is_numbered_heading(block["text"])
        ]
        
        # Need at least one strong criterion
        return any(criteria)
    
    def _determine_heading_level(self, block: Dict, median_fontsize: float) -> str:
        """Determine heading level based on font size"""
        font_ratio = block["fontsize"] / median_fontsize
        
        if font_ratio >= self.min_h1_font_ratio:
            return "H1"
        elif font_ratio >= self.min_h2_font_ratio:
            return "H2"
        else:
            return "H3"
    
    def _is_centered(self, block: Dict) -> bool:
        """Check if text block is centered"""
        # Simple heuristic: check if text starts after significant margin
        return block["x_position"] > 100  # Adjust threshold as needed
    
    def _is_capitalized(self, text: str) -> bool:
        """Check if text is mostly capitalized"""
        if len(text) < 3:
            return False
        return sum(c.isupper() for c in text) / len(text) > 0.7
    
    def _is_numbered_heading(self, text: str) -> bool:
        """Check if text looks like a numbered heading"""
        patterns = [
            r'^\d+\.',           # "1. Introduction"
            r'^\d+\s+[A-Z]',     # "1 Introduction"
            r'^[A-Z]\.',         # "A. Overview"
            r'^\d+\.\d+',        # "1.1 Subsection"
        ]
        
        return any(re.match(pattern, text) for pattern in patterns)
