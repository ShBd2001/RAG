"""
Brique 1 : la base vectorielle persistante.

Comportement du constructeur (l'aiguillage clé du TP) :
- si une base existe déjà sur disque au chemin donné -> on la recharge
- sinon, si des chunks sont fournis -> on crée la base et on les indexe
- sinon -> on lève une erreur explicite (rien à charger, rien à créer)
"""

import chromadb
from sentence_transformers import SentenceTransformer

import config


class AgentVectoriel:
    def __init__(self, db_path=None, collection_name=None, chunks=None):
        self.db_path = db_path or config.VECTOR_DB_PATH
        self.collection_name = collection_name or config.COLLECTION_NAME

        # Client persistant : les données survivent au redémarrage du programme
        self.client = chromadb.PersistentClient(path=self.db_path)

        existing_collections = [c.name for c in self.client.list_collections()]
        collection_exists = self.collection_name in existing_collections

        if collection_exists:
            self._load_existing_collection()
        elif chunks:
            self._create_collection(chunks)
        else:
            raise ValueError(
                f"Aucune collection '{self.collection_name}' trouvée dans '{self.db_path}' "
                "et aucun chunk fourni pour en créer une. "
                "Fournis des chunks (chunks=...) pour initialiser la base."
            )

    def _create_collection(self, chunks):
        """
        chunks : liste de dicts avec au minimum les clés 'id', 'text', 'source'
        (c'est exactement la forme de nos lignes du CSV du corpus).
        """
        # Le nom du modèle est écrit dans les métadonnées de la collection elle-même.
        # Au rechargement, on relira CE nom-là plutôt que celui (peut-être différent)
        # présent dans config.py au moment du rechargement.
        # -> Ca évite le bug silencieux suivant : si on change EMBEDDING_MODEL_NAME dans
        #    config.py après avoir indexé, un rechargement naïf encoderait la NOUVELLE
        #    question avec un NOUVEAU modèle, alors que les vecteurs stockés viennent
        #    de l'ANCIEN modèle. Les espaces vectoriels ne coïncident pas : les similarités
        #    cosinus deviennent n'importe quoi, sans aucune erreur levée. Le retrieval
        #    renverrait silencieusement des résultats incohérents.
        embedding_model_name = config.EMBEDDING_MODEL_NAME
        self.embedding_model = SentenceTransformer(embedding_model_name)

        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"embedding_model": embedding_model_name},
        )

        ids = [c["id"] for c in chunks]
        documents = [c["text"] for c in chunks]
        metadatas = [{"source": c.get("source", "")} for c in chunks]

        embeddings = self.embedding_model.encode(
            documents,
            batch_size=32,
            normalize_embeddings=True,  # pour que la similarité cosinus = simple produit scalaire
            show_progress_bar=True,
        )

        self.collection.add(
            ids=ids,
            documents=documents,
            embeddings=embeddings.tolist(),
            metadatas=metadatas,
        )

    def _load_existing_collection(self):
        self.collection = self.client.get_collection(name=self.collection_name)
        # On relit le nom du modèle stocké dans les métadonnées de la collection,
        # PAS celui de config.py : voir l'explication ci-dessus.
        embedding_model_name = self.collection.metadata["embedding_model"]
        self.embedding_model = SentenceTransformer(embedding_model_name)

    def encode(self, text):
        return self.embedding_model.encode(
            [text], normalize_embeddings=True
        )[0].tolist()

    def retrieve(self, question, n=None):
        n = n or config.TOP_K_CHUNKS
        query_embedding = self.encode(question)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n,
        )

        # results est un dict de listes de listes (une liste par requête envoyée,
        # ici on n'en envoie qu'une donc on prend l'indice [0])
        chunks = []
        for doc, meta, dist in zip(
            results["documents"][0],
            results["metadatas"][0],
            results["distances"][0],
        ):
            chunks.append({"text": doc, "source": meta.get("source", ""), "distance": dist})
        return chunks
