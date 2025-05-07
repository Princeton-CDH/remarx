import csv
from collections import defaultdict

import polars as pl


def load_title_phrases(filename: str) -> dict[str, str]:
    """
    Load title phrases from file. Returns a dictionary mapping
    a title (e.g., "Kapital") to a list of its search phrases
    used for identifying candidate sentences.
    """
    title_phrases = defaultdict(list)
    with open(filename, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            title_phrases[row["title"]].append(row["phrase"])
    return title_phrases


def load_candidate_sentences(
    filename: str, title_phrases: dict[str, str]
) -> pl.DataFrame:
    """
    Load from file and prepare candidate sentences dataframe.
    """
    # Load initial data
    df = pl.read_csv(filename)

    # Initial field munging
    df = df.with_columns(
        [
            # Create starting index
            pl.col("char_idx").alias("start_idx"),
            # Create phrase list from phrases column
            pl.col("phrases").str.split(" | ").alias("phrase_list"),
        ]
    )

    # Construct additional fields, dependent on previous step
    df = df.with_columns(
        [
            # Compute ending index
            (pl.col("start_idx") + pl.col("sentence").str.len_chars()).alias("end_idx"),
            # Determine if sentence is a title candidate by check for a title's phrases
            ## Determine if sentence is a candidate for Das Kapital
            (
                (
                    pl.col("phrase_list").list.set_intersection(
                        title_phrases["Kapital"]
                    )
                ).list.len()
                > 0
            ).alias("kapital_candidate"),
            ## Determine if sentence is a candidate for the Communist Manifesto
            (
                (
                    pl.col("phrase_list").list.set_intersection(
                        title_phrases["Manifesto"]
                    )
                ).list.len()
                > 0
            ).alias("manifest_candidate"),
        ]
    )

    return df
