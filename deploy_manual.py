"""Déploiement direct via l'API Workflows (contournement du bug de champ).

Le client Python (mistralai 3.7.0) envoie `github_url`, mais l'API attend désormais
`repository_url`. Ce script appelle l'endpoint directement avec le bon payload.

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_manual.py
"""

import json
import os

import httpx

API_URL = "https://api.mistral.ai/v1/workflows/deployments"
DEPLOYMENT_NAME = "newsletter-maree"
REPOSITORY_URL = "https://github.com/boyet-benjamin/poc-newsletter-data"

CANDIDATES = [
    {
        "name": DEPLOYMENT_NAME,
        "hardened": True,
        "spec": {
            "workflows_worker": {
                "repository_url": REPOSITORY_URL,
                "revision": "main",
                "backend_spec": {
                    "type": "mistral_cloud",
                    "build_directory": ".",
                    "dockerfile_path": "Dockerfile",
                },
            }
        },
    },
    {
        "name": DEPLOYMENT_NAME,
        "hardened": True,
        "spec": {
            "repository_url": REPOSITORY_URL,
            "revision": "main",
            "backend_spec": {
                "type": "mistral_cloud",
                "build_directory": ".",
                "dockerfile_path": "Dockerfile",
            },
        },
    },
    {
        "name": DEPLOYMENT_NAME,
        "hardened": True,
        "spec": {
            "workflows_worker": {
                "repository_url": REPOSITORY_URL,
                "backend_spec": {
                    "type": "mistral_cloud",
                    "build_directory": ".",
                    "dockerfile_path": "Dockerfile",
                },
            }
        },
    },
]


def main() -> None:
    api_key = os.environ["MISTRAL_API_KEY"]
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    for index, payload in enumerate(CANDIDATES, start=1):
        print(f"Essai {index}/{len(CANDIDATES)}...")
        response = httpx.post(API_URL, headers=headers, json=payload, timeout=120)
        print(f"  HTTP {response.status_code}")
        if response.status_code in (200, 201, 202):
            print("  Déploiement accepté :")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:2000])
            return
        print("  " + response.text[:500])
    print("Échec de tous les essais — collez la sortie complète dans le chat.")


if __name__ == "__main__":
    main()
