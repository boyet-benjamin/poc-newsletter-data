"""Contournement du bug de l'API de déploiement (422 "Set exactly one source").

L'endpoint refuse actuellement tout payload contenant `github_url` ET `revision`
ensemble. Ce script crée donc le déploiement avec `github_url` seul : Mistral Cloud
construit la branche par défaut du dépôt (`main`).

Usage (depuis la racine du projet) :
    uv run --env-file .env python deploy_manual.py
"""

import os

from mistralai.client import Mistral

DEPLOYMENT_NAME = "newsletter-maree"
GITHUB_URL = "https://github.com/boyet-benjamin/poc-newsletter-data"


def main() -> None:
    client = Mistral(api_key=os.environ["MISTRAL_API_KEY"])
    deployment = client.workflows.deployments.create_deployment(
        name=DEPLOYMENT_NAME,
        spec={
            "github_url": GITHUB_URL,
            "backend_spec": {
                "type": "mistral_cloud",
                "build_directory": ".",
                "dockerfile_path": "Dockerfile",
            },
        },
        hardened=True,
    )
    print(f"Déploiement créé : {deployment.name}")
    print(f"État : {getattr(deployment, 'phase', '?')}")


if __name__ == "__main__":
    main()
