"""
Script for saving the model responses for the title mentions task for
for all prompts and AI Sandbox models.

Note: This script requires the AI Sandbox API key to the environment
variable `AI_SANDBOX_KEY`.

Examples:

python get_title_mentions_responses.py [dataset csv] [prompts dir] [out csv]

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
    SANDBOX_MODELS,
    response_to_csv,
    submit_prompt,
)


def get_model_responses(
    model: str,
    prompt: str,
    dataset_csv: pathlib.Path,
) -> Generator[dict[str, str]]:
    """
    Get the model responses for a given prompt and dataset. Yield results
    as dictionary amenable to saving as a CSV.
    """
    with open(dataset_csv, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            input_id = row["UUID"]
            input_file = pathlib.Path(row["File"]).stem
            input_text = row["Text"]

            row = {"input_id": input_id, "input_file": input_file}

            try:
                response = submit_prompt(
                    prompt,
                    input_text,
                    model=model,
                )
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
        "prompt",
        "model",
        "timestamp",
        "finish_reason",
        "response",
    ]

    # Get number of examples in dataset
    with open(dataset_csv, newline="") as csvfile:
        reader = csv.DictReader(csvfile)
        n_examples = sum(1 for _ in reader)

    with open(out_csv, mode="w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=csv_fields)
        writer.writeheader()

        prompt_files = list(prompts_dir.glob("*.txt"))
        prompt_progress = tqdm(prompt_files, position=0)
        for prompt_file in prompt_progress:
            prompt_name = prompt_file.stem
            # Add prompt name to progress bar
            prompt_progress.set_description_str(f"Prompts - {prompt_name}")
            with open(prompt_file) as f:
                prompt_text = f.read()
            model_progress = tqdm(SANDBOX_MODELS, position=1)
            for model in model_progress:
                model_progress.set_description_str(f"Models - {model}")
                row_pfx = {
                    "model": model,
                    "prompt": prompt_name,
                }

                examples_progress = tqdm(
                    get_model_responses(model, prompt_text, dataset_csv),
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
