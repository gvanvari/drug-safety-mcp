#!/usr/bin/env python3
"""
Drug safety operations
Contains the core business logic for drug safety queries
"""

import logging

logger = logging.getLogger(__name__)


async def get_safety_profile(drug_name: str, reference_data, fda_service, ai_service=None) -> str:
    """Get comprehensive safety profile for a drug"""
    try:
        logger.info(f"Fetching safety profile for {drug_name}")
        
        # Try to get FDA generic name from reference data, otherwise use provided name
        fda_name = None
        if reference_data.is_valid_drug(drug_name):
            fda_name = reference_data.get_fda_generic_name(drug_name)
        
        # If not in reference data or no FDA name found, try the provided name directly
        if not fda_name:
            logger.info(f"Drug not in reference database, trying FDA API directly with: {drug_name}")
            fda_name = drug_name
        
        # Get adverse events and recalls
        adverse_events = await fda_service.get_adverse_events(fda_name)
        recalls = await fda_service.get_recalls(fda_name)
        
        if not adverse_events:
            # Try to suggest similar drugs from reference database
            similar = reference_data.search_drugs(drug_name)
            if similar:
                return f"❌ No FDA data found for '{drug_name}'. Did you mean: {', '.join([d.name for d in similar[:5]])}?"
            return f"❌ No FDA data found for '{drug_name}'. Please check the spelling or try a generic drug name."
        
        events_count = adverse_events.get("total_count", 0)
        recall_count = recalls.get("total_count", 0) if recalls else 0
        
        # Generate summary with AI if available
        summary = ""
        if ai_service and adverse_events:
            try:
                summary = ai_service.generate_safety_summary(drug_name, adverse_events)
                logger.info(f"AI Summary Generated: {summary}")
            except Exception as e:
                logger.error(f"Failed to generate AI summary: {e}")
                summary = ""
        
        if not summary:
            summary = f"{drug_name} has {events_count} reported adverse events. Consult healthcare provider for personalized advice."
        
        # Extract side effects from adverse events
        top_side_effects = []
        
        if adverse_events.get("adverse_events"):
            side_effects = {}
            for event in adverse_events["adverse_events"][:50]:
                reactions = event.get("patient", {}).get("reaction", [])
                for reaction in reactions:
                    effect = reaction.get("reactionmeddrapt", "Unknown")
                    side_effects[effect] = side_effects.get(effect, 0) + 1
            
            top_side_effects = [effect for effect, _ in sorted(side_effects.items(), key=lambda x: x[1], reverse=True)[:5]]
        
        # Format output with improved styling
        result = f"## 💊 Safety Profile: {drug_name}\n\n"
        
        # Show AI Analysis first (most important insight)
        if summary:
            result += f"### 🤖 AI Analysis\n\n{summary}\n\n"
        
        result += "---\n\n"
        
        # Display tables side by side using HTML
        result += "<div style='display: flex; gap: 20px; flex-wrap: wrap;'>\n"
        result += "<div style='flex: 1; min-width: 300px;'>\n\n"
        
        # Display key metrics in a table
        result += "### 📊 Key Safety Metrics\n\n"
        result += "| Metric | Count | Status |\n"
        result += "|--------|------:|--------|\n"
        result += f"| **Adverse Event Reports** | {events_count:,} | "
        result += "🟢 Low" if events_count < 1000 else "🟡 Moderate" if events_count < 10000 else "🔴 High"
        result += " |\n"
        result += f"| **Active Recalls** | {recall_count} | "
        result += "✅ None" if recall_count == 0 else f"⚠️ {recall_count} Active"
        result += " |\n\n"
        
        result += "</div>\n"
        result += "<div style='flex: 1; min-width: 300px;'>\n\n"
        
        # Side effects section
        result += "### ⚕️ Common Side Effects\n\n"
        if top_side_effects:
            result += "| # | Side Effect |\n"
            result += "|---|-------------|\n"
            for i, effect in enumerate(top_side_effects, 1):
                result += f"| {i} | {effect} |\n"
        else:
            result += "No significant side effects data available\n"
        
        result += "\n</div>\n"
        result += "</div>\n\n"
        
        result += "---\n\n"
        result += "> ⚠️ *This information is for educational purposes only. Always consult your healthcare provider.*"
        
        return result
        
    except Exception as e:
        logger.error(f"Error fetching safety profile: {e}")
        return f"❌ Error: {str(e)}"


