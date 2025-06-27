#!/usr/bin/env python3
"""
Google Search Agent Setup Test

This script helps verify that your Google Search Agent is configured correctly
by testing API connections and basic functionality.
"""

import os
import sys
from typing import Dict, Any
import asyncio

def test_environment_variables() -> Dict[str, Any]:
    """Test that required environment variables are set."""
    print("🔍 Testing environment variables...")
    
    required_vars = [
        "GOOGLE_API_KEY",
        "GOOGLE_SEARCH_API_KEY", 
        "GOOGLE_SEARCH_ENGINE_ID"
    ]
    
    optional_vars = [
        "GOOGLE_GENAI_USE_VERTEXAI",
        "GOOGLE_CLOUD_PROJECT",
        "GOOGLE_CLOUD_LOCATION"
    ]
    
    results = {"status": "success", "issues": []}
    
    # Check required variables
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            results["issues"].append(f"❌ Missing required environment variable: {var}")
            results["status"] = "error"
        elif value.startswith("your_") or "example" in value.lower():
            results["issues"].append(f"⚠️  Environment variable {var} appears to be a placeholder")
            results["status"] = "warning"
        else:
            print(f"✅ {var}: configured")
    
    # Check optional variables
    vertex_ai_mode = os.getenv("GOOGLE_GENAI_USE_VERTEXAI", "FALSE").upper() == "TRUE"
    if vertex_ai_mode:
        print("📍 Using Vertex AI mode")
        for var in ["GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_LOCATION"]:
            value = os.getenv(var)
            if not value:
                results["issues"].append(f"❌ Missing Vertex AI variable: {var}")
                results["status"] = "error"
            else:
                print(f"✅ {var}: configured")
    else:
        print("📍 Using Google AI Studio mode")
    
    return results

def test_adk_installation() -> Dict[str, Any]:
    """Test that ADK is properly installed."""
    print("\n🔧 Testing ADK installation...")
    
    try:
        import google.adk
        from google.adk.agents import LlmAgent
        from google.adk.tools import GoogleSearchTool
        print("✅ ADK successfully imported")
        return {"status": "success"}
    except ImportError as e:
        return {
            "status": "error", 
            "error": f"ADK import failed: {e}",
            "suggestion": "Install ADK with: pip install google-adk"
        }

def test_agent_creation() -> Dict[str, Any]:
    """Test that the search agent can be created."""
    print("\n🤖 Testing agent creation...")
    
    try:
        # Import the agent
        sys.path.insert(0, os.path.dirname(__file__))
        from search_agent.agent import root_agent
        
        if root_agent.name == "GoogleSearchAgent":
            print("✅ Agent created successfully")
            print(f"   Agent name: {root_agent.name}")
            print(f"   Model: {root_agent.model}")
            print(f"   Tools: {len(root_agent.tools)} tools configured")
            return {"status": "success"}
        else:
            return {
                "status": "error",
                "error": "Agent created but with unexpected configuration"
            }
    except Exception as e:
        return {
            "status": "error",
            "error": f"Agent creation failed: {e}",
            "suggestion": "Check search_agent/agent.py for syntax errors"
        }

def test_google_search_api() -> Dict[str, Any]:
    """Test Google Custom Search API connectivity."""
    print("\n🔍 Testing Google Search API connectivity...")
    
    api_key = os.getenv("GOOGLE_SEARCH_API_KEY")
    engine_id = os.getenv("GOOGLE_SEARCH_ENGINE_ID")
    
    if not api_key or not engine_id:
        return {
            "status": "error",
            "error": "Google Search API credentials not configured"
        }
    
    try:
        import requests
        
        # Test basic API connectivity
        url = "https://www.googleapis.com/customsearch/v1"
        params = {
            "key": api_key,
            "cx": engine_id,
            "q": "test query",
            "num": 1
        }
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                print("✅ Google Search API working correctly")
                print(f"   Found {len(data['items'])} results for test query")
                return {"status": "success"}
            else:
                return {
                    "status": "warning",
                    "message": "API responded but no search results found"
                }
        elif response.status_code == 403:
            return {
                "status": "error", 
                "error": "API key invalid or quota exceeded",
                "suggestion": "Check your API key and usage quota"
            }
        elif response.status_code == 400:
            return {
                "status": "error",
                "error": "Bad request - check your Search Engine ID",
                "suggestion": "Verify your Custom Search Engine ID is correct"
            }
        else:
            return {
                "status": "error",
                "error": f"API request failed with status {response.status_code}"
            }
    except requests.RequestException as e:
        return {
            "status": "error",
            "error": f"Network error: {e}",
            "suggestion": "Check your internet connection"
        }
    except ImportError:
        return {
            "status": "error",
            "error": "requests library not available",
            "suggestion": "Install requests with: pip install requests"
        }

