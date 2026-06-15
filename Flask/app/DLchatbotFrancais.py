# -*- coding: utf-8 -*-

import pandas as pd
from pathlib import Path
from langchain.schema import Document
from langchain.text_splitter import CharacterTextSplitter
from langchain_huggingface import HuggingFaceEmbeddings
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaLLM
from langchain.prompts import PromptTemplate
from langchain_core.runnables import RunnableSequence

# 0. Configuration des fichiers et thèmes
files_and_themes = [
    ("ScrapedPeriodeColoniale.xlsx",  "Période Coloniale"),
    ("ScrapedINDEPENDENCE.xlsx",      "Indépendance"),
    ("ScrapedReformesRecentes.xlsx",  "Réformes Récentes"),
    ("ScrapedREGNEDEHASSANII.xlsx",   "Règne de Hassan II"),
]

# 1. Charger et filtrer tous les DataFrames en un seul jeu de Documents
all_docs = []
for filename, theme in files_and_themes:
    path = Path(filename)
    if not path.exists():
        print(f"⚠️ Fichier introuvable : {filename}, je passe.")
        continue
    df = pd.read_excel(path, engine="openpyxl")
    df = df[df['status'].str.lower() == 'scraped']
    for _, row in df.iterrows():
        all_docs.append(
            Document(
                page_content=row['content'],
                metadata={
                    "theme": theme,
                    "subtheme": row.get('subtheme', ""),
                    "source": path.stem
                }
            )
        )

# 2. Chunking
splitter = CharacterTextSplitter(chunk_size=1000000, chunk_overlap=200)
split_docs = splitter.split_documents(all_docs)

# 3. Embeddings + vectorstore
embedder = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
vectordb = Chroma.from_documents(
    split_docs,
    embedder,
    persist_directory="./chroma_db"
)
retriever = vectordb.as_retriever(search_kwargs={"k": 4})

# 4. LLM Ollama
llm = OllamaLLM(
    model="llama3:latest",
    base_url="http://localhost:11434",
    verbose=False,
    streaming=True  # activation du streaming
)

prompt = PromptTemplate(
    input_variables=["context", "query"],
    template=(
        "Tu es un expert reconnu en histoire du Maroc, doté d'une grande rigueur scientifique. "
        "Utilise uniquement les informations contenues dans le contexte ci-dessous pour formuler une réponse précise, claire et complète, "
        "toujours en français.\n\n"
        "Si la réponse à la question ne se trouve pas dans le contexte, répond honnêtement que l'information n'est pas disponible.\n\n"
        "Contexte :\n{context}\n\n"
        "Question : {query}\n"
        "Réponse :"
    )
)


# 6. Chaîne moderne avec RunnableSequence
chain = prompt | llm

# 7. Fonction de réponse 
def get_answer_stream(question: str):
    relevant_docs = retriever.invoke(question)
    context = "\n\n---\n\n".join(doc.page_content for doc in relevant_docs)

    # Assuming `chain` is your RunnableSequence(prompt | llm)
    response_stream = chain.stream({"context": context, "query": question})

    for token in response_stream:
        # token is a string chunk — you can yield it directly
        yield token
