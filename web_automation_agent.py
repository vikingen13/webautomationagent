#!/usr/bin/env python3
"""
Web Automation Agent using Strands Agents SDK with Playwright MCP - FIXED VERSION
An agent that can browse the web, interact with pages, and perform web automation tasks.
"""

from strands import Agent, tool
from strands_tools import current_time, calculator, file_read, file_write, editor, file_read, file_write, editor
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
import logging
import asyncio
import argparse
import os
import boto3
from botocore.exceptions import NoCredentialsError, CredentialRetrievalError
from pathlib import Path
import subprocess

# Enable debug logging to see what's happening
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

def check_aws_credentials():
    """Check if AWS credentials are available and valid."""
    try:
        session = boto3.Session()
        credentials = session.get_credentials()
        if credentials is None:
            return False, "No AWS credentials found"
        
        # Try to get caller identity to verify credentials work
        sts = session.client('sts')
        identity = sts.get_caller_identity()
        return True, f"AWS credentials valid for account: {identity.get('Account', 'Unknown')}"
    except (NoCredentialsError, CredentialRetrievalError) as e:
        return False, f"AWS credentials error: {str(e)}"
    except Exception as e:
        return False, f"Error checking AWS credentials: {str(e)}"

def get_session_token_from_clipboard():
    """Try to get session token from clipboard (macOS)."""
    try:
        result = subprocess.run(['pbpaste'], capture_output=True, text=True)
        if result.returncode == 0:
            token = result.stdout.strip()
            if len(token) > 100:  # Reasonable length for a session token
                return token
    except Exception:
        pass
    return None

def update_aws_credentials():
    """Update AWS credentials via environment variables."""
    print("🔄 Update AWS Credentials")
    print("Enter your AWS credentials (press Enter to skip a field):")
    
    # Get current values to show as defaults
    current_access_key = os.environ.get('AWS_ACCESS_KEY_ID', '')
    current_secret_key = os.environ.get('AWS_SECRET_ACCESS_KEY', '')
    current_session_token = os.environ.get('AWS_SESSION_TOKEN', '')
    current_region = os.environ.get('AWS_DEFAULT_REGION', 'us-east-1')
    
    # Prompt for new credentials
    access_key = input(f"AWS Access Key ID [{current_access_key[:8]}...]: ").strip()
    if access_key:
        os.environ['AWS_ACCESS_KEY_ID'] = access_key
    
    secret_key = input(f"AWS Secret Access Key [{'*' * 8 if current_secret_key else ''}]: ").strip()
    if secret_key:
        os.environ['AWS_SECRET_ACCESS_KEY'] = secret_key
    
    # Handle session token with clipboard method
    print(f"\n🎫 AWS Session Token [{'Present' if current_session_token else 'Not set'}]:")
    
    if current_session_token:
        clear_token = input("Clear existing session token? (y/N): ").lower().startswith('y')
        if clear_token:
            os.environ.pop('AWS_SESSION_TOKEN', None)
            print("✅ Session token cleared")
            current_session_token = ''
    
    if not current_session_token:
        add_token = input("Add session token? (y/N): ").lower().startswith('y')
        if add_token:
            print("\n📋 Trying to read session token from clipboard...")
            print("💡 Make sure you've copied your AWS session token before proceeding")
            
            session_token = get_session_token_from_clipboard()
            if session_token:
                os.environ['AWS_SESSION_TOKEN'] = session_token
                print(f"✅ Session token set from clipboard (length: {len(session_token)} characters)")
            else:
                print("❌ No valid session token found in clipboard")
                print("💡 Copy your session token and try 'aws-update' again")
                print("   Or set it manually: export AWS_SESSION_TOKEN='your-token-here'")
    
    region = input(f"\nAWS Region [{current_region}]: ").strip()
    if region:
        os.environ['AWS_DEFAULT_REGION'] = region
    elif not region and not current_region:
        os.environ['AWS_DEFAULT_REGION'] = 'us-east-1'
    
    # Clear boto3 credential cache to force refresh
    boto3.DEFAULT_SESSION = None
    
    # Verify the new credentials
    print("\n🔍 Verifying credentials...")
    is_valid, message = check_aws_credentials()
    if is_valid:
        print(f"✅ {message}")
        return True
    else:
        print(f"❌ {message}")
        return False
        return False

