"""Sonde de déploiement : teste les formes de payload acceptées par l'API.

L'API actuelle a un décalage de schéma : le niveau externe `spec` parle de
`repository_url`, le niveau interne `spec.workflows_worker` réclame `github_url`,
et `revision` semble compté comme une seconde source. Ce script essaie les
formes candidates et s'arrête à la première acceptée.

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_manual.py
"""

import json
import os

import httpx

API_URL = "https://api.mistral.ai/v1/workflows/deployments"
DEPLOYMENT_NAME = "newsletter-maree"
REPO = "https://github.com/boyet-benjamin/poc-newsletter-data"

BACKEND = {"type": "koyeb", "build_directory": ".", "dockerfile_path": "Dockerfile"}

CANDIDATES = [
    ("github_url seul (plat)", {"github_url": REPO, "backend_spec": BACKEND}),
    ("github_url + revision (plat)", {"github_url": REPO, "revision": "main", "backend_spec": BACKEND}),
    ("repository_url + revision (plat)", {"repository_url": REPO, "revision": "main", "backend_spec": BACKEND}),
    ("nested workflows_worker github_url seul", {"workflows_worker": {"github_url": REPO, "backend_spec": BACKEND}}),
    ("nested workflows_worker github_url + revision", {"workflows_worker": {"github_url": REPO, "revision": "main", "backend_spec": BACKEND}}),
]


def main() -> None:
    headers = {
        "Authorization": f"Bearer {os.environ['MISTRAL_API_KEY']}",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    for label, spec in CANDIDATES:
        payload = {"name": DEPLOYMENT_NAME, "hardened": True, "spec": spec}
        print(f"Essai : {label}")
        response = httpx.post(API_URL, headers=headers, json=payload, timeout=120)
        print(f"  HTTP {response.status_code}")
        if response.status_code in (200, 201, 202):
            print("  ✓ Déploiement accepté :")
            print(json.dumps(response.json(), indent=2, ensure_ascii=False)[:2000])
            return
        print("  " + response.text[:400].replace("\n", " "))
    print("Échec de tous les essais — collez la sortie complète dans le chat.")


if __name__ == "__main__":
    main()
