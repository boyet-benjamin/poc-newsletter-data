"""Déploiement du workflow newsletter-canvas (déploiement géré, hardened).

Supprime d'abord un déploiement existant du même nom (état d'échec ou ancien),
puis le recrée sur la branche main. Contournement du bug API : github_url seul,
sans revision.

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_canvas.py
"""

import json
import os

import httpx
from mistralai.client import Mistral

API_URL = "https://api.mistral.ai/v1/workflows/deployments"
DEPLOYMENT_NAME = "newsletter-canvas"
REPO = "https://github.com/boyet-benjamin/poc-newsletter-data"


def delete_existing() -> None:
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    try:
        client.workflows.deployments.delete_deployment(name=DEPLOYMENT_NAME)
        print(f"Déploiement existant '{DEPLOYMENT_NAME}' supprimé.")
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code == 404:
            print(f"Aucun déploiement existant '{DEPLOYMENT_NAME}'.")
        else:
            raise


def create() -> None:
    payload = {
        "name": DEPLOYMENT_NAME,
        "hardened": True,
        "spec": {
            "github_url": REPO,
            "backend_spec": {
                "type": "mistral_cloud",
                "build_directory": ".",
                "dockerfile_path": "Dockerfile.canvas",
            },
        },
    }
    headers = {
        "Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    response = httpx.post(API_URL, headers=headers, json=payload, timeout=120)
    print(f"HTTP {response.status_code}")
    if response.status_code in (200, 201, 202):
        print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:1500])
    else:
        print(response.text[:500])


if __name__ == "__main__":
    delete_existing()
    create()