def create_agent(playwright_tools, context=None):
    """Create a new agent with the given tools and optional context.
    
    Args:
        playwright_tools: List of Playwright tools to include
        context: Optional conversation context to preserve
        
    Returns:
        Agent: A new agent instance
    """
    # Collect all tools including file operations
    all_tools = [
        current_time, 
        calculator,
        file_read,
        file_write,
        editor
    ]
    all_tools.extend(playwright_tools)
    
    # Create the agent with all tools
    agent = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        tools=all_tools,
        system_prompt="""You are a helpful Web Automation Agent built with Strands Agents SDK with web browsing and file management capabilities.

Your personality and capabilities:
- You're enthusiastic, helpful, and great at web automation and file management tasks
- You can browse websites, interact with web pages, fill forms, click buttons, and extract information
- You can read, write, edit, and manage files in the current workspace
- You respond warmly to greetings
- You can tell the current time and perform calculations when asked
- You explain what you can do when asked for help
- You give friendly goodbyes
- You do not invent answers. If asked to do something using a website, you rely only on information from that website.

Web Automation Capabilities:
- Navigate to websites and browse pages
- Click on links, buttons, and other interactive elements
- Fill out forms and submit them
- Extract text, data, and information from web pages
- Take screenshots of pages
- Handle multiple tabs and windows
- Wait for elements to load
- Perform searches and interactions

File Management Capabilities:
- Read files from the workspace using file_read
- Write content to files using file_write (create new or overwrite existing)
- Advanced file editing operations using editor (modify specific parts of files)
- All file operations work with the current directory and subdirectories

Common Use Cases:
- Extract data from websites and save it to files
- Read configuration files before performing web automation
- Save screenshots and reports from web interactions
- Create logs of web automation activities
- Process data files and use the information for web tasks
- Edit existing files to update configurations or data

When someone asks what you can do or says help, explain your capabilities including both web automation and file management.
When asked to browse the web or interact with websites, use the Playwright tools to accomplish the task.
When asked to work with files, use the file_read, file_write, or editor tools as appropriate.

Be conversational, friendly, and helpful in all responses. Always explain what you're doing when performing web automation or file management tasks.""",
        messages=context
    )
    
    # If context is provided, restore it to the agent
    if context:
        try:
            # Restore conversation context if the agent supports it
            if hasattr(agent, 'restore_context'):
                agent.restore_context(context)
            elif hasattr(agent, '_context'):
                agent._context = context
            print("✅ Agent created with preserved conversation context")
        except Exception as e:
            print(f"⚠️  Could not restore context: {e}")
            print("   Agent created with fresh context")
    
    return agent
    """Force a complete refresh of all AWS credential caches."""
    try:
        # Clear boto3 caches
        boto3.DEFAULT_SESSION = None
        
        # Clear botocore credential cache
        import botocore.session
        if hasattr(botocore.session, '_session_cache'):
            botocore.session._session_cache.clear()
        
        # Clear any cached credentials in botocore
        from botocore.credentials import CredentialResolver
        if hasattr(CredentialResolver, '_cache'):
            CredentialResolver._cache = {}
            
        # Try to clear Strands/Anthropic client caches if they exist
        try:
            import anthropic
            # Reset any cached clients
            if hasattr(anthropic, '_client_cache'):
                anthropic._client_cache.clear()
        except:
            pass
            
        print("🔄 Cleared all AWS credential caches")
        
    except Exception as e:
        print(f"⚠️  Warning: Could not clear all caches: {e}")
        print("   You may need to restart the agent for full credential refresh")

def main(headless=True):
    """Main function to run the web automation agent with proper MCP context management.
    
    Args:
        headless (bool): Whether to run the browser in headless mode. Default is True.
    """
    
    print("Web Automation Agent is starting...")
    print("This agent can browse the web and interact with websites using Playwright!")
    print(f"Browser mode: {'Headless' if headless else 'Visible'}")
    print("Type 'quit' to exit")
    print("-" * 60)
    
    # Create MCP client for Playwright with headless option
    playwright_args = ["@playwright/mcp@latest", "--output-dir=./screenshots/"]
    if headless:
        playwright_args.append("--headless")
    
    playwright_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="npx", 
            args=playwright_args
        )
    ))
    
    try:
        # Use the MCP client within its context manager
        with playwright_mcp_client:
            # Get Playwright tools
            playwright_tools = playwright_mcp_client.list_tools_sync()
            print(f"✅ Successfully loaded {len(playwright_tools)} Playwright tools")
            
            # Create initial agent
            agent = create_agent(playwright_tools)
            
            print("✅ Playwright web automation and file management are ready!")
            print("Try asking me to:")
            print("  - Visit a website and save the content to a file")
            print("  - Read a configuration file and use it for web automation")
            print("  - Search for something on Google and save results")
            print("  - Extract data from a website and create a report")
            print("  - Fill out a form on a website")
            print("  - Extract information from a web page")
            print("  - Read, write, or edit files in the workspace")
            print("\nSpecial commands:")
            print("  - Type 'aws-update' to update AWS credentials")
            print("  - Type 'aws-check' to check current AWS credentials")
            print("-" * 60)
            
            # Interactive loop - WITHIN the MCP context
            while True:
                try:
                    user_input = input("You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("Agent: Goodbye!")
                        break
                    
                    # Handle AWS credential commands
                    if user_input.lower() == 'aws-update':
                        update_aws_credentials()
                        agent = create_agent(playwright_tools, agent.messages)
                        print("✅ AWS credentials updated! Agent will use new credentials on next request.")
                        continue
                    
                    if user_input.lower() == 'aws-check':
                        is_valid, message = check_aws_credentials()
                        print(f"{'✅' if is_valid else '❌'} {message}")
                        continue
                    
                    if not user_input:
                        continue
                    
                    # Process the message through the agent
                    print("Agent: ", end="", flush=True)
                    response = agent(user_input)
                    print("\n")
                    
                except KeyboardInterrupt:
                    print("\nAgent: breaked!")
                except Exception as e:
                    print(f"Error: {e}")
                    
    except Exception as e:
        print(f"❌ Could not connect to Playwright MCP server: {e}")

if __name__ == "__main__":
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Web Automation Agent with Playwright")
    parser.add_argument(
        "--visible", 
        action="store_true", 
        help="Run browser in visible mode (not headless)"
    )
    args = parser.parse_args()
    
    # Run with headless=False if --visible flag is provided
    main(headless=not args.visible)
