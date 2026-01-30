#!/usr/bin/env python3
"""
Drug Safety Intelligence MCP Server
Provides tools for analyzing drug safety using FDA API, caching, and OpenAI
"""

import os
import json
import logging
import asyncio
import sys
from datetime import datetime, timedelta
from typing import Any

from dotenv import load_dotenv
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Import our services
from models import SafetyProfile, RecallInfo, DrugComparison, DrugComparisonItem
from reference_data import ReferenceDataLoader
from cache_service import CacheService
from fda_service import FDAService
from ai_service import AIService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
reference_data = ReferenceDataLoader("data/drugs_reference.json")
cache_service = CacheService("data/cache.db", ttl_hours=24)
fda_service = FDAService(rate_limit_per_minute=60)
openai_key = os.getenv("OPENAI_API_KEY")
if not openai_key:
    logger.warning("OPENAI_API_KEY not set. AI summarization will be disabled.")
ai_service = AIService(openai_key) if openai_key else None

# Create MCP server
server = Server("Drug Safety Intelligence")


@server.list_tools()
async def handle_list_tools():
    """List available tools"""
    return [
        Tool(
            name="drug_safety_profile",
            description="Get comprehensive safety profile for a drug. Combines FDA adverse event data, caching, reference data, and AI summarization.",
            inputSchema={
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "Name of the drug to analyze"
                    }
                },
                "required": ["drug_name"]
            }
        ),
        Tool(
            name="check_drug_recalls",
            description="Quick check for active drug recalls.",
            inputSchema={
                "type": "object",
                "properties": {
                    "drug_name": {
                        "type": "string",
                        "description": "Name of the drug to check"
                    }
                },
                "required": ["drug_name"]
            }
        ),
        Tool(
            name="compare_drug_safety",
            description="Compare safety profiles of 2-3 drugs.",
            inputSchema={
                "type": "object",
                "properties": {
                    "drugs": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of drug names to compare (2-3 drugs)"
                    }
                },
                "required": ["drugs"]
            }
        )
    ]


