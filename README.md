# newsletter-maree

Agent de newsletter construit avec le [Mistral Agents SDK](https://docs.mistral.ai/studio/agents/agents-sdk).

À chaque lancement, l'agent :

1. récupère les données de marée du jour sur [api-maree.fr](https://api-maree.fr) (site par défaut : Port-en-Bessin) ;
2. remplit le template prédéfini `template.html` en adaptant uniquement les zones de texte (intro, horaires, conseil) — la structure du template n'est jamais modifiée ;
3. présente la newsletter à l'utilisateur et attend sa validation explicite ;
4. après validation, envoie la newsletter par Gmail via le connecteur Mistral.

## Configuration

| Variable d'environnement | Rôle | Défaut |
| --- | --- | --- |
| `MAREE_API_KEY` | Clé API api-maree.fr | Clé de démonstration des docs (32 zéros) |
| `MISTRAL_API_KEY` | Clé Mistral (exécution locale uniquement) | — |

Destinataire fixe : `benjamin.boyet@arkea.com` (constante `NEWSLETTER_RECIPIENT` dans `main.py`).

## Exécuter en local

```bash
uv run --env-file .env agents chat
```

## Déployer (déploiement géré Mistral)

```bash
git add --all && git commit -m "..." && git push
uv run --env-file .env agents deploy
```

## Discuter avec l'agent déployé

```bash
uv run --env-file .env agents chat newsletter-maree
```
