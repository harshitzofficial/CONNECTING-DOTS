#!/usr/bin/env python3
# Main entry point with orchestration logic (see previous chat for full code)
#!/usr/bin/env python3
"""
Intelligent Document Insight Engine
Main entry point for Adobe "Connecting the Dots" Hackathon Solution
"""

import os
import json
import logging
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional
import argparse

from outline import OutlineExtractor
from ranker import PersonaRanker
from utils import setup_logging, validate_pdf, get_file_hash

# Configure logging
setup_logging()
logger = logging.getLogger(__name__)

class DocumentProcessor:
    """Main document processing orchestrator"""
    
    def __init__(self, input_dir: str = "/app/input", output_dir: str = "/app/output"):
        self.input_dir = Path(input_dir)
        self.output_dir = Path(output_dir)
        self.outline_extractor = OutlineExtractor()
        self.persona_ranker = PersonaRanker()
        
        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
    def process_round_1a(self, pdf_path: Path) -> Dict:
        """Process single PDF for Round 1A (outline extraction)"""
        try:
            logger.info(f"Processing Round 1A for {pdf_path.name}")
            start_time = time.time()
            
            # Validate PDF
            if not validate_pdf(pdf_path):
                raise ValueError(f"Invalid PDF file: {pdf_path}")
            
            # Extract outline
            result = self.outline_extractor.extract_outline(pdf_path)
            
            # Add metadata
            result["metadata"] = {
                "filename": pdf_path.name,
                "file_hash": get_file_hash(pdf_path),
                "processing_time": time.time() - start_time,
                "round": "1A"
            }
            
            processing_time = time.time() - start_time
            logger.info(f"Round 1A completed for {pdf_path.name} in {processing_time:.2f}s")
            
            if processing_time > 10:
                logger.warning(f"Processing exceeded 10s limit: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing {pdf_path.name}: {str(e)}")
            return {
                "error": str(e),
                "filename": pdf_path.name,
                "round": "1A"
            }
    
    def process_round_1b(self, pdf_paths: List[Path], persona: str, job_description: str) -> Dict:
        """Process multiple PDFs for Round 1B (persona-aware ranking)"""
        try:
            logger.info(f"Processing Round 1B for {len(pdf_paths)} PDFs")
            start_time = time.time()
            
            # Validate all PDFs
            valid_pdfs = []
            for pdf_path in pdf_paths:
                if validate_pdf(pdf_path):
                    valid_pdfs.append(pdf_path)
                else:
                    logger.warning(f"Skipping invalid PDF: {pdf_path}")
            
            if not valid_pdfs:
                raise ValueError("No valid PDFs found")
            
            # Extract and rank sections
            result = self.persona_ranker.rank_sections(valid_pdfs, persona, job_description)
            
            # Add metadata
            result["metadata"] = {
                "documents": [p.name for p in valid_pdfs],
                "persona": persona,
                "job": job_description,
                "processing_time": time.time() - start_time,
                "round": "1B"
            }
            
            processing_time = time.time() - start_time
            logger.info(f"Round 1B completed in {processing_time:.2f}s")
            
            if processing_time > 60:
                logger.warning(f"Processing exceeded 60s limit: {processing_time:.2f}s")
            
            return result
            
        except Exception as e:
            logger.error(f"Error in Round 1B processing: {str(e)}")
            return {
                "error": str(e),
                "persona": persona,
                "job": job_description,
                "round": "1B"
            }
    
    def process_all_pdfs(self, max_workers: int = 8):
        """Process all PDFs in input directory"""
        logger.info(f"Starting processing of all PDFs in {self.input_dir}")
        
        # Find all PDF files
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if not pdf_files:
            logger.warning("No PDF files found in input directory")
            return
        
        logger.info(f"Found {len(pdf_files)} PDF files")
        
        # Process Round 1A for each PDF
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            future_to_pdf = {
                executor.submit(self.process_round_1a, pdf_path): pdf_path 
                for pdf_path in pdf_files
            }
            
            for future in as_completed(future_to_pdf):
                pdf_path = future_to_pdf[future]
                try:
                    result = future.result()
                    output_path = self.output_dir / f"{pdf_path.stem}_outline.json"
                    
                    with open(output_path, 'w', encoding='utf-8') as f:
                        json.dump(result, f, indent=2, ensure_ascii=False)
                    
                    logger.info(f"Saved outline for {pdf_path.name}")
                    
                except Exception as e:
                    logger.error(f"Failed to process {pdf_path.name}: {str(e)}")
    
    def process_persona_query(self, persona: str, job_description: str):
        """Process persona query across all PDFs"""
        logger.info(f"Processing persona query: {persona} - {job_description}")
        
        # Find all PDF files
        pdf_files = list(self.input_dir.glob("*.pdf"))
        if not pdf_files:
            logger.warning("No PDF files found for persona query")
            return
        
        # Process Round 1B
        result = self.process_round_1b(pdf_files, persona, job_description)
        
        # Save result
        output_path = self.output_dir / "persona_ranking.json"
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2, ensure_ascii=False)
        
        logger.info("Saved persona ranking results")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Document Insight Engine')
    parser.add_argument('--mode', choices=['1A', '1B', 'both'], default='both',
                       help='Processing mode (default: both)')
    parser.add_argument('--persona', type=str, help='Persona for Round 1B')
    parser.add_argument('--job', type=str, help='Job description for Round 1B')
    parser.add_argument('--input-dir', default='/app/input', help='Input directory')
    parser.add_argument('--output-dir', default='/app/output', help='Output directory')
    parser.add_argument('--max-workers', type=int, default=8, help='Max worker threads')
    
    args = parser.parse_args()
    
    # Initialize processor
    processor = DocumentProcessor(args.input_dir, args.output_dir)
    
    try:
        if args.mode in ['1A', 'both']:
            processor.process_all_pdfs(args.max_workers)
        
        if args.mode in ['1B', 'both']:
            if args.persona and args.job:
                processor.process_persona_query(args.persona, args.job)
            else:
                logger.info("Skipping Round 1B - persona and job description required")
        
        logger.info("Processing completed successfully")
        
    except Exception as e:
        logger.error(f"Processing failed: {str(e)}")
        raise

if __name__ == "__main__":
    main()