@server.call_tool()
async def handle_call_tool(name: str, arguments: dict):
    """Handle tool calls"""
    try:
        if name == "drug_safety_profile":
            result = await drug_safety_profile(arguments["drug_name"])
            return [TextContent(type="text", text=result.model_dump_json(indent=2))]
        elif name == "check_drug_recalls":
            result = await check_drug_recalls(arguments["drug_name"])
            return [TextContent(type="text", text=result.model_dump_json(indent=2))]
        elif name == "compare_drug_safety":
            result = await compare_drug_safety(arguments["drugs"])
            return [TextContent(type="text", text=result.model_dump_json(indent=2))]
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
    except Exception as e:
        logger.error(f"Error handling tool {name}: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def drug_safety_profile(drug_name: str) -> SafetyProfile:
    """
    Get comprehensive safety profile for a drug.
    
    Combines FDA adverse event data, caching, reference data, and AI summarization.
    
    Args:
        drug_name: Name of the drug to analyze
    
    Returns:
        SafetyProfile with safety score, summary, and detailed data
    """
    try:
        # Validate drug exists in reference data
        if not reference_data.is_valid_drug(drug_name):
            similar = reference_data.search_drugs(drug_name)
            if similar:
                raise ValueError(f"Drug '{drug_name}' not found. Did you mean: {', '.join([d.name for d in similar])}?")
            raise ValueError(f"Drug '{drug_name}' not found in reference database")
        
        # Check cache first
        cached_data = cache_service.get(drug_name)
        if cached_data:
            cache_age = cache_service.get_cache_age(drug_name)
            hours_old = cache_age // 3600 if cache_age else 0
            
            profile = SafetyProfile(
                drug_name=drug_name,
                safety_score=cached_data.get("safety_score", 75),
                summary=cached_data.get("summary", ""),
                adverse_events_count=cached_data.get("adverse_events_count", 0),
                top_side_effects=cached_data.get("top_side_effects", []),
                high_risk_demographics=cached_data.get("high_risk_demographics", []),
                active_recalls=cached_data.get("active_recalls", 0),
                data_freshness=f"{hours_old} hours old (cached)",
                cached=True
            )
            logger.info(f"Returning cached profile for {drug_name}")
            return profile
        
        # Get FDA generic name
        fda_name = reference_data.get_fda_generic_name(drug_name)
        if not fda_name:
            raise ValueError(f"FDA generic name not found for {drug_name}")
        
        # Fetch from FDA API
        logger.info(f"Fetching data from FDA API for {drug_name}")
        
        # Get adverse events and recalls
        adverse_events = await fda_service.get_adverse_events(fda_name)
        recalls = await fda_service.get_recalls(fda_name)
        
        if not adverse_events:
            raise ValueError(f"Could not fetch data from FDA API for {drug_name}")
        
        # Extract data
        events_count = adverse_events.get("total_count", 0)
        recall_count = recalls.get("total_count", 0) if recalls else 0
        
        # Generate safety score (simple heuristic)
        safety_score = max(0, min(100, 100 - (events_count / 1000)))
        
        # Generate summary with AI if available
        summary = ""
        if ai_service:
            summary = ai_service.generate_safety_summary(drug_name, adverse_events)
        else:
            summary = f"{drug_name} has {events_count} reported adverse events. Consult healthcare provider for personalized advice."
        
        # Extract side effects from adverse events
        top_side_effects = []
        high_risk_demographics = []
        
        if adverse_events.get("adverse_events"):
            side_effects = {}
            ages = {}
            for event in adverse_events["adverse_events"][:50]:
                # Extract reactions
                reactions = event.get("patient", {}).get("reaction", [])
                for reaction in reactions:
                    effect = reaction.get("reactionmeddrapt", "Unknown")
                    side_effects[effect] = side_effects.get(effect, 0) + 1
                
                # Extract age
                age = event.get("patient", {}).get("patientonsetage")
                if age:
                    try:
                        age_int = int(float(age))
                        if age_int > 65:
                            ages["65+"] = ages.get("65+", 0) + 1
                        elif age_int > 40:
                            ages["40-65"] = ages.get("40-65", 0) + 1
                    except:
                        pass
            
            top_side_effects = [effect[0] for effect in sorted(side_effects.items(), key=lambda x: x[1], reverse=True)[:5]]
            if ages:
                high_risk_demographics = [f"Elderly ({age})" if age == "65+" else f"Middle-aged ({age})" for age in sorted(ages.keys())]
        
        # Cache the data
        cache_data = {
            "safety_score": safety_score,
            "summary": summary,
            "adverse_events_count": events_count,
            "top_side_effects": top_side_effects,
            "high_risk_demographics": high_risk_demographics,
            "active_recalls": recall_count
        }
        cache_service.set(drug_name, cache_data)
        
        profile = SafetyProfile(
            drug_name=drug_name,
            safety_score=safety_score,
            summary=summary,
            adverse_events_count=events_count,
            top_side_effects=top_side_effects,
            high_risk_demographics=high_risk_demographics,
            active_recalls=recall_count,
            data_freshness="Just fetched from FDA",
            cached=False
        )
        
        logger.info(f"Successfully generated profile for {drug_name}")
        return profile
    
    except Exception as e:
        logger.error(f"Error in drug_safety_profile: {e}")
        raise


async def check_drug_recalls(drug_name: str) -> RecallInfo:
    """
    Quick check for active drug recalls.
    
    Args:
        drug_name: Name of the drug to check
    
    Returns:
        RecallInfo with recall status and details
    """
    try:
        # Validate drug
        if not reference_data.is_valid_drug(drug_name):
            raise ValueError(f"Drug '{drug_name}' not found in reference database")
        
        fda_name = reference_data.get_fda_generic_name(drug_name)
        
        # Fetch recalls
        recalls = await fda_service.get_recalls(fda_name)
        
        if not recalls:
            return RecallInfo(
                drug_name=drug_name,
                recalls=[],
                status="No recall data available"
            )
        
        recall_list = recalls.get("recalls", [])
        status = f"No active recalls" if not recall_list else f"{len(recall_list)} recall(s) found"
        
        return RecallInfo(
            drug_name=drug_name,
            recalls=recall_list[:5],  # Return top 5
            status=status
        )
    
    except Exception as e:
        logger.error(f"Error in check_drug_recalls: {e}")
        raise


async def compare_drug_safety(drugs: list) -> DrugComparison:
    """
    Compare safety profiles of multiple drugs.
    
    Args:
        drugs: List of drug names to compare (2-3 drugs)
    
    Returns:
        DrugComparison with scores and recommendation
    """
    try:
        if not drugs or len(drugs) < 2:
            raise ValueError("Please provide at least 2 drugs to compare")
        
        if len(drugs) > 3:
            raise ValueError("Maximum 3 drugs can be compared at once")
        
        # Get profiles for all drugs
        comparison_items = []
        for drug_name in drugs:
            profile = await drug_safety_profile(drug_name)
            
            # Determine top concern (simplified)
            concern = "Monitor for side effects"
            if profile.top_side_effects:
                concern = f"Watch for {profile.top_side_effects[0]}"
            if profile.high_risk_demographics:
                concern = f"Risky for {profile.high_risk_demographics[0]}"
            
            comparison_items.append(DrugComparisonItem(
                drug_name=drug_name,
                safety_score=profile.safety_score,
                top_concern=concern
            ))
        
        # Generate recommendation with AI if available
        recommendation = ""
        if ai_service:
            drugs_data = [
                {
                    "name": item.drug_name,
                    "score": item.safety_score,
                    "concern": item.top_concern
                }
                for item in comparison_items
            ]
            recommendation = ai_service.generate_comparison_recommendation(drugs_data)
        else:
            # Fallback recommendation
            safest = max(comparison_items, key=lambda x: x.safety_score)
            recommendation = f"{safest.drug_name} has the best safety profile. Consult healthcare provider for personalized advice."
        
        return DrugComparison(
            comparison=comparison_items,
            recommendation=recommendation
        )
    
    except Exception as e:
        logger.error(f"Error in compare_drug_safety: {e}")
        raise


async def main():
    """Run the MCP server"""
    logger.info("Starting Drug Safety Intelligence MCP Server")
    logger.info(f"Reference drugs loaded: {len(reference_data.drugs)}")
    logger.info("Available tools: drug_safety_profile, check_drug_recalls, compare_drug_safety")
    
    # Use stdio transport for MCP server
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, None)


if __name__ == "__main__":
    import sys
    asyncio.run(main())
