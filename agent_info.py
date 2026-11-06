"""Affiche l'entrée agent newsletter-maree : état du worker et lien Vibe (chat_url).

Usage (depuis la racine du projet) :
    uv run --env-file .env python agent_info.py
"""

import asyncio
import os

from mistralai.vibe_agents.agents_client import AgentsClient

AGENT_NAME = "newsletter-maree"
CONTROL_PLANE_URL = "https://api.mistral.ai/v2/agents"


async def main() -> None:
    async with AgentsClient(
        base_url=CONTROL_PLANE_URL, api_key=os.environ["MISTRAL_API_KEY"]
    ) as client:
        agent = await client.get_agent_by_name(AGENT_NAME)
        print(f"agent_id       : {agent.agent_id}")
        print(f"deployment     : {agent.deployment_name}")
        print(f"worker actif   : {agent.is_active}")
        print(f"rollout        : {agent.rollout_status}")
        print(f"build          : {agent.build_phase}")
        if agent.build_message:
            print(f"build message  : {agent.build_message}")
        print(f"chat_url       : {agent.chat_url}")
        print(f"console_url    : {agent.console_url}")


if __name__ == "__main__":
    asyncio.run(main())
