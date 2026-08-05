import re


class TextCleaningService:

    def clean(
        self,
        text: str,
    ) -> str:

        text = self._normalize_line_breaks(text)
        text = self._remove_tabs(text)
        text = self._normalize_spaces(text)
        text = self._remove_empty_lines(text)
        
        text = self._remove_related_links(text)

        return text.strip()

    def _normalize_line_breaks(
        self,
        text: str,
    ) -> str:

        return text.replace("\r\n", "\n").replace("\r", "\n")

    def _remove_tabs(
        self,
        text: str,
    ) -> str:

        return text.replace("\t", " ")

    def _normalize_spaces(
        self,
        text: str,
    ) -> str:

        return re.sub(r"[ ]{2,}", " ", text)

    def _remove_empty_lines(
        self,
        text: str,
    ) -> str:

        return re.sub(r"\n{2,}", "\n", text)
    
    def _remove_related_links(
        self,
        text: str,
    ) -> str:

        lines = text.split("\n")

        cleaned_lines = []

        i = 0

        while i < len(lines):

            line = lines[i].strip()

            if line.startswith("- "):

                start = i

                while (
                    i < len(lines)
                    and lines[i].strip().startswith("- ")
                ):
                    i += 1

                block_size = i - start

                if block_size >= 3:
                    continue

                cleaned_lines.extend(lines[start:i])
                continue

            cleaned_lines.append(lines[i])
            i += 1

        return "\n".join(cleaned_lines)