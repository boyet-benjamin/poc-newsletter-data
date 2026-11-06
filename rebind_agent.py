"""Répare l'entrée agent newsletter-maree : supprime l'entrée morte, puis la
réenregistre liée au déploiement vivant poc-newsletter.

L'entrée agent pointe vers le déploiement supprimé `newsletter-maree` et le
registre refuse le changement de liaison (409). La séquence est :
1. suppression de l'entrée morte (le déploiement vivant n'est pas touché) ;
2. réenregistrement immédiat lié à `poc-newsletter`.

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
        old = await client.get_agent_by_name(AGENT_NAME)
        print(f"Entrée actuelle : deployment={old.deployment_name}, active={old.is_active}")
        if old.deployment_name == DEPLOYMENT_NAME and old.is_active:
            print("Déjà liée au bon déploiement actif — rien à faire.")
            return
        print("Suppression de l'entrée morte...")
        await client.shutdown_agent(old.agent_id)
        print("Réenregistrement lié à " + DEPLOYMENT_NAME + "...")
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
