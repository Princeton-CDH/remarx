"""
Utility functions for working with the AI Sandbox
"""

import os

from openai import AzureOpenAI
from openai.types.chat import ChatCompletion

# AI Sandbox variables
SANDBOX_API_KEY = os.environ["AI_SANDBOX_KEY"]
SANDBOX_ENDPOINT = "https://api-ai-sandbox.princeton.edu"
SANDBOX_API_VERSION = "2025-03-01-preview"


def create_client() -> AzureOpenAI:
    """
    Create an AI Sandbox client
    """
    return AzureOpenAI(
        api_key=SANDBOX_API_KEY,
        azure_endpoint=SANDBOX_ENDPOINT,
        api_version=SANDBOX_API_VERSION,
    )


def submit_prompt(
    task_prompt,
    user_prompt,
    model="gpt-4o",
) -> ChatCompletion:
    """
    Submits basic text prompt using given model with task- and user-level
    prompts. Returns resulting response object.
    """
    # Establish a connection to your Azure OpenAI instance
    client = create_client()

    # TODO: Determine what optional parameters should be customizable
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": task_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    return response


def get_text_response(response: ChatCompletion) -> str:
    """
    Extract the text output from model response. Prints warning if the model
    finished for an unexpected reason (i.e., length limit, content filtering)
    """
    # Assume the response contains a single output
    output_object = response.choices[0]
    # Check finish reason
    finish_reason = output_object.finish_reason
    if finish_reason == "length":
        print("WARNING: Response stopped early due to length limits!")
    elif finish_reason == "content_filter":
        print("WARNING: Content filtering occurred for response!")
    return output_object.message.content
