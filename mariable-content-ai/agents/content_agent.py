import json
import anthropic
from config import ANTHROPIC_API_KEY, MODEL, BRAND_CONTEXT


class ContentAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def write_post(self, idea: dict) -> dict:
        """
        Takes a content idea (from Notion or watch agent) and writes a full Instagram post.
        Returns a dict with hook, caption, hashtags, and format recommendations.
        """
        system_prompt = f"""{BRAND_CONTEXT}

Tu es un expert en copywriting Instagram pour la niche mariage en France.
Tu rédiges des posts qui convertissent : engagements, sauvegardes, partages.

Règles :
- Hook : 1 phrase choc qui stoppe le scroll (max 10 mots, commence par un chiffre ou une question)
- Caption : 150-250 mots, émotionnel + pratique, 1 CTA clair en fin
- Format Reel : ajoute un plan séquence en 5 étapes (0-3s / 3-8s / 8-15s / 15-25s / 25-30s)
- Hashtags : 15-20 hashtags mixés (grands #mariage, moyens #organisationmariage, petits #mariableapp)
- Ton : bienveillant, complice, jamais commercial
"""

        format_name = idea.get("format", "🎬 Reel")
        prompt = f"""Rédige un post Instagram complet pour Mariable basé sur cette idée :

Titre : {idea.get("titre", "")}
Hook suggéré : {idea.get("hook", "")}
Format : {format_name}
Analyse viralité : {idea.get("analyse", "")}
Score viralité : {idea.get("score", "")}/10

Réponds en JSON avec ces champs :
{{
  "hook": "...",
  "caption": "...",
  "hashtags": "...",
  "plan_sequence": ["...", "...", "...", "...", "..."],
  "cta": "...",
  "conseil_visuel": "..."
}}

Ne mets que le JSON, sans markdown autour."""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=2048,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )

        text = response.content[0].text.strip()
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            start = text.find("{")
            end = text.rfind("}") + 1
            if start != -1 and end > start:
                return json.loads(text[start:end])
            return {"hook": "", "caption": text, "hashtags": "", "plan_sequence": [], "cta": "", "conseil_visuel": ""}

    def adapt_for_story(self, post: dict) -> str:
        """Adapts an existing post into a 3-slide Story format."""
        prompt = f"""Adapte ce post Instagram en Story 3 slides pour Mariable.

Post original :
Hook : {post.get("hook")}
Caption : {post.get("caption")}

Génère 3 slides en JSON :
[
  {{"slide": 1, "texte": "...", "visuel": "..."}},
  {{"slide": 2, "texte": "...", "visuel": "..."}},
  {{"slide": 3, "texte": "...", "cta": "..."}}
]"""

        response = self.client.messages.create(
            model=MODEL,
            max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        return response.content[0].text

    def batch_write(self, ideas: list[dict]) -> list[dict]:
        """Write posts for multiple ideas using the Anthropic Batch API."""
        requests = [
            {
                "custom_id": f"idea_{i}_{idea.get('titre', '')[:20].replace(' ', '_')}",
                "params": {
                    "model": MODEL,
                    "max_tokens": 2048,
                    "messages": [{"role": "user", "content": self._build_prompt(idea)}],
                },
            }
            for i, idea in enumerate(ideas)
        ]

        batch = self.client.beta.messages.batches.create(requests=requests)
        print(f"Batch créé : {batch.id} — {len(requests)} posts en cours de génération")
        return [{"batch_id": batch.id, "ideas": ideas}]

    def _build_prompt(self, idea: dict) -> str:
        return f"""Rédige un post Instagram pour Mariable (mariage FR, couples 25-35 ans).
Idée : {idea.get("titre")} | Format : {idea.get("format")} | Hook : {idea.get("hook")}
Réponds en JSON : {{"hook":"...","caption":"...","hashtags":"...","cta":"..."}}"""
