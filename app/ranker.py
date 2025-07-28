# Persona-aware ranking module (see previous chat for full code)
"""
Persona-aware ranking module for Round 1B
Ranks document sections based on persona and job description
"""

import logging
import numpy as np
from typing import Dict, List, Tuple, Optional
from pathlib import Path
import json
import time
from collections import defaultdict

# Import sentence transformers for embeddings
try:
    from sentence_transformers import SentenceTransformer
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.feature_extraction.text import TfidfVectorizer
except ImportError:
    SentenceTransformer = None
    cosine_similarity = None
    TfidfVectorizer = None

from outline import OutlineExtractor
from utils import chunk_text, remove_stopwords, detect_language

logger = logging.getLogger(__name__)

class PersonaRanker:
    """Ranks document sections based on persona and job requirements"""
    
    def __init__(self):
        self.outline_extractor = OutlineExtractor()
        self.model = None
        self.fallback_to_tfidf = False
        
        # Initialize embedding model
        self._init_embedding_model()
        
        # Ranking weights
        self.weights = {
            "semantic_similarity": 0.55,
            "level_weight": 0.25,
            "recency_factor": 0.15,
            "content_boost": 0.05
        }
        
        # Level weights
        self.level_weights = {
            "H1": 1.0,
            "H2": 0.7,
            "H3": 0.4,
            "title": 1.2
        }
    
    def _init_embedding_model(self):
        """Initialize sentence transformer model"""
        if SentenceTransformer is None:
            logger.warning("SentenceTransformers not available, falling back to TF-IDF")
            self.fallback_to_tfidf = True
            return
        
        try:
            # Use lightweight model for CPU-only deployment
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Initialized sentence transformer model")
        except Exception as e:
            logger.error(f"Failed to initialize embedding model: {str(e)}")
            self.fallback_to_tfidf = True
    
    def rank_sections(self, pdf_paths: List[Path], persona: str, job_description: str) -> Dict:
        """Rank sections across multiple PDFs based on persona and job"""
        try:
            start_time = time.time()
            
            # Extract sections from all PDFs
            all_sections = []
            
            for pdf_path in pdf_paths:
                try:
                    # Extract outline
                    outline_result = self.outline_extractor.extract_outline(pdf_path)
                    
                    # Extract full text sections
                    sections = self._extract_full_sections(pdf_path, outline_result)
                    
                    for section in sections:
                        section["document"] = pdf_path.name
                        all_sections.append(section)
                        
                except Exception as e:
                    logger.error(f"Error processing {pdf_path.name}: {str(e)}")
                    continue
            
            if not all_sections:
                raise ValueError("No sections extracted from any PDF")
            
            # Create persona query
            persona_query = f"{persona}: {job_description}"
            
            # Rank sections
            ranked_sections = self._rank_sections_by_relevance(all_sections, persona_query)
            
            # Format output
            result = {
                "extracted_sections": ranked_sections[:10],  # Top 10 sections
                "total_sections": len(all_sections),
                "processing_time": time.time() - start_time
            }
            
            logger.info(f"Ranked {len(all_sections)} sections in {result['processing_time']:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Error in ranking sections: {str(e)}")
            raise
    
    def _extract_full_sections(self, pdf_path: Path, outline_result: Dict) -> List[Dict]:
        """Extract full text content for each section"""
        sections = []
        
        try:
            import fitz
            doc = fitz.open(pdf_path)
            
            outline = outline_result.get("outline", [])
            
            for i, heading in enumerate(outline):
                try:
                    # Determine section boundaries
                    start_page = heading["page"]
                    end_page = outline[i + 1]["page"] if i + 1 < len(outline) else len(doc)
                    
                    # Extract text from section
                    section_text = ""
                    for page_num in range(start_page - 1, min(end_page, len(doc))):
                        page = doc[page_num]
                        page_text = page.get_text()
                        section_text += page_text + "\n"
                    
                    # Clean and chunk text
                    cleaned_text = self._clean_text(section_text)
                    chunks = chunk_text(cleaned_text, max_tokens=200, overlap=50)
                    
                    sections.append({
                        "section_title": heading["text"],
                        "level": heading["level"],
                        "page": heading["page"],
                        "text": cleaned_text,
                        "chunks": chunks,
                        "importance_rank": 0  # Will be set during ranking
                    })
                    
                except Exception as e:
                    logger.warning(f"Error extracting section {heading['text']}: {str(e)}")
                    continue
            
            doc.close()
            
        except Exception as e:
            logger.error(f"Error extracting sections from {pdf_path.name}: {str(e)}")
        
        return sections
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Remove common PDF artifacts
        text = text.replace('\n', ' ').replace('\t', ' ')
        
        return text.strip()
    
    def _rank_sections_by_relevance(self, sections: List[Dict], persona_query: str) -> List[Dict]:
        """Rank sections by relevance to persona query"""
        if not sections:
            return []
        
        # Extract text for similarity calculation
        section_texts = [section["text"] for section in sections]
        
        # Calculate semantic similarity
        if self.fallback_to_tfidf or self.model is None:
            similarities = self._calculate_tfidf_similarity(section_texts, persona_query)
        else:
            similarities = self._calculate_semantic_similarity(section_texts, persona_query)
        
        # Calculate final scores
        for i, section in enumerate(sections):
            score = self._calculate_section_score(section, similarities[i], persona_query)
            section["relevance_score"] = score
            section["importance_rank"] = 0  # Will be set after sorting
        
        # Sort by relevance score
        ranked_sections = sorted(sections, key=lambda x: x["relevance_score"], reverse=True)
        
        # Set importance ranks
        for i, section in enumerate(ranked_sections):
            section["importance_rank"] = i + 1
        
        return ranked_sections
    
    def _calculate_semantic_similarity(self, texts: List[str], query: str) -> List[float]:
        """Calculate semantic similarity using sentence transformers"""
        try:
            # Encode texts and query
            text_embeddings = self.model.encode(texts)
            query_embedding = self.model.encode([query])
            
            # Calculate cosine similarity
            similarities = cosine_similarity(text_embeddings, query_embedding).flatten()
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Error calculating semantic similarity: {str(e)}")
            return [0.0] * len(texts)
    
    def _calculate_tfidf_similarity(self, texts: List[str], query: str) -> List[float]:
        """Fallback TF-IDF similarity calculation"""
        try:
            if TfidfVectorizer is None:
                return [0.0] * len(texts)
            
            # Create TF-IDF vectorizer
            vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
            
            # Fit on texts + query
            all_texts = texts + [query]
            tfidf_matrix = vectorizer.fit_transform(all_texts)
            
            # Calculate similarity
            query_vector = tfidf_matrix[-1]
            text_vectors = tfidf_matrix[:-1]
            
            similarities = cosine_similarity(text_vectors, query_vector).flatten()
            
            return similarities.tolist()
            
        except Exception as e:
            logger.error(f"Error calculating TF-IDF similarity: {str(e)}")
            return [0.0] * len(texts)
    
    def _calculate_section_score(self, section: Dict, similarity: float, query: str) -> float:
        """Calculate final section score using multiple factors"""
        # Semantic similarity
        semantic_score = similarity
        
        # Level weight
        level_score = self.level_weights.get(section["level"], 0.5)
        
        # Content boost for tables, figures, etc.
        content_score = self._calculate_content_boost(section["text"], query)
        
        # Recency factor (placeholder - would need document date parsing)
        recency_score = 0.5
        
        # Combine scores
        final_score = (
            self.weights["semantic_similarity"] * semantic_score +
            self.weights["level_weight"] * level_score +
            self.weights["recency_factor"] * recency_score +
            self.weights["content_boost"] * content_score
        )
        
        return final_score
    
    def _calculate_content_boost(self, text: str, query: str) -> float:
        """Calculate boost for special content types"""
        text_lower = text.lower()
        query_lower = query.lower()
        
        boost = 0.0
        
        # Boost for data/methodology related content
        if any(keyword in query_lower for keyword in ["data", "methodology", "analysis", "research"]):
            if any(keyword in text_lower for keyword in ["table", "figure", "chart", "graph", "dataset"]):
                boost += 0.3
        
        # Boost for financial content
        if any(keyword in query_lower for keyword in ["revenue", "profit", "financial", "earnings"]):
            if any(keyword in text_lower for keyword in ["$", "million", "billion", "percentage", "%"]):
                boost += 0.2
        
        return min(boost, 1.0)
