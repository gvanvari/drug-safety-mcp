#!/usr/bin/env python3
"""
Natural language query parser for drug safety queries
"""

import re
import logging
from typing import Tuple, List, Optional

logger = logging.getLogger(__name__)


class QueryParser:
    """Parse natural language queries about drug safety"""
    
    @staticmethod
    def parse_query(query: str) -> Tuple[str, List[str]]:
        """
        Parse a natural language query and determine intent and drugs
        
        Returns:
            Tuple of (intent, drug_names)
            intent: 'safety', 'recall', 'compare', or 'unknown'
            drug_names: List of extracted drug names
        """
        query_lower = query.lower().strip()
        
        # Pattern 1: Compare queries
        compare_patterns = [
            r'compare\s+(.+)',
            r'comparison\s+(?:of\s+)?(.+)',
            r'(.+)\s+vs\s+(.+)',
            r'(.+)\s+versus\s+(.+)',
        ]
        
        for pattern in compare_patterns:
            match = re.search(pattern, query_lower)
            if match:
                # Extract drug names from comma/and separated list
                text = match.group(1) if match.lastindex == 1 else f"{match.group(1)}, {match.group(2)}"
                drugs = QueryParser._extract_drug_names(text)
                if len(drugs) >= 2:
                    return 'compare', drugs
        
        # Pattern 2: Recall queries
        recall_patterns = [
            r'(?:any\s+)?recalls?\s+(?:for|on|about)\s+(.+)',
            r'(?:check|find)\s+recalls?\s+(?:for|on)?\s*(.+)',
            r'is\s+(.+)\s+recalled',
            r'has\s+(.+)\s+been\s+recalled',
        ]
        
        for pattern in recall_patterns:
            match = re.search(pattern, query_lower)
            if match:
                drugs = QueryParser._extract_drug_names(match.group(1))
                if drugs:
                    return 'recall', drugs
        
        # Pattern 3: Safety queries (most common)
        safety_patterns = [
            r'(?:tell me about|what about|info on|information on)\s+(.+?)(?:\'s)?\s+safety',
            r'(?:is|how)\s+safe\s+(?:is\s+)?(.+)',
            r'safety\s+(?:of|profile|info|information)\s+(?:for|on|about)?\s*(.+)',
            r'(?:side effects?|adverse events?)\s+(?:of|for)\s+(.+)',
            r'(.+)\s+(?:side effects?|adverse events?|safety)',
            r'(?:what|tell me)\s+(?:about|is)\s+(.+)',
        ]
        
        for pattern in safety_patterns:
            match = re.search(pattern, query_lower)
            if match:
                drugs = QueryParser._extract_drug_names(match.group(1))
                if drugs:
                    return 'safety', drugs
        
        # Fallback: Try to extract any drug name and assume safety query
        drugs = QueryParser._extract_drug_names(query)
        if drugs:
            if len(drugs) >= 2:
                return 'compare', drugs
            else:
                return 'safety', drugs
        
        return 'unknown', []
    
    @staticmethod
    def _extract_drug_names(text: str) -> List[str]:
        """
        Extract drug names from text
        Handles comma-separated, 'and'-separated, or 'vs' separated lists
        """
        # Clean up common words
        text = text.lower().strip()
        
        # Remove common filler words
        for word in ['the', 'a', 'an', 'drug', 'medication', 'medicine']:
            text = re.sub(rf'\b{word}\b', '', text)
        
        # Split by common separators
        separators = r'[,;]|\s+and\s+|\s+vs\.?\s+|\s+versus\s+'
        parts = re.split(separators, text)
        
        # Clean and capitalize each drug name
        drugs = []
        for part in parts:
            part = part.strip()
            if part and len(part) > 2:  # Avoid very short strings
                # Capitalize first letter of each word
                drug_name = ' '.join(word.capitalize() for word in part.split())
                drugs.append(drug_name)
        
        return drugs
    
    @staticmethod
    def get_example_queries() -> List[str]:
        """Return example queries for user guidance"""
        return [
            "Tell me about Ibuprofen's safety",
            "What are the side effects of Aspirin?",
            "Compare Aspirin, Ibuprofen, and Acetaminophen",
            "Is Metformin safe?",
            "Check recalls for Lisinopril",
            "Ibuprofen vs Naproxen",
        ]