async def test_agent_runner() -> Dict[str, Any]:
    """Test that the agent can run with ADK Runner."""
    print("\n🏃 Testing agent runner...")
    
    try:
        from google.adk.runner import Runner
        from google.adk.sessions import InMemorySessionService
        
        # Import the agent
        sys.path.insert(0, os.path.dirname(__file__))
        from search_agent.agent import root_agent
        
        session_service = InMemorySessionService()
        runner = Runner(
            agent=root_agent,
            app_name="test_search_agent",
            session_service=session_service
        )
        
        print("✅ Runner created successfully")
        print("   Ready to process search requests")
        return {"status": "success"}
        
    except Exception as e:
        return {
            "status": "error",
            "error": f"Runner setup failed: {e}",
            "suggestion": "Check ADK installation and agent configuration"
        }

def print_summary(results: list) -> None:
    """Print a summary of all test results."""
    print("\n" + "="*50)
    print("🎯 SETUP TEST SUMMARY")
    print("="*50)
    
    success_count = sum(1 for r in results if r.get("status") == "success")
    warning_count = sum(1 for r in results if r.get("status") == "warning") 
    error_count = sum(1 for r in results if r.get("status") == "error")
    
    print(f"✅ Successful tests: {success_count}")
    print(f"⚠️  Warnings: {warning_count}")
    print(f"❌ Errors: {error_count}")
    
    if error_count == 0 and warning_count == 0:
        print("\n🎉 Perfect! Your Google Search Agent is ready to use!")
        print("\nNext steps:")
        print("1. Run: adk web")
        print("2. Open: http://localhost:8000")
        print("3. Try searching for something!")
    elif error_count == 0:
        print("\n✅ Your setup looks good with minor warnings.")
        print("You should be able to run the agent, but consider addressing the warnings.")
    else:
        print("\n❌ Setup incomplete. Please fix the errors above before running the agent.")
        print("\nCommon fixes:")
        print("1. Copy env.example to .env and fill in your API keys")
        print("2. Install ADK: pip install google-adk")
        print("3. Set up Google Custom Search Engine")
        print("4. Enable Custom Search JSON API in Google Cloud Console")

def main():
    """Run all setup tests."""
    print("🔬 Google Search Agent Setup Test")
    print("="*50)
    
    # Load environment from .env file if available
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("📁 Loaded .env file")
    except ImportError:
        print("💡 Tip: Install python-dotenv for automatic .env loading")
        print("   pip install python-dotenv")
    
    # Run all tests
    tests = [
        ("Environment Variables", test_environment_variables),
        ("ADK Installation", test_adk_installation), 
        ("Agent Creation", test_agent_creation),
        ("Google Search API", test_google_search_api),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            result["test_name"] = test_name
            results.append(result)
            
            # Print any issues or suggestions
            if "issues" in result:
                for issue in result["issues"]:
                    print(f"   {issue}")
            if "error" in result:
                print(f"   ❌ {result['error']}")
            if "suggestion" in result:
                print(f"   💡 {result['suggestion']}")
                
        except Exception as e:
            print(f"   ❌ Test failed with exception: {e}")
            results.append({
                "test_name": test_name,
                "status": "error", 
                "error": str(e)
            })
    
    # Test runner (async)
    try:
        result = asyncio.run(test_agent_runner())
        result["test_name"] = "Agent Runner"
        results.append(result)
        
        if "error" in result:
            print(f"   ❌ {result['error']}")
        if "suggestion" in result:
            print(f"   💡 {result['suggestion']}")
    except Exception as e:
        print(f"   ❌ Runner test failed: {e}")
        results.append({
            "test_name": "Agent Runner",
            "status": "error",
            "error": str(e)
        })
    
    # Print summary
    print_summary(results)

if __name__ == "__main__":
    main() 