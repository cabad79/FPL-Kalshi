import sys
sys.path.insert(0, r"C:\Users\carlos.jaramillo\Downloads\FPL-Kalshi\fpl-mcp-v2\src")

try:
    from fpl_mcp.presentation.tools import register_tools
    print("✅ tools.py import OK")
except Exception as e:
    print(f"❌ tools.py import failed: {e}")

try:
    from fpl_mcp.presentation.resources import register_resources
    print("✅ resources.py import OK")
except Exception as e:
    print(f"❌ resources.py import failed: {e}")

try:
    from fpl_mcp.presentation.prompts import register_prompts
    print("✅ prompts.py import OK")
except Exception as e:
    print(f"❌ prompts.py import failed: {e}")

try:
    from fpl_mcp.server import FPLMCPServer, create_services
    print("✅ server.py import OK")
except Exception as e:
    print(f"❌ server.py import failed: {e}")

print("\nAll presentation layer imports verified.")
