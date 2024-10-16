import boto3
import streamlit as st
from langchain.llms.bedrock import Bedrock
from langchain.embeddings import BedrockEmbeddings
from langchain.document_loaders import PyPDFDirectoryLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import FAISS
from langchain.prompts import PromptTemplate
from langchain.chains import RetrievalQA

#Bedrock Client
bedrock = boto3.client(service_name="bedrock-runtime",region_name="us-east-1")

#Bedrock Embedding
bedrock_embedding = BedrockEmbeddings(model_id="amazon.titan-embed-text-v1",client=bedrock)

prompt_template="""
Human:Use the following pieces of context to provide a concise answer to the question at the 
end but use atleast summarize with 250 words with detailed explainatons.If you dont know the answer
just say that you dont know, dont try to make up an answer.
<context>
{context}
</context

Question:{question}

Assistant:"""
def get_documents():
    loader= PyPDFDirectoryLoader("data")
    documents=loader.load()
    text_splitter= RecursiveCharacterTextSplitter(chunk_size=1000,chunk_overlap=500)
    docs=text_splitter.split_documents(documents)
    return docs

def get_vector_store(docs):
    vector_store_faiss=FAISS.from_documents(docs,bedrock_embedding)
    vector_store_faiss.save_local("faiss_local")

def get_llm():
    llm=Bedrock(model_id="amazon.titan-text-lite-v1",client=bedrock)
    return llm

PROMPT = PromptTemplate(template=prompt_template,input_variables=["context","question"])


def get_llm_response(llm,vectorstore_fiass,query):
    qa=RetrievalQA.from_chain_type(llm=llm,
                                    chain_type="stuff",
                                    retriever=vectorstore_fiass.as_retriever(search_type="similarity",
                                                                             search_kwargs={"k":3}),
                                                                             return_source_documents=True,
                                                                             chain_type_kwargs={"prompt":PROMPT}
                                                                             )

    response=qa({"query":query})
    return response["result"]    
    
def main():
    st.set_page_config("RAG")
    st.header("End to End RAG using Bedrock")

    user_question= st.text_input("Ask Question from the pdf file")
    with st.sidebar:
        st.title("Update and create vector store")
        if st.button("Store Vector"):
            with st.spinner("Processing..."):
                docs=get_documents()
                get_vector_store(docs)
                st.success("Done")
    
    if st.button("Send"):
            with st.spinner("Processing..."):
                faiss_index=FAISS.load_local("faiss_local",bedrock_embedding,allow_dangerous_deserialization=True)
                llm=get_llm()
                st.write(get_llm_response(llm,faiss_index,user_question))
                st.success("Done")


if __name__=="__main__":
    main()
