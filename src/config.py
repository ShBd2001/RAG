"""
Module de configuration.
Toutes les constantes (noms de modèles, chemins) vivent ici et nulle part ailleurs.
Ça évite d'avoir "distiluse-base-multilingual-cased-v2" écrit en dur dans 3 fichiers
différents si un jour on veut changer de modèle.
"""

import os

# Modèle d'embedding (encodage des chunks + des questions)
EMBEDDING_MODEL_NAME = "distiluse-base-multilingual-cased-v2"

# Modèle de génération (le LLM qui répond à l'utilisateur)
GENERATION_MODEL_NAME = "llama-3.3-70b-versatile"

# Modèle de modération (famille "safeguard" de Groq, spécialisé détection d'abus)
MODERATION_MODEL_NAME = "meta-llama/Llama-Guard-4-12B"

# Chemin où ChromaDB persiste ses données sur disque
VECTOR_DB_PATH = os.path.join(os.path.dirname(__file__), "chroma_db")

# Nom de la collection ChromaDB
COLLECTION_NAME = "corpus_rag"

# Nombre de chunks récupérés à chaque question
TOP_K_CHUNKS = 3

# Chemins des fichiers de prompts (texte, pas de code -> se retravaillent sans toucher au code)
PROMPTS_DIR = os.path.join(os.path.dirname(__file__), "prompts")
RAG_SYSTEM_PROMPT_PATH = os.path.join(PROMPTS_DIR, "rag_system.txt")
MODERATOR_SYSTEM_PROMPT_PATH = os.path.join(PROMPTS_DIR, "moderator_system.txt")

# Marqueur remplacé par les chunks récupérés dans le prompt système du RAG
CHUNKS_PLACEHOLDER = "{{Chunks}}"
