"""
Base file input class with common functionality. Provides a factory
method for initialization of known input classes based on supported
file types.

Subclasses must define a supported `file_type` extension and call
`FileInput.register_input` to register the input class for use with
the factory method.

To initialize the appropriate subclass for a supported file type,
use [FileInput.init()][remarx.sentence.corpus.base_input.FileInput.init].

For a list of supported file types across all registered input classes,
use [FileInput.supported_types()][remarx.sentence.corpus.base_input.FileInput.supported_types].

"""

import pathlib
from collections.abc import Generator
from dataclasses import dataclass
from functools import cached_property
from typing import Any, ClassVar, Self

from remarx.sentence.segment import segment_text


@dataclass
class FileInput:
    """Base class for file input for sentence corpus creation"""

    input_file: pathlib.Path
    "Reference to input file. Source of content for sentences."

    field_names: ClassVar[tuple[str, ...]] = ("file", "offset", "text")
    "List of field names for sentences from text input files."

    _input_classes: ClassVar[dict[str, type[Self]]] = {}

    file_type: ClassVar[str]
    "Supported file extension; subclasses must define"

    @classmethod
    def register_input(cls, subclass: type[Self]) -> None:
        """
        Register an input class subclass with associated file type.
        """
        cls._input_classes[subclass.file_type] = subclass

    @cached_property
    def file_name(self) -> str:
        """
        Input file name. Associated with sentences in generated corpus.
        """
        return self.input_file.name

    def get_text(self) -> Generator[dict[str, str]]:
        """
        Get plain-text contents for this input file with any desired chunking
        (e.g. pages or other semantic unit).
        Subclasses must implement; no default implementation.

        :returns: Generator with a dictionary of text and any other metadata
        that applies to this unit of text.
        """
        raise NotImplementedError

    def get_sentences(self) -> Generator[dict[str, Any]]:
        """
        Get sentences for this file, with associated metadata.

        :returns: Generator of one dictionary per sentence; dictionary
        always includes: `text` (text content), `file` (filename),
        `sent_index` (sentence index within the document). It may include
        other metadata, depending on the input file type.
        """
        # zero-based sentence index for this file, across all chunks
        sentence_index = 0
        for chunk_info in self.get_text():
            # each chunk of text is a dictionary that at minimum
            # contains text for that chunk; it may include other metadata
            chunk_text = chunk_info["text"]
            for _char_idx, sentence in segment_text(chunk_text):
                # for each sentence, yield text, filename, and sentence index
                # with any other metadata included in chunk_info

                # character index is not included in output,
                # but may be useful for sub-chunk metadata (e.g., line number)
                sentence_info = chunk_info | {
                    "text": sentence,
                    "file": self.file_name,
                    "sent_index": sentence_index,
                }
                yield sentence_info

                # increment sentence index
                sentence_index += 1

    @classmethod
    def supported_types(cls) -> list[str]:
        """
        Unique list of supported file extensions for available input classes.
        """
        return list(set(cls._input_classes.keys()))

    @classmethod
    def init(cls, input_file: pathlib.Path) -> Self:
        """
        Instantiate and return the appropriate input class for the specified
        input file.

        :raises ValueError: if input_file is not a supported type
        """
        input_cls = cls._input_classes.get(input_file.suffix)
        # for now, check based on file extension
        if input_cls is None:
            raise ValueError(f"{input_file.suffix} is not a supported input type")
        return input_cls(input_file=input_file)
