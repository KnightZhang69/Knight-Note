import requests
import json
import os
import argparse
import re
from datetime import datetime

def sanitize_filename(text):
    """Create a safe filename from user input."""
    # Remove or replace invalid filename characters
    safe_text = re.sub(r'[<>:"/\\|?*]', '_', text)
    # Limit length and remove extra spaces
    safe_text = re.sub(r'\s+', '_', safe_text.strip())
    return safe_text[:50]  # Limit to 50 characters

def save_to_markdown(content, filename=None, query=None):
    """Save the assistant's response to a markdown file."""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        if query:
            safe_query = sanitize_filename(query)
            filename = f"perplexity_{safe_query}_{timestamp}.md"
        else:
            filename = f"perplexity_response_{timestamp}.md"
    
    # Ensure filename has .md extension
    if not filename.endswith('.md'):
        filename += '.md'
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(f"# Perplexity AI Research Report\n\n")
            f.write(f"**Generated on:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            f.write(f"**Research Topic:** {query}\n\n")
            f.write("---\n\n")
            f.write(content)
        
        print(f"✅ Response saved to: {filename}")
        return filename
    except Exception as e:
        print(f"❌ Error saving to markdown file: {e}")
        return None

def get_user_input():
    """Get research topic from user with validation."""
    print("\n🔍 Perplexity AI Research Assistant")
    print("=" * 50)
    print("Enter your research topic or question below.")
    print("Examples:")
    print("  • Impact of AI on healthcare")
    print("  • Latest developments in quantum computing")
    print("  • Analysis of Tesla's autonomous driving technology")
    print("  • Climate change solutions and renewable energy trends")
    print("=" * 50)
    
    while True:
        try:
            topic = input("\n📝 Research Topic: ").strip()
            
            if not topic:
                print("❌ Please enter a research topic. It cannot be empty.")
                continue
            
            if len(topic) < 5:
                print("❌ Please provide a more detailed research topic (at least 5 characters).")
                continue
            
            if len(topic) > 500:
                print("❌ Research topic is too long. Please keep it under 500 characters.")
                continue
            
            # Confirm with user
            print(f"\n📋 You entered: '{topic}'")
            confirm = input("Is this correct? (y/n): ").strip().lower()
            
            if confirm in ['y', 'yes', '']:
                return topic
            elif confirm in ['n', 'no']:
                print("Let's try again...")
                continue
            else:
                print("Please answer with 'y' or 'n'.")
                continue
                
        except KeyboardInterrupt:
            print("\n\n👋 Goodbye!")
            exit(0)
        except EOFError:
            print("\n\n👋 Goodbye!")
            exit(0)

def create_research_prompt(topic):
    """Create a comprehensive research prompt from user topic."""
    return f"Provide a comprehensive, in-depth analysis and research report on: {topic}. Include current trends, key developments, expert insights, statistical data, and cite reliable sources. Structure the response with clear sections and actionable insights."

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Interactive Perplexity AI Research Assistant')
    parser.add_argument('--output', '-o', help='Output markdown filename (optional)')
    parser.add_argument('--query', '-q', help='Research topic (if not provided, will ask interactively)')
    parser.add_argument('--non-interactive', action='store_true', help='Run without interactive prompts (requires --query)')
    args = parser.parse_args()
    
    # Load your Perplexity API key from environment variable for security
    api_key = os.environ.get("PERPLEXITY_API_KEY")

    if not api_key:
        print("❌ Error: PERPLEXITY_API_KEY environment variable not set.")
        print("Please set your API key: export PERPLEXITY_API_KEY='your_api_key_here'")
        return

    # Get research topic
    if args.query:
        research_topic = args.query
        print(f"🔍 Research Topic: {research_topic}")
    elif args.non_interactive:
        print("❌ Error: Non-interactive mode requires --query argument.")
        return
    else:
        research_topic = get_user_input()

    # Create comprehensive prompt
    full_query = create_research_prompt(research_topic)
    
    print(f"\n🚀 Querying Perplexity AI about: '{research_topic}'")
    print("⏳ This may take a moment...")
    
    url = "https://api.perplexity.ai/chat/completions"
    payload = {
        "model": "sonar-reasoning",
        "messages": [
            {"role": "system", "content": "You are a research assistant. Provide detailed, well-structured analysis with citations and sources. Use clear headings and bullet points for better readability."},
            {"role": "user", "content": full_query}
        ],
        "max_tokens": 8000,
        "temperature": 0.3  # Lower temperature for more focused research
    }
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status()  # Check for HTTP errors
        response_data = response.json()
        
        # Extract and display the assistant's reply
        if response_data.get("choices"):
            assistant_message = response_data["choices"][0]["message"]["content"]
            print("\n📊 Research Report Generated!")
            print("=" * 60)
            print(assistant_message)
            print("=" * 60)
            
            # Save to markdown file
            saved_file = save_to_markdown(assistant_message, args.output, research_topic)
            if saved_file:
                print(f"\n💾 Complete research report saved to: {saved_file}")
                print(f"📁 You can now open and review the detailed report!")
        else:
            print("❌ No response received from Perplexity AI")
            print("Raw response:", json.dumps(response_data, indent=2))

    except requests.exceptions.RequestException as e:
        print(f"❌ An error occurred: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print("Error details:", e.response.text)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    main()
