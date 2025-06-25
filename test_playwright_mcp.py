#!/usr/bin/env python3
"""
Test script to verify Playwright MCP server connectivity
"""

import asyncio
import sys
from mcp import stdio_client, StdioServerParameters

async def test_playwright_mcp():
    """Test if we can connect to the Playwright MCP server and list its tools."""
    
    print("Testing Playwright MCP server connection...")
    
    try:
        # Create connection to Playwright MCP server
        async with stdio_client(
            StdioServerParameters(
                command="npx", 
                args=["@playwright/mcp@latest", "--headless"]
            )
        ) as (read, write):
            
            print("✅ Successfully connected to Playwright MCP server!")
            
            # Try to list available tools
            from mcp.client.session import ClientSession
            
            session = ClientSession(read, write)
            await session.initialize()
            
            print("✅ Session initialized!")
            
            # List tools
            tools_result = await session.list_tools()
            tools = tools_result.tools
            
            print(f"✅ Found {len(tools)} available tools:")
            for i, tool in enumerate(tools, 1):
                print(f"  {i}. {tool.name}: {tool.description}")
            
            print("\n🎉 Playwright MCP server is working correctly!")
            return True
            
    except Exception as e:
        print(f"❌ Error connecting to Playwright MCP server: {e}")
        print(f"Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_playwright_mcp())
    sys.exit(0 if success else 1)
