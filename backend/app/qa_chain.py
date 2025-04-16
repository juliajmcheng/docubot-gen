import os
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv

# Load env 
load_dotenv(dotenv_path="/app/.env")  # hardcoded path inside container
OPENAI_API_KEY=os.getenv("OPENAI_API_KEY")
print(f"🧪 Loaded API key: {OPENAI_API_KEY[:8]}...")  # safe to print the first 8 chars

# Custom prompt
QA_PROMPT = PromptTemplate.from_template("""
You are an AI researcher assistant. Based strictly on the context below, answer the user's question clearly and factually.
If the context is insufficient, respond with: "I don't know."

Context:
{context}

Question: {question}
""")

def get_qa_chain(document_text):
    # Remove known problematic OpenAI special tokens
    disallowed_tokens = ["<|endofprompt|>", "<|endoftext|>", "<|startoftext|>", "<|system|>", "<|user|>", "<|assistant|>"]
    for token in disallowed_tokens:
        document_text = document_text.replace(token, "")

    # Chunk text into small pieces for high-recall retrieval
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=600, chunk_overlap=80)
    texts = text_splitter.split_text(document_text)

    # Embed and index
    embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
    docsearch = FAISS.from_texts(texts, embeddings)

    # Use GPT-4 turbo via ChatOpenAI
    llm = ChatOpenAI(
        model_name="gpt-4-turbo",
        openai_api_key=OPENAI_API_KEY,
        temperature=0.3,
        request_timeout=60
    )

    chain = load_qa_chain(
        llm,
        chain_type="stuff",
        verbose=True
    )
    return docsearch, chain


def answer_question(docsearch, chain, query):
    # Limit to the 2 most relevant chunks to control prompt size
    docs = docsearch.similarity_search(query, k=10)
    print("📄 First chunk content:\n", docs[0].page_content[:500])
    trimmed_docs = []
    for doc in docs:
        doc.page_content = doc.page_content[:1200]
        trimmed_docs.append(doc)
    # Debug print (optional)
    print("\n📎 Retrieved docs:\n", [doc.page_content[:200] for doc in docs])
    print("📄 Retrieved Chunks:")
    for i, doc in enumerate(docs):
        print(f"Chunk {i+1}:\n{doc.page_content[:300]}\n---")

    return chain.run(input_documents=trimmed_docs, question=query)