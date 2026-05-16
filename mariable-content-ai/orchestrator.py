"""
Mariable Content AI — Orchestrateur principal

Usage :
  python orchestrator.py veille              # Lance la veille + push vers Notion
  python orchestrator.py redige              # Rédige les posts des idées Notion (statut: Idée)
  python orchestrator.py digest              # Génère le digest hebdo des tendances
  python orchestrator.py tout                # Veille + rédaction enchaînées
"""

import sys
from agents.watch_agent import WatchAgent
from agents.content_agent import ContentAgent
from agents.notion_agent import NotionAgent


def run_veille(nb_ideas: int = 5) -> list[dict]:
    print("\n🔍 Agent Veille — Analyse des tendances virales mariage...")
    watch = WatchAgent()
    notion = NotionAgent()

    ideas = watch.run(nb_ideas=nb_ideas)
    print(f"  → {len(ideas)} idées détectées\n")

    pushed = []
    for idea in ideas:
        idea["source"] = "🔍 Agent Veille"
        url = notion.add_idea(idea)
        print(f"  ✅ [{idea.get('score_viralite', 0):.1f}/10] {idea['titre']}")
        print(f"     Hook : {idea.get('hook', '')[:80]}")
        print(f"     Notion : {url}\n")
        pushed.append(idea)

    return pushed


def run_redige(limit: int = 3) -> list[dict]:
    print("\n✍️  Agent Contenu — Rédaction des posts Instagram...")
    notion = NotionAgent()
    content = ContentAgent()

    ideas = notion.get_ideas(status="💡 Idée")[:limit]
    if not ideas:
        print("  Aucune idée en attente dans Notion.")
        return []

    print(f"  → {len(ideas)} idées à rédiger\n")
    results = []

    for idea in ideas:
        print(f"  📝 Rédaction : {idea['titre']} ({idea.get('format', '')})")
        post = content.write_post(idea)

        notion.update_idea(idea["id"], {
            "statut": "✅ Rédigé",
            "caption": post.get("caption", ""),
            "hashtags": post.get("hashtags", ""),
            "hook": post.get("hook", ""),
        })

        print(f"  ✅ Hook : {post.get('hook', '')}")
        print(f"     CTA  : {post.get('cta', '')}")
        print(f"     Notion mis à jour → statut : Rédigé\n")
        results.append({"idea": idea, "post": post})

    return results


def run_digest() -> str:
    print("\n📊 Agent Veille — Digest hebdo des tendances mariage...\n")
    watch = WatchAgent()
    digest = watch.get_weekly_digest()
    print(digest)
    return digest


def main():
    command = sys.argv[1] if len(sys.argv) > 1 else "aide"

    if command == "veille":
        run_veille()
    elif command == "redige":
        run_redige()
    elif command == "digest":
        run_digest()
    elif command == "tout":
        run_veille()
        run_redige()
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
