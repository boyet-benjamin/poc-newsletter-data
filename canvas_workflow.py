"""Workflow conversationnel newsletter-canvas.

Affiche le rendu visuel exact de la newsletter dans un canvas Vibe (text/html),
laisse l'utilisateur le modifier, attend sa validation, puis envoie l'email
via le connecteur Gmail au nom de l'utilisateur qui déclenche le workflow (OBO).
"""

import json
from datetime import timedelta

import mistralai.workflows as workflows
import mistralai.workflows.plugins.mistralai as workflows_mistralai
from mistralai.workflows import Depends
from mistralai.workflows.conversational import CanvasInput
from mistralai.workflows.plugins.mistralai import Agent, Runner
from mistralai.workflows.plugins.mistralai.connectors import (
    ToolCallClient,
    connector,
    uses_connectors,
)

MAREE_API_BASE_URL = "https://api-maree.fr"
DEFAULT_MAREE_SITE = "port-en-bessin"
DEFAULT_MAREE_API_KEY = "0" * 32
NEWSLETTER_RECIPIENT = "benjamin.boyet@arkea.com"

gmail_connector = connector("gmail")


@workflows.activity(name="fetch-maree-data", start_to_close_timeout=timedelta(seconds=60))
async def fetch_maree_data(site: str) -> dict:
    """Récupère les extrema de marée du jour sur api-maree.fr."""
    import os
    from datetime import datetime, timezone

    import httpx

    api_key = os.environ.get("MAREE_API_KEY") or DEFAULT_MAREE_API_KEY
    day = datetime.now(timezone.utc).date().isoformat()
    params = {
        "site": site,
        "from": day,
        "to": day,
        "tz": "Europe/Paris",
        "key": api_key,
    }
    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.get(f"{MAREE_API_BASE_URL}/tide-extrema", params=params)
    response.raise_for_status()
    payload = response.json()
    if payload.get("error"):
        raise RuntimeError(f"api-maree.fr : {payload['error']}")
    return payload


@workflows.activity(name="write-sections", start_to_close_timeout=timedelta(seconds=180))
async def write_sections(data: dict) -> dict:
    """Rédige l'intro et le conseil du jour adaptés aux marées, via un agent durable."""
    day = data["data"][0]
    extrema = day["extrema"]
    lines = []
    for extremum in extrema:
        label = "Pleine mer" if extremum["type"] == "PM" else "Basse mer"
        coef = f" coef. {extremum['coef']}" if "coef" in extremum else ""
        lines.append(
            f"- {label} {extremum['time']} {extremum['height']:.2f} m{coef}"
        )
    tide_summary = "\n".join(lines)
    prompt = (
        f"Site : {data['site_name']}. Date : {day['date']}.\n"
        f"Marées du jour :\n{tide_summary}\n\n"
        "Rédige une introduction (2 phrases) et un conseil du jour (2-3 phrases) "
        "pour une newsletter marine en français, adaptés à ces marées et coefficients. "
        'Réponds STRICTEMENT en JSON : {"intro": "...", "conseil": "..."}'
    )
    agent = Agent(
        name="newsletter-writer",
        model="mistral-large-4",
        instructions=(
            "Tu rédiges des textes courts de newsletter marine en français. "
            "Tu réponds uniquement par un objet JSON valide avec les clés demandées, "
            "sans balise de code ni texte autour."
        ),
    )
    chunks = await Runner.run(agent=agent, inputs=prompt)
    raw = "".join(chunk.text for chunk in chunks if getattr(chunk, "text", None))
    try:
        return json.loads(raw)
    except (ValueError, TypeError):
        return {
            "intro": f"Voici les horaires de marée du jour à {data['site_name']}.",
            "conseil": "Vérifiez les coefficients avant vos activités cotières.",
        }


