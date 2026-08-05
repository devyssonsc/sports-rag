from llama_index.core.node_parser import SentenceSplitter
from llama_index.core.schema import Document

class LlamaIndexChunkingService:

    def __init__(
        self,
        chunk_size: int = 350,
        chunk_overlap: int = 50,
    ):
        self.splitter = SentenceSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    # def split(
    #     self,
    #     text: str,
    # ) -> list[str]:

    #     document = Document(text=text)

    #     nodes = self.splitter.get_nodes_from_documents(
    #         [document]
    #     )

    #     return [
    #         node.text
    #         for node in nodes
    #     ]
        
    def split(
        self,
        text: str,
    ) -> list[str]:

        document = Document(text=text)

        nodes = self.splitter.get_nodes_from_documents([document])

        print(f"Chunks: {len(nodes)}")

        for i, node in enumerate(nodes):
            print(
                f"{i}: chars={len(node.text)} "
                f"tokens={self.splitter._tokenizer(node.text).__len__()}"
            )

        return [node.text for node in nodes]