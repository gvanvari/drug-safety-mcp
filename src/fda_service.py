import httpx
import asyncio
from typing import Optional, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class FDAService:
    """Service for interacting with FDA API"""
    
    BASE_URL = "https://api.fda.gov/drug"
    
    def __init__(self, rate_limit_per_minute: int = 60):
        self.rate_limit_per_minute = rate_limit_per_minute
        self.client = httpx.AsyncClient(timeout=10.0)
        self.request_times = []
    
    async def check_rate_limit(self) -> bool:
        """Check if we should rate limit"""
        now = asyncio.get_event_loop().time()
        # Keep only requests from last minute
        self.request_times = [t for t in self.request_times if now - t < 60]
        
        if len(self.request_times) >= self.rate_limit_per_minute:
            logger.warning(f"Rate limit approached: {len(self.request_times)}/{self.rate_limit_per_minute}")
            return False
        
        self.request_times.append(now)
        return True
    
    async def get_adverse_events(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """Get adverse events for a drug"""
        if not await self.check_rate_limit():
            logger.error("Rate limit exceeded")
            return None
        
        try:
            # Try searching by brand name first, then generic name
            search_queries = [
                f'openfda.brand_name:"{drug_name.upper()}"',
                f'openfda.generic_name:"{drug_name.upper()}"',
                f'patient.drug.medicinalproduct:"{drug_name.upper()}"'
            ]
            
            url = f"{self.BASE_URL}/event.json"
            
            for search_query in search_queries:
                try:
                    # Create a fresh client for this request
                    async with httpx.AsyncClient(timeout=10.0) as client:
                        response = await client.get(url, params={"search": search_query, "limit": 100})
                        
                        if response.status_code == 200:
                            data = response.json()
                            if data.get("results"):
                                logger.info(f"Successfully fetched adverse events using query: {search_query}")
                                return {
                                    "adverse_events": data.get("results", []),
                                    "total_count": data.get("meta", {}).get("results", {}).get("total", 0)
                                }
                except Exception as e:
                    logger.debug(f"Query {search_query} failed: {e}")
                    continue
            
            # If no results found, return empty
            logger.warning(f"No adverse events found for {drug_name} with any search query")
            return {
                "adverse_events": [],
                "total_count": 0
            }
        except Exception as e:
            logger.error(f"Error fetching adverse events for {drug_name}: {e}")
            return None
    
    async def get_recalls(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """Get recalls for a drug"""
        if not await self.check_rate_limit():
            logger.error("Rate limit exceeded")
            return None
        
        try:
            search_query = f'openfda.generic_name:"{drug_name.upper()}"'
            url = f"{self.BASE_URL}/enforcement.json"
            
            # Create a fresh client for this request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params={"search": search_query, "limit": 100})
                response.raise_for_status()
                
                data = response.json()
                return {
                    "recalls": data.get("results", []),
                    "total_count": data.get("meta", {}).get("results", {}).get("total", 0)
                }
        except Exception as e:
            logger.error(f"Error fetching recalls for {drug_name}: {e}")
            return None
    
    async def get_drug_info(self, drug_name: str) -> Optional[Dict[str, Any]]:
        """Get general drug info"""
        if not await self.check_rate_limit():
            logger.error("Rate limit exceeded")
            return None
        
        try:
            search_query = f'openfda.generic_name:"{drug_name.upper()}"'
            url = f"{self.BASE_URL}/label.json"
            
            # Create a fresh client for this request
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url, params={"search": search_query, "limit": 10})
                response.raise_for_status()
                
                data = response.json()
                return data.get("results", [])
        except Exception as e:
            logger.error(f"Error fetching drug info for {drug_name}: {e}")
            return None
    
    async def close(self):
        """Close HTTP client"""
        await self.client.aclose()
