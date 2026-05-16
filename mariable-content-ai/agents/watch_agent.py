import json
import anthropic
from duckduckgo_search import DDGS
from config import ANTHROPIC_API_KEY, MODEL, BRAND_CONTEXT

SEARCH_QUERIES = [
    "mariage tendance TikTok Instagram 2025 2026",
    "wedding reels viral TikTok ideas",
    "organisation mariage conseils viral instagram",
    "fiançailles mariage contenu viral france",
    "wedding planning tips viral video ideas",
]

TOOLS = [
    {
        "name": "web_search",
        "description": "Recherche du contenu viral sur le web (TikTok, Instagram, blogs mariage).",
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Requête de recherche"},
                "max_results": {"type": "integer", "default": 5},
            },
            "required": ["query"],
        },
    }
]


def _run_web_search(query: str, max_results: int = 5) -> str:
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return json.dumps(results, ensure_ascii=False)
    except Exception as e:
        return json.dumps({"error": str(e)})


def _process_tool_call(tool_name: str, tool_input: dict) -> str:
    if tool_name == "web_search":
        return _run_web_search(tool_input["query"], tool_input.get("max_results", 5))
    return ""


class WatchAgent:
    def __init__(self):
        self.client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

    def run(self, nb_ideas: int = 5) -> list[dict]:
        """
        Run the watch agent. Returns a list of viral content ideas with virality scores.
        Uses an agentic loop: Claude searches the web, analyzes results, scores and structures ideas.
        """
        system_prompt = f"""{BRAND_CONTEXT}

Tu es un agent de veille spécialisé dans le contenu viral mariage sur TikTok et Instagram.
Ta mission :
1. Rechercher les tendances virales actuelles dans la niche mariage/wedding
2. Analyser ce qui fonctionne (format, hook, durée, angle)
3. Scorer chaque tendance /10 selon ces critères :
   - Croissance des vues (vitesse) : 30%
   - Engagement rate (likes/vues estimé) : 25%
   - Duplication du format (combien le copient) : 20%
   - Pertinence pour mariable.fr (couples FR, 25-35 ans) : 15%
   - Fraîcheur (< 72h = bonus) : 10%
4. Générer {nb_ideas} idées de posts Instagram adaptées à Mariable

Pour chaque idée, fournis un JSON avec ces champs :
- titre : titre court de l'idée (max 60 chars)
- hook : phrase d'accroche percutante pour le post
- format : "🎬 Reel" | "🖼️ Carrousel" | "📸 Post photo" | "📱 Story"
- score_viralite : score /10 (float)
- analyse : 2-3 phrases sur pourquoi ça marche et comment l'adapter à Mariable
- tendance : URL ou description de la source de tendance

Réponds UNIQUEMENT avec un JSON array d'idées à la fin, après tes recherches.
"""

        messages = [{"role": "user", "content": "Lance la veille virale mariage et génère les meilleures idées de contenu pour Mariable."}]

        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=4096,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = _process_tool_call(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})

            elif response.stop_reason == "end_turn":
                return self._parse_ideas(response)

    def get_weekly_digest(self) -> str:
        """Generate a weekly digest: what's working, what formats dominate, key hooks."""
        system_prompt = f"""{BRAND_CONTEXT}
Tu es un analyste de contenu social media spécialisé mariage.
Analyse les tendances de la semaine et produis un digest structuré en Markdown :

## Digest Hebdo — Contenu Mariage Instagram

### Ce qui cartonne cette semaine
(3 formats/sujets avec explication)

### Hooks qui convertissent
(5 exemples de hooks viraux adaptables à Mariable)

### À éviter
(2-3 tendances saturées ou hors-cible)

### Recommandation de la semaine
(1 format prioritaire à tester pour Mariable)
"""
        messages = [{"role": "user", "content": "Génère le digest hebdo des tendances mariage."}]
        while True:
            response = self.client.messages.create(
                model=MODEL,
                max_tokens=2048,
                system=system_prompt,
                tools=TOOLS,
                messages=messages,
            )
            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = _process_tool_call(block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
            elif response.stop_reason == "end_turn":
                for block in response.content:
                    if hasattr(block, "text"):
                        return block.text
                return ""

    def _parse_ideas(self, response) -> list[dict]:
        for block in response.content:
            if not hasattr(block, "text"):
                continue
            text = block.text
            start = text.rfind("[")
            end = text.rfind("]") + 1
            if start != -1 and end > start:
                try:
                    return json.loads(text[start:end])
                except json.JSONDecodeError:
                    pass
        return []
