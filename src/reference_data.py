import json
import os
from pathlib import Path
from typing import List, Optional
from models import Drug


class ReferenceDataLoader:
    """Loads and manages reference drug data"""
    
    def __init__(self, data_path: str = "data/drugs_reference.json"):
        self.data_path = data_path
        self.drugs: List[Drug] = []
        self.drug_map = {}
        self._load()
    
    def _load(self):
        """Load drugs from JSON file"""
        try:
            with open(self.data_path, 'r') as f:
                data = json.load(f)
                self.drugs = [Drug(**drug) for drug in data.get('drugs', [])]
                # Create case-insensitive lookup map
                for drug in self.drugs:
                    self.drug_map[drug.name.lower()] = drug
                    self.drug_map[drug.fda_generic_name.lower()] = drug
        except FileNotFoundError:
            print(f"Warning: Reference data file not found at {self.data_path}")
            self.drugs = []
    
    def get_drug(self, drug_name: str) -> Optional[Drug]:
        """Get drug by name (case-insensitive)"""
        return self.drug_map.get(drug_name.lower())
    
    def search_drugs(self, query: str) -> List[Drug]:
        """Search drugs by name or generic name"""
        query_lower = query.lower()
        return [
            drug for drug in self.drugs
            if query_lower in drug.name.lower() or 
               query_lower in drug.fda_generic_name.lower()
        ]
    
    def is_valid_drug(self, drug_name: str) -> bool:
        """Check if drug exists in reference data"""
        return drug_name.lower() in self.drug_map
    
    def get_fda_generic_name(self, drug_name: str) -> Optional[str]:
        """Get FDA generic name for a drug"""
        drug = self.get_drug(drug_name)
        return drug.fda_generic_name if drug else None
