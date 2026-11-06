"""Déploiement via l'API Agents (crée l'entrée agent visible dans Vibe).

Réutilise la logique exacte de `agents deploy` (plan_deploy + create_deployment),
avec le seul contournement suivant : `revision` est laissée vide, car l'API
refuse actuellement `github_url` + `revision` ensemble (422 "Set exactly one source").

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_vibe.py
"""

import asyncio
from pathlib import Path

from mistralai.vibe_agents.sdk.app import deploy as deploy_module


async def main() -> None:
    plan = deploy_module.plan_deploy(Path("."))
    plan = plan.model_copy(update={"spec": plan.spec.model_copy(update={"revision": None})})
    print(f"Agent      : {plan.spec.agent_name}")
    print(f"Dépôt      : {plan.spec.github_url}")
    print(f"Hardened   : {plan.hardened}")
    print("Création de l'agent sur la plateforme gérée...")
    response = await deploy_module.create_deployment(plan)
    print("✓ Agent créé")
    print(f"  agent_id    : {response.agent_id}")
    print(f"  chat_url    : {response.chat_url}")
    print(f"  console_url : {response.console_url}")


if __name__ == "__main__":
    asyncio.run(main())
