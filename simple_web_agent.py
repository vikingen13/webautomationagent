#!/usr/bin/env python3

from strands import Agent
from strands.tools.mcp import MCPClient
from mcp import stdio_client, StdioServerParameters

# Create MCP client for Playwright in visible mode
playwright_args = ["@playwright/mcp@latest", "--output-dir=./screenshots/"]

playwright_mcp_client = MCPClient(lambda: stdio_client(
    StdioServerParameters(
        command="npx",
        args=playwright_args
    )
))

# Use the MCP client within its context manager
with playwright_mcp_client:
    # Get Playwright tools
    playwright_tools = playwright_mcp_client.list_tools_sync()
    
    # Create agent
    agent = Agent(
        model="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        tools=playwright_tools,
        system_prompt="""You are a specialized web automation agent using Playwright.

Your main capabilities:
- Navigate to websites (ALWAYS use Playwright tools for this)
- Click on elements, buttons, links
- Fill out forms
- Extract text and data
- Take screenshots
- Interact with web pages

IMPORTANT: When asked to go to a website or interact with a page, 
use your Playwright tools IMMEDIATELY."""
    )
    
    print("\n🌐 Agent Web Automation")
    
    # Interactive loop - WITHIN the MCP context
    while True:
        user_input = input("Vous: ").strip()
        
        # Process the message through the agent
        print("Agent: ", end="", flush=True)
        response = agent(user_input)
        print("\n")
