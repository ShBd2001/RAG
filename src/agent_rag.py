"""
Brique 3 : le RAG, qui orchestre tout.

Pipeline de answer_question() :
1. Modération de la question (AVANT tout le reste -> décision de sécurité)
2. Si injection détectée -> refus immédiat, le LLM principal n'est JAMAIS contacté
3. Sinon -> retrieval des chunks pertinents
4. Construction du prompt système à trous (marqueur {{Chunks}} remplacé)
5. Appel au LLM de génération avec messages system/user
"""

import os

from dotenv import load_dotenv
from groq import Groq

import config
from agent_vectoriel import AgentVectoriel
from agent_moderateur import AgentModerateur


class AgentRAG:
    def __init__(self, vector_db: AgentVectoriel):
        load_dotenv()
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY manquant : vérifie ton fichier .env")

        self.client = Groq(api_key=api_key)
        self.moderator = AgentModerateur(self.client)
        self.vector_db = vector_db

        with open(config.RAG_SYSTEM_PROMPT_PATH, "r", encoding="utf-8") as f:
            self.system_prompt_template = f.read()

    def _build_system_prompt(self, chunks):
        formatted_chunks = "\n".join(
            f"- ({c['source']}) {c['text']}" for c in chunks
        )
        return self.system_prompt_template.replace(
            config.CHUNKS_PLACEHOLDER, formatted_chunks
        )

    def answer_question(self, question: str) -> str:
        moderation = self.moderator.moderate(question)
        if moderation.get("is_prompt_injection"):
            return (
                "Je ne peux pas traiter cette demande : elle a été identifiée "
                "comme une tentative de détournement des instructions du système."
            )

        chunks = self.vector_db.retrieve(question, n=config.TOP_K_CHUNKS)
        system_prompt = self._build_system_prompt(chunks)

        response = self.client.chat.completions.create(
            model=config.GENERATION_MODEL_NAME,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": question},
            ],
        )
        return response.choices[0].message.content