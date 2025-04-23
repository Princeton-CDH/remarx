"""
Script for saving the model responses for the quotations task for
for all prompts and AI Sandbox models.

Note: This script requires the AI Sandbox API key to the environment
variable `AI_SANDBOX_KEY`.

Examples:

python get_quotations.py [dataset csv] [prompts dir] [out csv]

export AI_SANDBOX_KEY=[your api key]; python get_title_mentions_responses.py \
        [dataset csv] [prompts dir] [out csv]

"""

import argparse
import csv
import pathlib
import sys
from collections.abc import Generator

from openai import BadRequestError
from tqdm import tqdm

from remarx.sandbox_utils import (
    create_client,
    # SANDBOX_MODELS,
    response_to_csv,
    submit_prompt,
)


def get_model_responses(
    model: str, prompt: str, dataset_rows: list[dict], client
) -> Generator[dict[str, str]]:
    """
    Get the model responses for a given prompt and dataset. Yield results
    as dictionary amenable to saving as a CSV.
    """
    for row in dataset_rows:
        row.copy()
        input_text = row.pop("input_text")
        try:
            response = submit_prompt(prompt, input_text, model=model, client=client)
            row |= response_to_csv(response)
        except BadRequestError as e:
            # Check for prompt content filtering
            if (
                e.status_code == 400
                and e.param == "prompt"
                and e.code == "content_filter"
            ):
                row |= {"model": model, "finish_reason": "prompt_content_filter"}
            else:
                raise

        print(row)  # temporary /debug
        yield row


def save_responses(
    dataset_csv: pathlib.Path,
    prompts_dir: pathlib.Path,
    out_csv: pathlib.Path,
) -> None:
    """
    Save the model responses for each model supported by the AI Sandbox
    and each task prompt for all examples in the dataset.
    """
    csv_fields = [
        "input_id",
        "input_file",
        "page_index",
        "prompt",
        "model",
        "timestamp",
        "finish_reason",
        "response",
    ]

    # Get examples from input dataset
    with open(dataset_csv, newline="", encoding="utf-8-sig") as csvfile:
        reader = csv.DictReader(csvfile)
        dataset_rows = [
            {
                "input_id": row["UUID"],
                "input_file": pathlib.Path(row["FILE"]).stem,
                "page_index": row["page_index"],
                "input_text": row["page_text"],
            }
            for row in reader
        ]
        n_examples = len(dataset_rows)

    # run on a subset of models
    models = ["o3-mini", "gpt-4o-mini", "gpt-4o"]
    client = create_client()

    with open(out_csv, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()

        prompt_files = list(prompts_dir.glob("basic.txt"))
        prompt_progress = tqdm(prompt_files, position=0)
        for prompt_file in prompt_progress:
            prompt_name = prompt_file.stem
            # Add prompt name to progress bar
            prompt_progress.set_description_str(f"Prompts - {prompt_name}")
            with open(prompt_file) as f:
                prompt_text = f.read()
            model_progress = tqdm(models, position=1)
            for model in model_progress:
                model_progress.set_description_str(f"Models - {model}")
                row_pfx = {
                    "model": model,
                    "prompt": prompt_name,
                }

                examples_progress = tqdm(
                    get_model_responses(model, prompt_text, dataset_rows, client),
                    total=n_examples,
                    desc="Submitting examples",
                    position=2,
                )
                for response in examples_progress:
                    row = row_pfx | response
                    writer.writerow(row)


def main():
    parser = argparse.ArgumentParser(
        "Run title mentions task for all prompts and models"
    )

    # Required arguments
    parser.add_argument(
        "in_csv",
        help="CSV containing title mentions annotated data",
        type=pathlib.Path,
    )
    parser.add_argument(
        "prompts_dir",
        help="Directory containing task-level prompts",
        type=pathlib.Path,
    )
    parser.add_argument(
        "out_csv",
        help="Filename where the resulting CSV should be saved",
        type=pathlib.Path,
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.in_csv.is_file():
        print(f"Error: input csv {args.in_csv} does not exist", file=sys.stderr)
        sys.exit(1)
    if not args.prompts_dir.is_dir():
        print(
            f"Error: prompts directory {args.promts_dir} does not exist",
            file=sys.stderr,
        )
        sys.exit(1)
    if args.out_csv.is_file():
        print(f"Error: output csv {args.out_csv} already exists", file=sys.stderr)
        sys.exit(1)

    save_responses(
        dataset_csv=args.in_csv,
        prompts_dir=args.prompts_dir,
        out_csv=args.out_csv,
    )


if __name__ == "__main__":
    main()
