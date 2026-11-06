"""Déploiement via l'API Agents (crée l'entrée agent visible dans Vibe).

Réutilise la logique exacte de `agents deploy` (plan_deploy + create_deployment),
avec le seul contournement suivant : `revision` est laissée vide, car l'API
refuse actuellement `github_url` + `revision` ensemble (422 "Set exactly one source").

Supprime d'abord le déploiement workflows du même nom s'il existe (créé manuellement,
il bloque la création de l'agent : 409 "already linked to a managed deployment").

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_vibe.py
"""

import asyncio
from pathlib import Path

import httpx
from mistralai.client import Mistral
from mistralai.vibe_agents.sdk.app import deploy as deploy_module

DEPLOYMENT_NAME = "newsletter-maree"


async def delete_existing_deployment() -> None:
    client = Mistral(api_key=_api_key())
    try:
        client.workflows.deployments.delete_deployment(name=DEPLOYMENT_NAME)
        print(f"Déploiement existant '{DEPLOYMENT_NAME}' supprimé.")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            print(f"Aucun déploiement existant '{DEPLOYMENT_NAME}' à supprimer.")
        else:
            raise
    except Exception as exc:  # noqa: BLE001
        if "404" in str(exc) or "not found" in str(exc).lower():
            print(f"Aucun déploiement existant '{DEPLOYMENT_NAME}' à supprimer.")
        else:
            raise


def _api_key() -> str:
    import os

    return os.environ["MISTRAL_API_KEY"]


async def main() -> None:
    await delete_existing_deployment()
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