async def check_recalls(drug_name: str, reference_data, fda_service) -> str:
    """Check for active drug recalls"""
    try:
        logger.info(f"Checking recalls for {drug_name}")
        
        # Try to get FDA generic name from reference data, otherwise use provided name
        fda_name = None
        if reference_data.is_valid_drug(drug_name):
            fda_name = reference_data.get_fda_generic_name(drug_name)
        
        # If not in reference data or no FDA name found, try the provided name directly
        if not fda_name:
            logger.info(f"Drug not in reference database, trying FDA API directly with: {drug_name}")
            fda_name = drug_name
        
        # Get recalls
        recalls = await fda_service.get_recalls(fda_name)
        
        if not recalls or recalls.get("total_count", 0) == 0:
            return f"## ✅ No Active Recalls\n\n**{drug_name}** has no active recalls reported.\n\n---\n\n> 🔍 *Data sourced from FDA public API*"
        
        result = f"## 🚨 Active Recalls for {drug_name}\n\n"
        result += "---\n\n"
        
        for i, recall in enumerate(recalls.get("recalls", [])[:10], 1):
            reason = recall.get("reason_for_recall", "Unknown reason")
            classification = recall.get("classification", "N/A")
            recall_date = recall.get("recall_initiation_date", "N/A")
            
            # Classification emoji
            class_emoji = "🔴" if classification == "Class I" else "🟡" if classification == "Class II" else "🟢"
            
            result += f"### {class_emoji} Recall #{i}\n"
            result += f"• **Reason:** {reason}\n"
            result += f"• **Classification:** {classification}\n"
            result += f"• **Date:** {recall_date}\n\n"
        
        result += "---\n\n"
        result += "> ⚠️ *This information is for educational purposes only. Contact your healthcare provider if concerned.*"
        
        return result
        
    except Exception as e:
        logger.error(f"Error checking recalls: {e}")
        return f"❌ Error: {str(e)}"


async def compare_drugs(drug1: str, drug2: str, drug3: str, reference_data, fda_service, ai_service=None) -> str:
    """Compare safety profiles of 2-3 drugs"""
    try:
        drugs_to_compare = [d.strip() for d in [drug1, drug2, drug3] if d.strip()]
        
        if len(drugs_to_compare) < 2:
            return "❌ Please provide at least 2 drugs to compare"
        
        logger.info(f"Comparing drugs: {drugs_to_compare}")
        
        result = f"## 🔬 Drug Safety Comparison\n\n"
        result += "---\n\n"
        
        drugs_data = []
        comparison_text = ""
        
        for drug in drugs_to_compare:
            # Try to get FDA generic name from reference data, otherwise use provided name
            fda_name = None
            if reference_data.is_valid_drug(drug):
                fda_name = reference_data.get_fda_generic_name(drug)
            
            # If not in reference data or no FDA name found, try the provided name directly
            if not fda_name:
                logger.info(f"Drug '{drug}' not in reference database, trying FDA API directly")
                fda_name = drug
            
            # Get adverse events
            adverse_events = await fda_service.get_adverse_events(fda_name)
            
            if not adverse_events:
                # Try to suggest similar drugs from reference database
                similar = reference_data.search_drugs(drug)
                if similar:
                    return f"❌ No FDA data found for '{drug}'. Did you mean: {', '.join([d.name for d in similar[:5]])}?"
                return f"❌ No FDA data found for '{drug}'. Please check the spelling or try a generic drug name."
            
            events_count = adverse_events.get("total_count", 0)
            
            # Get top side effect
            top_effect = ""
            if adverse_events.get("adverse_events"):
                side_effects = {}
                for event in adverse_events["adverse_events"][:50]:
                    reactions = event.get("patient", {}).get("reaction", [])
                    for reaction in reactions:
                        effect = reaction.get("reactionmeddrapt", "Unknown")
                        side_effects[effect] = side_effects.get(effect, 0) + 1
                
                if side_effects:
                    top_effect = max(side_effects.items(), key=lambda x: x[1])[0]
            
            comparison_text += f"\n### 💊 {drug}\n"
            comparison_text += f"• **Adverse Events:** {events_count:,} reports\n"
            comparison_text += f"• **Primary Concern:** {top_effect if top_effect else 'N/A'}\n"
            
            drugs_data.append({
                "name": drug,
                "events": events_count,
                "concern": top_effect if top_effect else "N/A"
            })
        
        result += comparison_text
        
        # Get AI recommendation if available
        if ai_service and len(drugs_data) >= 2:
            recommendation = ai_service.generate_comparison_recommendation(drugs_data)
            result += f"\n---\n\n### 🤖 AI Recommendation\n{recommendation}\n"
        
        result += "\n---\n\n"
        result += "> 📋 *Comparison based on FDA adverse event reports. Consult your healthcare provider for personalized advice.*"
        
        return result
        
    except Exception as e:
        logger.error(f"Error comparing drugs: {e}")
        return f"❌ Error: {str(e)}"
