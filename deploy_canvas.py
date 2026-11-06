"""Déploiement du workflow newsletter-canvas (déploiement géré, hardened).

Contournement du bug API : github_url seul, sans revision (voir deploy_manual.py).

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_canvas.py
"""

import json
import os

import httpx

API_URL = "https://api.mistral.ai/v1/workflows/deployments"
DEPLOYMENT_NAME = "newsletter-canvas"
REPO = "https://github.com/boyet-benjamin/poc-newsletter-data"


def main() -> None:
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
        print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:2000])
    else:
        print(response.text[:500])


if __name__ == "__main__":
    main()
