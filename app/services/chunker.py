from langchain_text_splitters import RecursiveCharacterTextSplitter

def chunk_text(text:str, Strategy:str, chunk_overlap:int=200) -> list[str]: 
    if Strategy == "recursive" :
        return recursive_chunk(text)
    elif Strategy == "semantic":
        raise semantic_chunk(text)
    else:
        raise ValueError("Invalid chunking strategy. choose either 'recursive' or 'semantic'.")


def recursive_chunk(text:str) -> list[str]:
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=250)
    separators = ["\n\n", "\n","." ," ", ""]
    #  Split from paragraph--> to line --> to sentence --> to word 
    chunks = text_splitter.split_text(text)
    return chunks

def semantic_chunk(text:str) -> list[str]:
    raise NotImplementedError("Semantic chunking strategy is not implemented yet.")