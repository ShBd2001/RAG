"""
Brique 2 : l'agent modérateur.

Pourquoi une classe séparée plutôt que "refuse les injections" dans le prompt du RAG ?
- Séparation des responsabilités : un modèle petit/rapide et spécialisé fait UNE seule
  chose (classifier), avec une sortie contrainte (JSON), ce qui est plus fiable et
  plus facile à tester qu'une consigne noyée parmi 5 autres règles dans un prompt
  généraliste.
- Sécurité : la décision de refuser est prise AVANT même de construire le prompt du
  RAG. Si on comptait uniquement sur le prompt du RAG pour se défendre, une injection
  suffisamment habile pourrait justement réussir à faire ignorer cette consigne-là
  en même temps que les autres (c'est tout le principe d'une injection réussie).
- Un modèle dédié à la modération peut être mis à jour / durci indépendamment du
  modèle de génération, sans toucher au reste du pipeline.
"""

import json

from groq import Groq

import config


class AgentModerateur:
    def __init__(self, groq_client: Groq):
        self.client = groq_client
        with open(config.MODERATOR_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            self.system_prompt = f.read()

    def moderate(self, question: str) -> dict:
        response = self.client.chat.completions.create(
            model=config.MODERATION_MODEL_NAME,
            messages=[
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": question},
            ],
            response_format={"type": "json_object"},
        )
        raw = response.choices[0].message.content
        try:
            return json.loads(raw)
        except json.JSONDecodeError:
            # Filet de sécurité : si le modèle ne renvoie pas un JSON valide,
            # on considère la question comme suspecte plutôt que de planter.
            return {"is_prompt_injection": True}
