"Base text input class with common functionality"

from collections.abc import Generator
from dataclasses import dataclass

from remarx.sentence.corpus.base_input import FileInput


@dataclass
class TextInput(FileInput):
    """Class for text file input for sentence corpus creation"""

    file_type = ".txt"
    "Supported file extension for text input"

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get plain-text contents for this file with any desired chunking (e.g.
        pages or other semantic unit).
        Default implementation does no chunking, no additional metadata.

        :returns: Generator with a dictionary of text and any other metadata
        that applies to this unit of text.
        """
        yield {"text": self.input_file.read_text(encoding="utf-8")}


FileInput.register_input(TextInput)
