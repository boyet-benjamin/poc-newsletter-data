import os
from pathlib import Path
from typing import Annotated

import httpx
from pydantic import Field

from mistralai import agents

MAREE_API_BASE_URL = "https://api-maree.fr"
DEFAULT_MAREE_SITE = "port-en-bessin"
DEFAULT_MAREE_API_KEY = "0" * 32
NEWSLETTER_RECIPIENT = "benjamin.boyet@arkea.com"
TEMPLATE_PATH = Path(__file__).resolve().parent / "template.html"


@agents.tool
async def fetch_maree_data(
    site: Annotated[str, Field(description="Identifiant du site api-maree.fr, ex. 'port-en-bessin', 'brest', 'saint-malo'. Par défaut : port-en-bessin.")] = DEFAULT_MAREE_SITE,
    day: Annotated[str, Field(description="Date des données au format YYYY-MM-DD. Laisser vide pour aujourd'hui.")] = "",
) -> dict:
    """Récupère les horaires de marée du jour (basses mers, pleines mers, coefficients, hauteurs d'eau) depuis api-maree.fr."""
    api_key = os.environ.get("MAREE_API_KEY") or DEFAULT_MAREE_API_KEY
    target_day = day or agents.now().date().isoformat()
    params = {
        "site": site,
        "from": target_day,
        "to": target_day,
        "tz": "Europe/Paris",
        "key": api_key,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{MAREE_API_BASE_URL}/tide-extrema", params=params)
    if response.status_code != 200:
        raise agents.ToolError(
            f"api-maree.fr a répondu {response.status_code} pour le site '{site}' : {response.text[:200]}"
        )
    payload = response.json()
    if payload.get("error"):
        raise agents.ToolError(f"api-maree.fr a refusé la requête : {payload['error']}")
    return payload


@agents.tool
async def render_newsletter(
    date_text: Annotated[str, Field(description="Date lisible à afficher en en-tête, ex. 'vendredi 6 novembre 2026'.")],
    site_name: Annotated[str, Field(description="Nom lisible du site de marée, ex. 'Port-en-Bessin'.")],
    intro: Annotated[str, Field(description="Texte d'introduction adapté aux données du jour. HTML simple autorisé (<strong>, <em>).")],
    marees_html: Annotated[str, Field(description="Tableau HTML <table> des horaires de marée du jour, avec type (basse/pleine mer), heure, hauteur et coefficient.")],
    conseil: Annotated[str, Field(description="Conseil du jour adapté aux données du jour (marées, coefficients). Texte simple, pas de HTML de structure.")],
) -> dict:
    """Remplit le template prédéfini de la newsletter en remplaçant uniquement les zones de texte délimitées, sans jamais modifier la structure du template."""
    template = TEMPLATE_PATH.read_text(encoding="utf-8")
    values = {
        "DATE": date_text,
        "SITE_NAME": site_name,
        "INTRO": intro,
        "MAREES": marees_html,
        "CONSEIL": conseil,
    }
    html = template
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", value)
    if "{{" in html:
        leftover = html[html.index("{{") : html.index("{{") + 30]
        raise agents.ToolError(f"Zone de texte non remplie dans le template : {leftover}")
    return {"html": html, "recipient": NEWSLETTER_RECIPIENT}


agent = agents.Agent(
    model="mistral-large-4",
    name="newsletter-maree",
    instructions=f"""Tu es un agent de newsletter marine, en français.

Ton workflow, à chaque demande de préparation ou d'envoi de la newsletter :

1. Appelle `fetch_maree_data` pour récupérer les données de marée du jour (site par défaut : {DEFAULT_MAREE_SITE}, sauf si l'utilisateur précise un autre site api-maree.fr).
2. À partir des données, rédige les textes adaptés : une introduction qui résume la marée du jour, un tableau HTML des horaires (basse mer / pleine mer, heure, hauteur en m, coefficient), et un conseil du jour pertinent selon les coefficients (ex. grandes marées = pêche à pied, coefficient faible = navigation).
3. Appelle `render_newsletter` avec ces textes. Le template est prédéfini : ne modifie JAMAIS sa structure, seules les zones de texte sont remplies par l'outil.
4. Présente à l'utilisateur : l'objet proposé de l'email, le destinataire ({NEWSLETTER_RECIPIENT}), le contenu textuel de la newsletter (texte du template rempli), puis demande explicitement : « Validez-vous l'envoi de cette newsletter ? »
5. Attends la validation explicite de l'utilisateur (oui, validé, envoie). S'il refuse ou demande des modifications, ajuste les textes (jamais le template) et représente la version corrigée.
6. Seulement après validation explicite, envoie la newsletter avec l'outil Gmail (`gmail_send_email`) : destinataire {NEWSLETTER_RECIPIENT}, objet « Newsletter marée — <site> — <date> », le HTML rendu comme corps du message.
7. Confirme l'envoi avec l'identifiant du message.

Règles absolues :
- N'envoie JAMAIS d'email sans validation explicite de l'utilisateur dans la conversation.
- Ne modifie JAMAIS la structure, le style ou la mise en page du template.
- Réponds toujours en français.""",
    tools=[fetch_maree_data, render_newsletter],
    connectors=[agents.connector("gmail")],
)
