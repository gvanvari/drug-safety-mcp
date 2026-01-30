#!/usr/bin/env python3
"""
Gradio client for Drug Safety Intelligence MCP Server
Provides a web interface to test the three tools
"""

import os
import sys
import asyncio
import json
import logging
from dotenv import load_dotenv

import gradio as gr

# Add parent directories to path
import sys
from pathlib import Path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / 'src'))
sys.path.insert(0, str(project_root))

from src.fda_service import FDAService
from src.cache_service import CacheService
from src.reference_data import ReferenceDataLoader
from src.ai_service import AIService
from src.models import SafetyProfile, RecallInfo, DrugComparison, DrugComparisonItem
from clients.shared.drug_operations import get_safety_profile, check_recalls, compare_drugs
from clients.shared.query_parser import QueryParser

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize services
reference_data = ReferenceDataLoader("data/drugs_reference.json")
cache_service = CacheService("data/cache.db", ttl_hours=24)
fda_service = FDAService(rate_limit_per_minute=60)
openai_key = os.getenv("OPENAI_API_KEY")
ai_service = AIService(openai_key) if openai_key else None


# Wrap async functions for Gradio with progress tracking
def get_safety_profile_wrapper(drug_name: str, progress=gr.Progress()) -> str:
    progress(0, desc="🔄 Fetching safety data...")
    result = asyncio.run(get_safety_profile(drug_name, reference_data, fda_service, ai_service))
    progress(1, desc="✅ Complete!")
    return result


def check_recalls_wrapper(drug_name: str, progress=gr.Progress()) -> str:
    progress(0, desc="🔄 Checking FDA recalls...")
    result = asyncio.run(check_recalls(drug_name, reference_data, fda_service))
    progress(1, desc="✅ Complete!")
    return result


def compare_drugs_wrapper(drug1: str, drug2: str, drug3: str = "", progress=gr.Progress()) -> str:
    progress(0, desc="🔄 Comparing drugs...")
    result = asyncio.run(compare_drugs(drug1, drug2, drug3, reference_data, fda_service, ai_service))
    progress(1, desc="✅ Complete!")
    return result


def natural_language_query_wrapper(query: str, progress=gr.Progress()) -> str:
    """Handle natural language queries"""
    if not query.strip():
        return "❌ Please enter a query"
    
    progress(0, desc="🔄 Understanding your query...")
    
    # Parse the query
    intent, drugs = QueryParser.parse_query(query)
    
    logger.info(f"Query: '{query}' | Intent: {intent} | Drugs: {drugs}")
    
    if intent == 'unknown' or not drugs:
        examples = "\n".join([f"• {ex}" for ex in QueryParser.get_example_queries()[:3]])
        return f"❌ I couldn't understand your query. Try questions like:\n\n{examples}"
    
    progress(0.3, desc=f"🔄 Processing {intent} query...")
    
    # Route to appropriate handler
    if intent == 'safety':
        result = asyncio.run(get_safety_profile(drugs[0], reference_data, fda_service, ai_service))
    elif intent == 'recall':
        result = asyncio.run(check_recalls(drugs[0], reference_data, fda_service))
    elif intent == 'compare':
        drug1 = drugs[0] if len(drugs) > 0 else ""
        drug2 = drugs[1] if len(drugs) > 1 else ""
        drug3 = drugs[2] if len(drugs) > 2 else ""
        result = asyncio.run(compare_drugs(drug1, drug2, drug3, reference_data, fda_service, ai_service))
    else:
        result = "❌ Unable to process query"
    
    progress(1, desc="✅ Complete!")
    return result


# Create Gradio interface
with gr.Blocks(title="Drug Safety Intelligence") as demo:
    gr.Markdown("<h1 style='text-align: center;'>🏥 Drug Safety Intelligence</h1>", elem_classes="center")
    gr.Markdown("<p style='text-align: center;'>Query FDA drug safety data with AI-powered insights</p>")
    
    with gr.Tabs():
        # Tab 0: Natural Language Query (NEW)
        with gr.Tab("💬 Ask Anything"):
            gr.Markdown("### Ask questions in plain English about drug safety")
            gr.Markdown("**Examples:**")
            
            example_queries = QueryParser.get_example_queries()
            examples_md = "\n".join([f"• *{ex}*" for ex in example_queries])
            gr.Markdown(examples_md)
            
            with gr.Row():
                nl_query_input = gr.Textbox(
                    label="Your Question",
                    placeholder="e.g., Tell me about Ibuprofen's safety or Compare Aspirin and Naproxen",
                    lines=2
                )
            
            nl_query_btn = gr.Button("Ask", variant="primary")
            nl_query_output = gr.Markdown()
            
            nl_query_btn.click(
                fn=natural_language_query_wrapper,
                inputs=[nl_query_input],
                outputs=[nl_query_output],
                show_progress="full"
            )
        
        # Tab 1: Safety Profile
        with gr.Tab("Safety Profile"):
            gr.Markdown("Get comprehensive safety information about a drug")
            
            with gr.Row():
                drug_input = gr.Textbox(
                    label="Drug Name",
                    placeholder="e.g., Ibuprofen, Aspirin, Metformin",
                    value="Ibuprofen"
                )
            
            profile_btn = gr.Button("Get Safety Profile", variant="primary")
            profile_output = gr.Markdown()
            
            profile_btn.click(
                fn=get_safety_profile_wrapper,
                inputs=[drug_input],
                outputs=[profile_output],
                show_progress="full"
            )
        
        # Tab 2: Check Recalls
        with gr.Tab("Check Recalls"):
            gr.Markdown("Check for active FDA recalls")
            
            with gr.Row():
                recall_input = gr.Textbox(
                    label="Drug Name",
                    placeholder="e.g., Ibuprofen, Aspirin",
                    value="Ibuprofen"
                )
            
            recall_btn = gr.Button("Check Recalls", variant="primary")
            recall_output = gr.Markdown()
            
            recall_btn.click(
                fn=check_recalls_wrapper,
                inputs=[recall_input],
                outputs=[recall_output],
                show_progress="full"
            )
        
        # Tab 3: Compare Drugs
        with gr.Tab("Compare Drugs"):
            gr.Markdown("Compare safety profiles of 2-3 drugs")
            
            with gr.Row():
                drug1_input = gr.Textbox(
                    label="Drug 1",
                    placeholder="e.g., Ibuprofen",
                    value="Ibuprofen"
                )
                drug2_input = gr.Textbox(
                    label="Drug 2",
                    placeholder="e.g., Aspirin",
                    value="Aspirin"
                )
            
            with gr.Row():
                drug3_input = gr.Textbox(
                    label="Drug 3 (Optional)",
                    placeholder="e.g., Acetaminophen",
                    value="Acetaminophen"
                )
            
            compare_btn = gr.Button("Compare", variant="primary")
            compare_output = gr.Markdown()
            
            compare_btn.click(
                fn=compare_drugs_wrapper,
                inputs=[drug1_input, drug2_input, drug3_input],
                outputs=[compare_output],
                show_progress="full"
            )
    
    gr.Markdown("""
    ---
    **Notes:**
    - Data is cached for 24 hours to improve performance
    - AI summaries require OPENAI_API_KEY to be set in .env
    - All data comes from FDA public API
    - This is for informational purposes only, not medical advice
    """)


if __name__ == "__main__":
    demo.launch(share=False, show_error=True)
