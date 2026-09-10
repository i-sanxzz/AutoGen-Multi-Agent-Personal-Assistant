import asyncio
import os
import sys
from dotenv import load_dotenv
from autogen_agentchat.agents import AssistantAgent
from src.client import get_model_client


async def run_smoke_test():
    """Milestone 1: Verify AutoGen environment and model client connectivity."""
    load_dotenv()

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("\n" + "=" * 60)
        print(" [!] Missing API Key Configuration")
        print("=" * 60)
        print("To run the smoke test, configure your API key in a .env file:")
        print("  1. cp .env.example .env")
        print("  2. Edit .env to set OPENAI_API_KEY (and optionally OPENAI_BASE_URL)")
        print("=" * 60 + "\n")
        sys.exit(1)

    try:
        model_client = get_model_client()
    except Exception as e:
        print(f"\n[X] Error creating model client: {e}\n")
        sys.exit(1)

    model_name = os.getenv("OPENAI_MODEL", "default")
    base_url = os.getenv("OPENAI_BASE_URL", "default OpenAI endpoint")
    max_tokens = os.getenv("OPENAI_MAX_TOKENS", "1000")
    print(f"[*] Initializing model client:")
    print(f"    - Model:      {model_name}")
    print(f"    - Endpoint:   {base_url}")
    print(f"    - Max Tokens: {max_tokens}")


    print("[*] Creating test AssistantAgent ('test_assistant')...")
    agent = AssistantAgent(
        name="test_assistant",
        model_client=model_client,
        system_message="You are a helpful AI assistant. Always be concise and direct."
    )

    prompt = "Say hello and confirm you are running."
    print(f"[*] Sending prompt to agent: \"{prompt}\"")
    
    try:
        response = await agent.run(task=prompt)
        print("\n" + "=" * 60)
        print(" [✓] Milestone 1 Smoke Test Successful!")
        print("=" * 60)
        for msg in response.messages:
            if hasattr(msg, "source") and hasattr(msg, "content"):
                print(f"[{msg.source}]: {msg.content}")
        print("=" * 60 + "\n")
    except Exception as e:
        print("\n" + "=" * 60)
        print(f" [X] Error running agent: {e}")
        print("=" * 60 + "\n")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(run_smoke_test())
