"""
Point d'entrée. Premier lancement : indexe le corpus (crée la base).
Lancements suivants : recharge la base existante, sans réindexer.
"""

import os

import config
from load_corpus import load_corpus
from agent_vectoriel import AgentVectoriel
from agent_rag import AgentRAG


def get_vector_db() -> AgentVectoriel:
    db_exists = os.path.exists(config.VECTOR_DB_PATH) and os.listdir(config.VECTOR_DB_PATH)
    if db_exists:
        print("Base vectorielle existante détectée -> rechargement (pas de réindexation).")
        return AgentVectoriel()
    else:
        print("Aucune base existante -> création et indexation du corpus...")
        chunks = load_corpus("../05_corpus_rag.csv")
        return AgentVectoriel(chunks=chunks)


def main():
    vector_db = get_vector_db()
    rag = AgentRAG(vector_db)

    print("\nRAG prêt. Tape 'exit' pour quitter.\n")
    while True:
        question = input("Question : ").strip()
        if question.lower() in ("exit", "quit"):
            break
        if not question:
            continue
        answer = rag.answer_question(question)
        print(f"\nRéponse : {answer}\n")


if __name__ == "__main__":
    main()