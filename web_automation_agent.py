#!/usr/bin/env python3
"""
Web Automation Agent using Strands Agents SDK with Playwright MCP - FIXED VERSION
An agent that can browse the web, interact with pages, and perform web automation tasks.
"""

from strands import Agent, tool
from strands_tools import current_time, calculator
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters
import logging
import asyncio

# Enable debug logging to see what's happening
logging.getLogger("strands").setLevel(logging.INFO)
logging.basicConfig(
    format="%(levelname)s | %(name)s | %(message)s",
    handlers=[logging.StreamHandler()]
)

def main():
    """Main function to run the web automation agent with proper MCP context management."""
    
    print("Web Automation Agent is starting...")
    print("This agent can browse the web and interact with websites using Playwright!")
    print("Type 'quit' to exit")
    print("-" * 60)
    
    # Create MCP client for Playwright
    playwright_mcp_client = MCPClient(lambda: stdio_client(
        StdioServerParameters(
            command="npx", 
            args=["@playwright/mcp@latest", "--headless", "--output-dir=./screenshots/"]
        )
    ))
    
    try:
        # Use the MCP client within its context manager
        with playwright_mcp_client:
            # Get Playwright tools
            playwright_tools = playwright_mcp_client.list_tools_sync()
            print(f"✅ Successfully loaded {len(playwright_tools)} Playwright tools")
            
            # Collect all tools
            all_tools = [
                current_time, 
                calculator
            ]
            all_tools.extend(playwright_tools)
            
            # Create the agent with all tools
            agent = Agent(
                model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
                tools=all_tools,
                system_prompt="""You are a helpful Web Automation Agent built with Strands Agents SDK and Playwright capabilities.

Your personality and capabilities:
- You're enthusiastic, helpful, and great at web automation tasks
- You can browse websites, interact with web pages, fill forms, click buttons, and extract information
- You respond warmly to greetings
- You can tell the current time and perform calculations when asked
- You explain what you can do when asked for help
- You give friendly goodbyes
- You do not invent answers. If asked to do something using a website, you rely only on informations from that website.

Web Automation Capabilities:
- Navigate to websites and browse pages
- Click on links, buttons, and other interactive elements
- Fill out forms and submit them
- Extract text, data, and information from web pages
- Take screenshots of pages
- Handle multiple tabs and windows
- Wait for elements to load
- Perform searches and interactions

When someone asks what you can do or says help, explain your capabilities including web automation.
When asked to browse the web or interact with websites, use the Playwright tools to accomplish the task.

Be conversational, friendly, and helpful in all responses. Always explain what you're doing when performing web automation tasks."""
            )
            
            print("✅ Playwright web automation is ready!")
            print("Try asking me to:")
            print("  - Visit a website and tell you about it")
            print("  - Search for something on Google")
            print("  - Fill out a form on a website")
            print("  - Extract information from a web page")
            print("-" * 60)
            
            # Interactive loop - WITHIN the MCP context
            while True:
                try:
                    user_input = input("You: ").strip()
                    
                    if user_input.lower() in ['quit', 'exit', 'q']:
                        print("Agent: Goodbye!")
                        break
                    
                    if not user_input:
                        continue
                    
                    # Process the message through the agent
                    print("Agent: ", end="", flush=True)
                    response = agent(user_input)
                    print(response.message)
                    
                except KeyboardInterrupt:
                    print("\nAgent: breaked!")
                except Exception as e:
                    print(f"Error: {e}")
                    
    except Exception as e:
        print(f"❌ Could not connect to Playwright MCP server: {e}")

if __name__ == "__main__":
    main()
