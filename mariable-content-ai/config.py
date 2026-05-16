import os
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.environ["ANTHROPIC_API_KEY"]
NOTION_TOKEN = os.environ["NOTION_TOKEN"]
NOTION_DATABASE_ID = os.environ["NOTION_DATABASE_ID"]

MODEL = "claude-sonnet-4-6"

BRAND_CONTEXT = """
Tu travailles pour Mariable (mariable.fr), une plateforme française qui aide les couples
à organiser leur mariage sereinement. La marque est élégante, moderne, bienveillante.
Audience cible : couples fiancés de 25-35 ans en France.
Ton : inspirant, rassurant, pratique. Pas de jargon. Pas trop formel.
Réseau principal : Instagram (Reels, Carrousels, Posts, Stories).
"""

VIRALITY_CRITERIA = {
    "croissance_vues": 0.30,
    "engagement_rate": 0.25,
    "duplication_format": 0.20,
    "pertinence_mariable": 0.15,
    "fraicheur": 0.10,
}