@workflows.activity(name="render-newsletter", start_to_close_timeout=timedelta(seconds=30))
async def render_newsletter(data: dict, sections: dict) -> dict:
    """Remplit le template prédéfini, en remplaçant uniquement les zones de texte."""
    day = data["data"][0]
    rows = []
    for extremum in day["extrema"]:
        label = "Pleine mer" if extremum["type"] == "PM" else "Basse mer"
        coef = f"<td>{extremum['coef']}</td>" if "coef" in extremum else "<td>—</td>"
        rows.append(
            "<tr>"
            f"<td style='padding:8px;border-bottom:1px solid #e3ecf2;'>{label}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e3ecf2;'>{extremum['time']}</td>"
            f"<td style='padding:8px;border-bottom:1px solid #e3ecf2;'>{extremum['height']:.2f} m</td>"
            f"{coef}"
            "</tr>"
        )
    from pathlib import Path

    template_path = Path(__file__).resolve().parent / "template.html"
    template = template_path.read_text(encoding="utf-8")
    marees_html = (
        "<table style='width:100%;border-collapse:collapse;font-size:14px;'>"
        "<tr><th style='text-align:left;padding:8px;'>Type</th>"
        "<th style='text-align:left;padding:8px;'>Heure</th>"
        "<th style='text-align:left;padding:8px;'>Hauteur</th>"
        "<th style='text-align:left;padding:8px;'>Coefficient</th></tr>"
        + "".join(rows)
        + "</table>"
    )
    values = {
        "DATE": day["date"],
        "SITE_NAME": data["site_name"],
        "INTRO": sections["intro"],
        "MAREES": marees_html,
        "CONSEIL": sections["conseil"],
    }
    html = template
    for key, value in values.items():
        html = html.replace("{{" + key + "}}", value)
    if "{{" in html:
        raise RuntimeError("Zone de texte non remplie dans le template")
    return {"html": html, "subject": f"Newsletter marée — {data['site_name']} — {day['date']}"}


@workflows.activity(name="send-newsletter", start_to_close_timeout=timedelta(seconds=60))
async def send_newsletter(
    to: str,
    subject: str,
    html_body: str,
    gmail: ToolCallClient = Depends(gmail_connector),
) -> str:
    """Envoie la newsletter via le connecteur Gmail (identité de l'utilisateur)."""
    result = await gmail.call_tool(
        tool_name="send_email",
        arguments={"to": [to], "subject": subject, "htmlBody": html_body},
    )
    return str(result)


@workflows.workflow.define(
    name="newsletter-canvas",
    workflow_display_name="Newsletter Marée",
    workflow_description=(
        "Prépare la newsletter marée du jour (api-maree.fr), l'affiche en rendu "
        "visuel dans un canvas, attend la validation, puis l'envoie par Gmail."
    ),
    on_behalf_of=True,
)
@uses_connectors(gmail_connector)
class NewsletterCanvasWorkflow(workflows.InteractiveWorkflow):
    @workflows.workflow.entrypoint
    async def run(
        self, site: str = DEFAULT_MAREE_SITE
    ) -> workflows_mistralai.ChatAssistantWorkflowOutput:
        data = await fetch_maree_data(site)
        sections = await write_sections(data)
        newsletter = await render_newsletter(data, sections)
        title = f"Newsletter — {data['site_name']} — {data['data'][0]['date']}"

        canvas_resource = workflows_mistralai.CanvasResource(
            canvas=workflows_mistralai.CanvasPayload(
                type="text/html",
                title=title,
                content=newsletter["html"],
            )
        )
        await workflows_mistralai.send_assistant_message(
            "Voici le rendu visuel de la newsletter du jour. "
            "Vous pouvez le modifier directement dans le canvas.",
            canvas=canvas_resource,
        )

        edited = await self.wait_for_input(
            CanvasInput(
                canvas_uri=canvas_resource.uri,
                prompt=(
                    "Modifiez le rendu si besoin, puis écrivez « envoie » pour "
                    "expédier à " + NEWSLETTER_RECIPIENT + " (ou « annule »)."
                ),
            ),
            label="Validation de la newsletter",
        )

        final_html = edited.canvas.content
        message = (edited.chatInput or "").strip().lower()
        final_resource = workflows_mistralai.CanvasResource(
            canvas=workflows_mistralai.CanvasPayload(
                type="text/html", title=title, content=final_html
            )
        )

        if not message or message.startswith("annul"):
            return workflows_mistralai.ChatAssistantWorkflowOutput(
                content=[
                    workflows_mistralai.TextOutput(text="Envoi annulé — rien n'a été envoyé."),
                    workflows_mistralai.ResourceOutput(resource=final_resource),
                ]
            )

        confirmation = await send_newsletter(
            to=NEWSLETTER_RECIPIENT,
            subject=newsletter["subject"],
            html_body=final_html,
        )
        return workflows_mistralai.ChatAssistantWorkflowOutput(
            content=[
                workflows_mistralai.TextOutput(
                    text=f"Newsletter envoyée à {NEWSLETTER_RECIPIENT}. {confirmation}"
                ),
                workflows_mistralai.ResourceOutput(resource=final_resource),
            ]
        )
