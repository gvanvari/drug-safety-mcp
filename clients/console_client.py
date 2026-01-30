#!/usr/bin/env python3
"""
Console client for Drug Safety Intelligence MCP Server
Provides a command-line interface to test the three tools
"""

import os
import sys
import asyncio
import argparse
import logging
from dotenv import load_dotenv

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
from clients.shared.drug_operations import get_safety_profile, check_recalls, compare_drugs
from clients.shared.query_parser import QueryParser

# Load environment
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.WARNING)  # Less verbose for console
logger = logging.getLogger(__name__)

# Initialize services
reference_data = ReferenceDataLoader("data/drugs_reference.json")
cache_service = CacheService("data/cache.db", ttl_hours=24)
fda_service = FDAService(rate_limit_per_minute=60)
openai_key = os.getenv("OPENAI_API_KEY")
ai_service = AIService(openai_key) if openai_key else None


def print_banner():
    """Print welcome banner"""
    print("\n" + "="*70)
    print("🏥 Drug Safety Intelligence - Console Client")
    print("="*70)
    print()


def print_result(result: str):
    """Print formatted result"""
    # Strip markdown for console display (basic)
    import re
    # Remove HTML tags
    result = re.sub(r'<[^>]+>', '', result)
    # Convert markdown headers to uppercase
    result = re.sub(r'###\s+(.+)', r'\n\1:', result)
    result = re.sub(r'##\s+(.+)', r'\n\1\n' + '-'*50, result)
    # Remove markdown bold
    result = re.sub(r'\*\*(.+?)\*\*', r'\1', result)
    
    print("\n" + result + "\n")


async def handle_safety_query(drug_name: str):
    """Handle safety profile query"""
    print(f"\n🔄 Fetching safety profile for {drug_name}...")
    result = await get_safety_profile(drug_name, reference_data, fda_service, ai_service)
    print_result(result)


async def handle_recall_query(drug_name: str):
    """Handle recall check query"""
    print(f"\n🔄 Checking recalls for {drug_name}...")
    result = await check_recalls(drug_name, reference_data, fda_service)
    print_result(result)


async def handle_compare_query(drugs: list):
    """Handle drug comparison query"""
    drug1 = drugs[0] if len(drugs) > 0 else ""
    drug2 = drugs[1] if len(drugs) > 1 else ""
    drug3 = drugs[2] if len(drugs) > 2 else ""
    
    print(f"\n🔄 Comparing {', '.join([d for d in drugs if d])}...")
    result = await compare_drugs(drug1, drug2, drug3, reference_data, fda_service, ai_service)
    print_result(result)


async def handle_natural_language_query(query: str):
    """Handle natural language query"""
    print(f"\n🔄 Understanding your query...")
    
    intent, drugs = QueryParser.parse_query(query)
    
    if intent == 'unknown' or not drugs:
        print("\n❌ I couldn't understand your query. Try questions like:")
        for ex in QueryParser.get_example_queries()[:3]:
            print(f"  • {ex}")
        return
    
    print(f"📝 Detected: {intent.upper()} query for {', '.join(drugs)}")
    
    if intent == 'safety':
        await handle_safety_query(drugs[0])
    elif intent == 'recall':
        await handle_recall_query(drugs[0])
    elif intent == 'compare':
        await handle_compare_query(drugs)


def interactive_mode():
    """Run in interactive REPL mode"""
    print_banner()
    print("Interactive Mode - Type 'help' for commands, 'quit' to exit\n")
    
    while True:
        try:
            query = input("🏥 > ").strip()
            
            if not query:
                continue
            
            if query.lower() in ['quit', 'exit', 'q']:
                print("\n👋 Goodbye!\n")
                break
            
            if query.lower() == 'help':
                print("\nAvailable Commands:")
                print("  • safety <drug>          - Get safety profile")
                print("  • recall <drug>          - Check for recalls")
                print("  • compare <drug1> <drug2> [drug3] - Compare drugs")
                print("  • ask <question>         - Natural language query")
                print("  • help                   - Show this help")
                print("  • quit                   - Exit")
                print("\nOr just ask naturally:")
                for ex in QueryParser.get_example_queries()[:3]:
                    print(f"  • {ex}")
                print()
                continue
            
            # Parse command
            parts = query.split(maxsplit=1)
            command = parts[0].lower()
            
            if command == 'safety' and len(parts) > 1:
                asyncio.run(handle_safety_query(parts[1]))
            elif command == 'recall' and len(parts) > 1:
                asyncio.run(handle_recall_query(parts[1]))
            elif command == 'compare' and len(parts) > 1:
                drugs = [d.strip() for d in parts[1].split(',') if d.strip()]
                if len(drugs) < 2:
                    drugs = parts[1].split()
                asyncio.run(handle_compare_query(drugs))
            elif command == 'ask' and len(parts) > 1:
                asyncio.run(handle_natural_language_query(parts[1]))
            else:
                # Try as natural language query
                asyncio.run(handle_natural_language_query(query))
        
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}\n")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Drug Safety Intelligence Console Client',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  Interactive mode:
    python console_client.py
  
  Direct commands:
    python console_client.py safety Ibuprofen
    python console_client.py recall Aspirin
    python console_client.py compare Ibuprofen Aspirin
    python console_client.py ask "Tell me about Metformin's safety"
        """
    )
    
    parser.add_argument('command', nargs='?', choices=['safety', 'recall', 'compare', 'ask'],
                       help='Command to execute')
    parser.add_argument('args', nargs='*', help='Arguments for the command')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.INFO)
    
    # If no command, run interactive mode
    if not args.command:
        interactive_mode()
        return
    
    # Direct command mode
    print_banner()
    
    try:
        if args.command == 'safety':
            if not args.args:
                print("❌ Error: Please provide a drug name")
                print("Usage: python console_client.py safety <drug_name>")
                sys.exit(1)
            asyncio.run(handle_safety_query(' '.join(args.args)))
        
        elif args.command == 'recall':
            if not args.args:
                print("❌ Error: Please provide a drug name")
                print("Usage: python console_client.py recall <drug_name>")
                sys.exit(1)
            asyncio.run(handle_recall_query(' '.join(args.args)))
        
        elif args.command == 'compare':
            if len(args.args) < 2:
                print("❌ Error: Please provide at least 2 drug names")
                print("Usage: python console_client.py compare <drug1> <drug2> [drug3]")
                sys.exit(1)
            asyncio.run(handle_compare_query(args.args))
        
        elif args.command == 'ask':
            if not args.args:
                print("❌ Error: Please provide a question")
                print('Usage: python console_client.py ask "your question here"')
                sys.exit(1)
            asyncio.run(handle_natural_language_query(' '.join(args.args)))
    
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
