"""Relie l'entrée agent newsletter-maree au déploiement vivant poc-newsletter.

L'entrée agent pointe encore vers le déploiement supprimé `newsletter-maree`
(worker actif: False). `register_agent` est un upsert idempotent sans
configuration : il met à jour la liaison agent → déploiement.

Usage (depuis la racine du projet) :
    uv run --env-file .env python rebind_agent.py
"""

import asyncio
import os

from mistralai.vibe_agents.agents_client import AgentsClient

AGENT_NAME = "newsletter-maree"
WORKFLOW_NAME = "newsletter-maree"
DEPLOYMENT_NAME = "poc-newsletter"
CONTROL_PLANE_URL = "https://api.mistral.ai/v2/agents"


async def main() -> None:
    async with AgentsClient(
        base_url=CONTROL_PLANE_URL, api_key=os.environ["MISTRAL_API_KEY"]
    ) as client:
        response = await client.register_agent(
            agent_name=AGENT_NAME,
            workflow_name=WORKFLOW_NAME,
            deployment_name=DEPLOYMENT_NAME,
        )
        print("✓ Agent réenregistré")
        print(f"  agent_id     : {response.agent_id}")
        print(f"  deployment   : {response.deployment_name}")
        print(f"  worker actif : {response.is_active}")
        print(f"  chat_url     : {response.chat_url}")


if __name__ == "__main__":
    asyncio.run(main())
