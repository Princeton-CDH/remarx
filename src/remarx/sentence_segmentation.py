"""
Sentence segmentation utilities using Stanza NLP pipeline.
"""

import logging
import pathlib
from collections.abc import Generator

import stanza
from stanza import DownloadMethod
from tqdm import tqdm

logger = logging.getLogger(__name__)


class SentenceSegmenter:
    """
    This class provides methods to segment text into individual sentences,
    returning structured information about each sentence including its position
    and character indices within the original text, and the file it belongs to.
    """

    def __init__(
        self,
        lang: str = "de",
        download_method: DownloadMethod = DownloadMethod.REUSE_RESOURCES,
    ) -> None:
        """
        Initialize the stanza sentence segmenter. Language code defaults to "de" (German).
        Use DownloadMethod.REUSE_RESOURCES to avoid model re-downloading.
        """
        self.lang = lang
        self.pipeline = stanza.Pipeline(
            lang=lang, processors="tokenize", download_method=download_method
        )

    def segment_file(self, file_path: pathlib.Path) -> list[dict]:
        """
        Segment a text file into sentences.

        Returns:
            list[dict]: A list of sentence dictionaries, each containing the following keys:
                - file (str): The stem name of the file
                - sent_idx (int): Index of the sentence within the file
                - char_idx (int): Starting character position of the sentence
                - text (str): The sentence text

        Example:
            >>> segmenter = SentenceSegmenter()
            >>> sentences = segmenter.segment_file(pathlib.Path("document_name.txt"))
            >>> len(sentences)  # Total sentences in this file
            150
            >>> sentences[0]['file']
            'document_name'
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if not file_path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")

        try:
            text = file_path.read_text(encoding="utf-8")
        except Exception as e:
            raise OSError(f"Error reading file {file_path}: {e}") from e

        doc = self.pipeline(text)
        sentences = []

        for i, sentence in enumerate(doc.sentences):
            sentence_data = {
                "file": file_path.stem,
                "sent_idx": i,
                "char_idx": sentence.tokens[0].start_char,
                "text": sentence.text,
            }
            sentences.append(sentence_data)

        return sentences

    def segment_files(
        self, input_dir: pathlib.Path, file_pattern: str = "*.txt"
    ) -> Generator[dict, None, None]:
        """
        Segment multiple text files from a directory.
        Can specify file pattern to only process certain file types (defaults to txt files).
        """
        if not input_dir.exists():
            raise ValueError(f"Directory does not exist: {input_dir}")

        if not input_dir.is_dir():
            raise ValueError(f"Path is not a directory: {input_dir}")

        file_paths = list(input_dir.rglob(file_pattern))
        file_progress = tqdm(file_paths, desc="Processing files")

        for file_path in file_progress:
            file_progress.set_description_str(f"Processing {file_path.stem}")
            try:
                sentences = self.segment_file(file_path)
                yield from sentences
            except (OSError, FileNotFoundError) as e:
                # Log warning but continue processing other files
                logger.warning("Skipping file %s: %s", file_path, e)
                continue
