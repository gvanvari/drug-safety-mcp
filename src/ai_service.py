from openai import OpenAI
import logging

logger = logging.getLogger(__name__)


class AIService:
    """Service for OpenAI integration"""
    
    def __init__(self, api_key: str):
        self.client = OpenAI(api_key=api_key)
    
    def generate_safety_summary(self, drug_name: str, adverse_events_data: dict) -> str:
        """Generate intelligent summary of drug safety using OpenAI"""
        try:
            # Prepare context from adverse events data
            total_events = adverse_events_data.get("total_count", 0)
            events = adverse_events_data.get("adverse_events", [])
            
            # Extract top side effects
            side_effects = {}
            for event in events[:20]:  # Sample top 20
                outcomes = event.get("patient", {}).get("reaction", [])
                for outcome in outcomes:
                    reaction = outcome.get("reactionmeddrapt", "Unknown")
                    side_effects[reaction] = side_effects.get(reaction, 0) + 1
            
            top_effects = sorted(side_effects.items(), key=lambda x: x[1], reverse=True)[:5]
            top_effects_str = ", ".join([effect[0] for effect in top_effects])
            
            # Generate summary using GPT
            prompt = f"""
Analyze the following drug safety data for {drug_name} and provide a brief, clear 2-3 sentence safety summary:

Total Adverse Events Reported: {total_events}
Top Side Effects: {top_effects_str}

Provide a concise, patient-friendly summary that highlights the main safety concerns and who should be careful. 
Be factual and avoid overstating risks. Format: Start with the drug name and main concerns.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a medical safety expert who provides clear, factual drug safety summaries."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=150
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
            return f"Safety data available for {drug_name}. {total_events} adverse events reported."
    
    def generate_comparison_recommendation(self, drugs_data: list) -> str:
        """Generate intelligent comparison recommendation"""
        try:
            drugs_summary = "\n".join([
                f"- {drug['name']}: Safety Score {drug['score']}, Main Concern: {drug['concern']}"
                for drug in drugs_data
            ])
            
            prompt = f"""
Compare the following drugs and provide a brief recommendation (2-3 sentences) on which is safest and for whom:

{drugs_summary}

Be practical and mention specific use cases or patient populations.
            """
            
            response = self.client.chat.completions.create(
                model="gpt-5-nano",
                messages=[
                    {"role": "system", "content": "You are a medical expert who provides practical drug safety comparisons."},
                    {"role": "user", "content": prompt}
                ],
                max_completion_tokens=200
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating recommendation: {e}")
            return "Refer to medical professional for personalized recommendation."
