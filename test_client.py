import asyncio
import sys
from typing import Optional
from contextlib import AsyncExitStack
import logging
import os

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from anthropic import Anthropic
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger('mcp_client')

# Load environment variables
load_dotenv()

# Verify API key
api_key = os.getenv('ANTHROPIC_API_KEY')
if not api_key:
    logger.error("ANTHROPIC_API_KEY not found in environment variables")
    print("Error: ANTHROPIC_API_KEY not found in environment variables")
    print("Please create a .env file with your Anthropic API key")
    sys.exit(1)

class MCPClient:
    def __init__(self):
        # Initialize session and client objects
        self.session: Optional[ClientSession] = None
        self.exit_stack = AsyncExitStack()
        self.anthropic = Anthropic(api_key=api_key)
        self.connected = False
        self.last_search_results = None

    async def connect_to_server(self, server_script_path: str):
        """Connect to an MCP server

        Args:
            server_script_path: Path to the server script (.py or .js)
        """
        try:
            is_python = server_script_path.endswith('.py')
            is_js = server_script_path.endswith('.js')
            if not (is_python or is_js):
                raise ValueError("Server script must be a .py or .js file")

            command = "python" if is_python else "node"
            server_params = StdioServerParameters(
                command=command,
                args=[server_script_path],
                env=None
            )

            logger.info(f"Connecting to server: {server_script_path}")
            stdio_transport = await self.exit_stack.enter_async_context(stdio_client(server_params))
            self.stdio, self.write = stdio_transport
            self.session = await self.exit_stack.enter_async_context(ClientSession(self.stdio, self.write))

            await self.session.initialize()

            # List available tools
            response = await self.session.list_tools()
            tools = response.tools
            logger.info(f"Connected to server with tools: {[tool.name for tool in tools]}")
            self.connected = True
            return True
        except Exception as e:
            logger.error(f"Failed to connect to server: {str(e)}", exc_info=True)
            self.connected = False
            raise

    async def process_query(self, query: str) -> str:
        """Process a query using Claude and available tools"""
        if not self.connected:
            return "Error: Not connected to server. Please connect first."

        try:
            # Check if this is a direct command
            if query.startswith("add ") and "products to cart" in query:
                # Directly call add_products_to_cart tool
                try:
                    max_products = int(query.split()[1])
                    result = await self.session.call_tool("add_products_to_cart", {"max_products": max_products})
                    return result.content
                except Exception as e:
                    return f"Error adding to cart: {str(e)}"
            elif query.startswith("search for "):
                # Directly call search_amazon tool
                search_term = query.replace("search for ", "")
                result = await self.session.call_tool("search_amazon", {"query": search_term})
                self.last_search_results = result.content
                return result.content
            else:
                # Let Claude handle other queries
                messages = [
                    {
                        "role": "user",
                        "content": query
                    }
                ]

                response = await self.session.list_tools()
                available_tools = [{
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                } for tool in response.tools]

                # Initial Claude API call
                response = self.anthropic.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=1000,
                    messages=messages,
                    tools=available_tools
                )

                # Process response and handle tool calls
                final_text = []

                assistant_message_content = []
                for content in response.content:
                    if content.type == 'text':
                        final_text.append(content.text)
                        assistant_message_content.append(content)
                    elif content.type == 'tool_use':
                        tool_name = content.name
                        tool_args = content.input

                        logger.info(f"Calling tool {tool_name} with args {tool_args}")
                        # Execute tool call
                        try:
                            result = await self.session.call_tool(tool_name, tool_args)
                            if tool_name == "search_amazon":
                                self.last_search_results = result.content
                            final_text.append(f"[Tool {tool_name} executed successfully]")
                        except Exception as e:
                            logger.error(f"Tool call failed: {str(e)}", exc_info=True)
                            final_text.append(f"[Error executing tool {tool_name}: {str(e)}]")
                            result = {"content": f"Error: {str(e)}"}

                        assistant_message_content.append(content)
                        messages.append({
                            "role": "assistant",
                            "content": assistant_message_content
                        })
                        messages.append({
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": result.content
                                }
                            ]
                        })

                        # Get next response from Claude
                        response = self.anthropic.messages.create(
                            model="claude-3-5-sonnet-20241022",
                            max_tokens=1000,
                            messages=messages,
                            tools=available_tools
                        )

                        final_text.append(response.content[0].text)

                return "\n".join(final_text)
        except Exception as e:
            logger.error(f"Error processing query: {str(e)}", exc_info=True)
            return f"Error processing query: {str(e)}"

    async def chat_loop(self):
        """Run an interactive chat loop"""
        print("\nMCP Client Started!")
        print("Available commands:")
        print("- Type a search term to search Amazon and add products to cart")
        print("- Type 'quit' to exit")
        print("- Type 'help' to show this help message")

        while True:
            try:
                query = input("\nSearch term: ").strip().lower()

                if query == 'quit':
                    break
                elif query == 'help':
                    print("\nAvailable commands:")
                    print("- Type a search term to search Amazon and add products to cart")
                    print("- Type 'quit' to exit")
                    print("- Type 'help' to show this help message")
                    continue

                # First perform the search
                print(f"\nSearching for: {query}")
                search_response = await self.process_query(f"search for {query}")
                print("\nSearch results:")
                print(search_response)

                # Then automatically add products to cart
                print("\nAdding products to cart...")
                add_to_cart_response = await self.process_query("add 6 products to cart")
                print("\nAdd to cart results:")
                print(add_to_cart_response)

            except KeyboardInterrupt:
                print("\nExiting...")
                break
            except Exception as e:
                logger.error(f"Error in chat loop: {str(e)}", exc_info=True)
                print(f"\nError: {str(e)}")

    async def cleanup(self):
        """Clean up resources"""
        try:
            if self.connected:
                logger.info("Cleaning up client resources")
                await self.exit_stack.aclose()
                self.connected = False
        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}", exc_info=True)

async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_client.py <path_to_server_script>")
        sys.exit(1)

    client = MCPClient()
    try:
        await client.connect_to_server(sys.argv[1])
        await client.chat_loop()
    except Exception as e:
        logger.error(f"Fatal error: {str(e)}", exc_info=True)
        print(f"Fatal error: {str(e)}")
    finally:
        await client.cleanup()

if __name__ == "__main__":
    asyncio.run(main()) 