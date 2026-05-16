from notion_client import Client
from config import NOTION_TOKEN, NOTION_DATABASE_ID


class NotionAgent:
    def __init__(self):
        self.client = Client(auth=NOTION_TOKEN)
        self.db_id = NOTION_DATABASE_ID

    def get_ideas(self, status: str = "💡 Idée") -> list[dict]:
        """Fetch ideas from Notion filtered by status."""
        response = self.client.databases.query(
            database_id=self.db_id,
            filter={"property": "Statut", "select": {"equals": status}},
            sorts=[{"property": "Score Viralité", "direction": "descending"}],
        )
        ideas = []
        for page in response["results"]:
            props = page["properties"]
            ideas.append({
                "id": page["id"],
                "titre": _get_text(props, "Titre"),
                "hook": _get_text(props, "Hook"),
                "analyse": _get_text(props, "Analyse Viralité"),
                "tendance": _get_text(props, "Tendance Source"),
                "score": props["Score Viralité"]["number"],
                "format": _get_select(props, "Format"),
            })
        return ideas

    def add_idea(self, idea: dict) -> str:
        """Push a new idea to Notion. Returns page URL."""
        page = self.client.pages.create(
            parent={"database_id": self.db_id},
            properties={
                "Titre": {"title": [{"text": {"content": idea["titre"]}}]},
                "Statut": {"select": {"name": "💡 Idée"}},
                "Source": {"select": {"name": idea.get("source", "🔍 Agent Veille")}},
                "Score Viralité": {"number": idea.get("score_viralite", 0)},
                "Format": {"select": {"name": idea.get("format", "🎬 Reel")}},
                "Hook": {"rich_text": [{"text": {"content": idea.get("hook", "")}}]},
                "Analyse Viralité": {"rich_text": [{"text": {"content": idea.get("analyse", "")}}]},
                "Tendance Source": {"rich_text": [{"text": {"content": idea.get("tendance", "")}}]},
            },
        )
        return page["url"]

    def update_idea(self, page_id: str, updates: dict) -> None:
        """Update an existing idea (e.g. add caption, change status)."""
        properties = {}
        if "statut" in updates:
            properties["Statut"] = {"select": {"name": updates["statut"]}}
        if "caption" in updates:
            properties["Caption"] = {"rich_text": [{"text": {"content": updates["caption"]}}]}
        if "hashtags" in updates:
            properties["Hashtags"] = {"rich_text": [{"text": {"content": updates["hashtags"]}}]}
        if "hook" in updates:
            properties["Hook"] = {"rich_text": [{"text": {"content": updates["hook"]}}]}
        self.client.pages.update(page_id=page_id, properties=properties)


def _get_text(props: dict, key: str) -> str:
    field = props.get(key, {})
    if field.get("type") == "title":
        items = field.get("title", [])
    else:
        items = field.get("rich_text", [])
    return "".join(t["plain_text"] for t in items)


def _get_select(props: dict, key: str) -> str | None:
    sel = props.get(key, {}).get("select")
    return sel["name"] if sel else None
