class ChunkingService:
    
    def split(self, text:str, max_chunk_size:int = 1000) -> list[str]:
        paragraphs = text.split("\n")
        
        chunks = []
        current_chunk = ""
        current_size = 0
        last_paragraph = ""

        for paragraph in paragraphs:
            if current_size + len(paragraph) <= max_chunk_size:
                current_chunk += paragraph + "\n"
                current_size += len(paragraph)
                last_paragraph = paragraph
            else:
                chunks.append(current_chunk.strip())

                current_chunk = last_paragraph + "\n"
                current_chunk += paragraph + "\n"

                current_size = len(last_paragraph) + len(paragraph)

                last_paragraph = paragraph
                
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks