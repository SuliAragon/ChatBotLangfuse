import os
from langchain_community.document_loaders import DirectoryLoader, TextLoader
from langchain_classic.text_splitter import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_community.vectorstores import FAISS
from dotenv import load_dotenv
from langfuse import observe

load_dotenv()

class RAGEngine:
    def __init__(self, knowledge_base_path="knowledge_base"):
        self.knowledge_base_path = knowledge_base_path
        self.vector_store = None
        self.embeddings = GoogleGenerativeAIEmbeddings(model="models/embedding-001")

    @observe(as_type="span")
    def load_and_process_documents(self):
        print("📚 Cargando documentos de la base de conocimiento...")
        loader = DirectoryLoader(self.knowledge_base_path, glob="**/*.txt", loader_cls=TextLoader)
        documents = loader.load()
        print(f"   - {len(documents)} documentos cargados.")

        text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
        texts = text_splitter.split_documents(documents)
        print(f"   - {len(texts)} fragmentos generados.")
        return texts

    @observe(as_type="span")
    def create_vector_store(self):
        texts = self.load_and_process_documents()
        if not texts:
            print("⚠️ No se encontraron documentos para indexar.")
            return

        print("🧠 Creando índice vectorial (Embeddings)...")
        self.vector_store = FAISS.from_documents(texts, self.embeddings)
        print("✅ Base de conocimiento indexada correctamente.")

    def get_retriever(self):
        if not self.vector_store:
            self.create_vector_store()
        return self.vector_store.as_retriever(search_kwargs={"k": 3})

    @observe(as_type="span")
    def query(self, query_text):
        if not self.vector_store:
            self.create_vector_store()
        
        docs = self.vector_store.similarity_search(query_text)
        return docs

if __name__ == "__main__":
    # Test básico
    rag = RAGEngine()
    rag.create_vector_store()
    results = rag.query("¿Cómo debo documentar una función en Python?")
    for doc in results:
        print(f"\n---\n{doc.page_content}\n---")
