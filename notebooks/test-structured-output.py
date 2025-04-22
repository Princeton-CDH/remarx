import marimo

__generated_with = "0.12.10"
app = marimo.App(
    width="medium",
    app_title="Test Structured Outputs",
    css_file="custom.css",
)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        # Test Structured Output / Structured response

        Some models and APIs have support for structured output, even defining and enforcing a schema and types for the generated output. Is that usable enough for us to use it? Which models support it?
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Testing with AI Sandbox 

        This is the [OpenAI post](https://openai.com/index/introducing-structured-outputs-in-the-api/) I started with.

        Then I found Azure OpenAI documentation on [structured outputs](https://learn.microsoft.com/en-us/azure/ai-services/openai/how-to/structured-outputs?tabs=python-secure%2Cdotnet-entra-id&pivots=programming-language-python).

        Documentation includes the list of supported models; this includes version dates, but I'm not sure we have access to that information for the AI Sandbox models.

        It _also_ lists the API version, which might be why I couldn't get this to work: 

        > Support for structured outputs was first added in API version `2024-08-01-preview`. It is available in the latest preview APIs as well as the latest GA API: `2024-10-21`.

        As of April 2025, the API version to use with AI Sandbox is **2025-03-01-preview**.

        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        * * *

        Use a page of text from the quote data subset for testing.

        This is the last entry in the quote data subset file. The expected quote based on annotation data: 

        > „die Arbeiter¬ klasse nicht die fertige Staatsmaschine einfach in Besitz nehmen und für ihre eigenen Zwecke in Bewegung setzen kann“
        """
    )
    return


@app.cell
def _():
    # define some variables with sample content and prompts to use in a few different calls

    page_text = """
    Das demokrattsche Prinzip und seine Anwendung. 25 liegt das auf der Hand. Wir mögen bis an den Eingang zur Werkstatt gleich¬ sein, aber in der Werkstatt sind wir es nicht mehr. Da muß der Ingenieur anordnett und der Schlosser, Dreher &c. ausführen, da kann der Heizer nicht nach seinem Kopf verfahren und den Kessel abstellen, wenn es ihm paßt. So¬ in jedem großen Wirthschaftsunternehmen, so aber auch in der Wirthschaft selbst. Ueberall, wo Kooporation ist, ist Arbeitstheilung, und wo Arbeitstheilung ist, ist Verschiedenheit der Funktionen, wo Verschiedenheit der Funktionen Verschieden¬ heit der Vollmachten. Diese sind heute vielfach übertrieben, weil das überkommene Nr C Klassenmoment hineinspielt, weil der Hert Ingenieur in der Regel der he¬ schenden Gesellschaftsklasse angehört und der Dreher der beherrschten. Diese Ueber¬ treibung, der Absolutismus in der Werkstatt &c., läßt sich beseitigen und wird im Lautfe der Entwicklung beseitigt werden. Aber eben nur die Uebertreibung, die Differenzirung wird darum doch bleiben. Sie wird nur ihre Schärfe dadurch¬ verlieren, daß die Menschen selbst vielseitiger ausgebildet und vielseitiger beschäftigt, werden, so daß die Unterordnung wechselt. Die Sozialdemokratie kann sich nicht außerhalb der Gesellschaft stellen, der sie lebt, kann also auch in ihren Reihen die thatsächlichen Unterschiede nicht ignoriren. Es wird immer ihr Bestreben sein müssen, für jeden Posten den möglichst geeigneten Mann herauszusuchen, und das trifft auch für die Vertretung im Parlament 3u. In Uebrigen sind für die Verwirklichung der Demokratie noch wichtigere, Aufgaben zu erfüllen als die Verbesserung der Stimmenzählungsmethoden. Sehr viel wichtiger ist die Demokratisirung der Verwaltungen, die bessere Vertheilung der Verwaltungsaufgaben und die Demokratisirung des Wahlrechts zu den Ver¬ waltungskörpern. Ob die Arbetterklasse statt durch 45 durch 95 Abgeordnete, im Reichstag vertreten ist, das würde an den Dingen vorderhand wenig ändern, denn die Gesetze würden kaum viel anders ausfallen als jetzt. Aber noch ist der Eintritt in die meisten Landtage, in die Provinzial- und Kreisvertretungen. den Arbeitern verschlossen, und in den Gemeindevertretungen nur mit großen Einschränkungen möglich. Das möchte Manchem hente als gleichgiltig erscheinen gegenüber den großen Erfolgen bei den Reichstagswahlen. Ohue diese zu ver¬ kleinern müssen wir jedoch daran erinnern, daß diese Erfolge zum Theil das Produkt außergewöhnlicher Umstände sind, und daß im Uebrigen „die Arbeiter¬ klasse nicht die fertige Staatsmaschine einfach in Besitz nehmen und für ihre eigenen Zwecke in Bewegung setzen kann“ Wir erkennen also an, daß innerhalb gewisser Greuzen und unter bestimmten. erhältnissen — sehr vorgeschrittene politische Einrichtungen - has Proportional¬ wahlsystem wünschbar sein mag. In Deutschland, wo noch so viele Elementar¬ bedingungen demokratischen Lebens fehlen, ist es ein Luxusartikel, für den Kraft¬ einzusetzen sie wichtigeren Arbeiten entziehen hieße. — Beispiele dafür giebt es schon heute. So kommen bei sogenannten freiwilligen Feuerwehren Subordinationsverhältnisse vor, die den bürgerlichen Lebensstellungen der be¬ treffenden Personen direkt widersprechen. Desgleichen beim Heer, und sie würden dort noch hüufiger sein, wenn nicht in Deutschland bei den Heereseinrichtungen dem ständischen Prinzip Rechnung getragen würde. NEW_DOCUMENT
    Zinner,+etal._1896_15:01_388_Notizen,Feuilleton
    """

    system_prompt = "You are a helpful research assistant fluent in German. You help researchers identify important content in text from German scholarship.  Identify and return any passages in this text provided by the user that quote from works by Karl Marx."

    user_prompt = page_text
    return page_text, system_prompt, user_prompt


@app.cell
def _():
    import json
    import os
    from typing import Optional

    import marimo as mo
    import openai
    from openai import AzureOpenAI
    from pydantic import BaseModel


    # define a simple model with the fields we want returned
    # previously tried including start/end indices; model returns numbers but they are useless
    class Quote(BaseModel):
        text: str
        title: Optional[str]


    # Both APIs supports nested models; we need to support multiple quotes on a page, so return a list of quotes
    # using the Quote model defined above
    class QuoteList(BaseModel):
        quotes: list[Quote]


    # initialize an api client for AI sandbox

    SANDBOX_ENDPOINT = "https://api-ai-sandbox.princeton.edu/"
    SANDBOX_API_VERSION = "2025-03-01-preview"

    client = AzureOpenAI(
        api_key=os.getenv("AI_SANDBOX_KEY"),
        api_version=SANDBOX_API_VERSION,
        azure_endpoint=SANDBOX_ENDPOINT,
    )
    return (
        AzureOpenAI,
        BaseModel,
        Optional,
        Quote,
        QuoteList,
        SANDBOX_API_VERSION,
        SANDBOX_ENDPOINT,
        client,
        json,
        mo,
        openai,
        os,
    )


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### gpt-4o

        For structured response with gpt-4o, we use openai + pydantic to pass in the response model to the `tools` option.

        If you try passing it in as a response format (`response_format=Quote`), you get a BadRequest response with this error message: 
        ```
        response_format value as json_schema is enabled only for api versions 2024-08-01-preview and later
        ```
        """
    )
    return


@app.cell
def _(QuoteList, client, openai, system_prompt, user_prompt):
    gpt4o_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        # model="gpt-4o-mini",
        # model="Meta-Llama-3-1-8B-Instruct-nwxcg",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # response_format=QuoteList.model_json_schema(),  # not supported by our API version or not being passed correctly
        tools=[
            openai.pydantic_function_tool(QuoteList),
        ],
    )
    return (gpt4o_completion,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Dump the full response as json:""")
    return


@app.cell
def _(gpt4o_completion):
    # here is the full response as json
    print(gpt4o_completion.model_dump_json(indent=2))
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Output the parsed response:""")
    return


@app.cell
def _(gpt4o_completion, mo):
    # this parsed_arguments field is actually a Quote instance!
    gpt4o_parsed = (
        gpt4o_completion.choices[0].message.tool_calls[0].function.parsed_arguments
    )

    mo.md(f"""
    Returned {len(gpt4o_parsed.quotes)} quote(s).

    **quotation:**

    {gpt4o_parsed.quotes[0].text}


    **title:**
    {gpt4o_parsed.quotes[0].title}


    """)
    return (gpt4o_parsed,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        **GPT4o** : ✅ quote  ⛔title

        Correctly returns the full text of the expected quote and only that quote.

        It looks like it is using the article title (?) at the top of the page text as the title.  The tag in the annotation data is "Manifest der Kommunistischen Partei"
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### gpt-4o-mini""")
    return


@app.cell
def _(QuoteList, client, openai, system_prompt, user_prompt):
    gpt4omini_completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        # model="Meta-Llama-3-1-8B-Instruct-nwxcg",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # response_format=Quote,  # not supported by our API version
        tools=[
            openai.pydantic_function_tool(QuoteList),
        ],
    )
    return (gpt4omini_completion,)


@app.cell
def _(gpt4omini_completion):
    print(gpt4omini_completion.model_dump_json(indent=2))
    return


@app.cell
def _(gpt4omini_completion, mo):
    # this parsed_arguments field is actually a Quote instance!
    gpt4omini_parsed = (
        gpt4omini_completion.choices[0]
        .message.tool_calls[0]
        .function.parsed_arguments
    )

    mo.md(f"""
    Returned {len(gpt4omini_parsed.quotes)} quote(s).

    **quotation:**

    {gpt4omini_parsed.quotes[0].text}


    **title:**
    {gpt4omini_parsed.quotes[0].title}
    """)
    return (gpt4omini_parsed,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        **GPT4o-mini** : ⛔/✅quote  ⛔title

        On a previous run it returned incorrect quote: a different set of text surrounded by „“.  This time it returned the correct quote.

        Like GPT4o, it returns the text at the beginning of the page as a title.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ### ⛔ llama 3.1 8B instruct 

        I couldn't get this one to work. When I try the `tools` parameters that works for gpt4o and our version of the API: 
        ```python
        tools=[
                openai.pydantic_function_tool(Quote),
            ],
        ```
        I get an "invalid input error." The details of the message indicate it's complaining about required fields (maybe required fields for the quote object).

        When I try specifying it as a response format, I get different errors. Passing in the class: 
        ```python
        response_format=Quote
        ```
        Results in 
        > Response format was json_schema but must be either 'text' or 'json_object'.

        When I try passing the json schema for my model, I get the same error: 
        ```python
        response_format=Quote.model_json_schema()
        ```
        """
    )
    return


@app.cell(disabled=True)
def _(Quote, client, system_prompt, user_prompt):
    llama_completion = client.beta.chat.completions.parse(
        model="Meta-Llama-3-1-8B-Instruct-nwxcg",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # not sure the right syntax for this one
        response_format=Quote.model_json_schema(),
    )
    return (llama_completion,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        ## Testing with local Ollama server

        Testing with the Ollama python client based on a [blog post about structured outputs](https://ollama.com/blog/structured-outputs).

        Setup requires installing [ollama](https://ollama.com/), and then start the server and download (pull) and run models.

        ```console
        pip install ollama
        ollama serve
        ollama run llama3.2
        ollama run mixtral
        ```

        You can use `ollama ps` to check which models are running and how much longer they will be running; default keepalive time is 5 minutes.
        """
    )
    return


@app.cell
def _(QuoteList, system_prompt, user_prompt):
    from ollama import chat


    def identify_quotes(page_text, model):
        response = chat(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            model=model,
            format=QuoteList.model_json_schema(),
        )

        return QuoteList.model_validate_json(response.message.content)
    return chat, identify_quotes


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### llama3.2""")
    return


@app.cell
def _(identify_quotes, page_text):
    # try getting from llama3.2
    llama_quotes = identify_quotes(page_text, "llama3.2")
    return (llama_quotes,)


@app.cell
def _(llama_quotes, mo):
    llama_quotes_md = [f"Identified {len(llama_quotes.quotes)} quote(s)"]

    for llama_q in llama_quotes.quotes:
        llama_quotes_md.append(f"""**quotation:**    
    {llama_q.text}

    **title:**
    {llama_q.title}""")

    mo.md("\n\n\n".join(llama_quotes_md))
    return llama_q, llama_quotes_md


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        **llama3.2** : ⛔/0️⃣ quote  ⛔/0️⃣title

        On some runs it returned an incorrect quote and incorrect title. It was returning some text from the third line of the first paragraph. When I adjusted the prompt to move the instructions to the system prompt, it didn't return anything.
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### mixtral""")
    return


@app.cell
def _(identify_quotes, page_text):
    mixtral_quotes = identify_quotes(page_text, "mixtral")
    return (mixtral_quotes,)


@app.cell
def _(mixtral_quotes, mo):
    mixtral_quotes_md = [f"Identified {len(mixtral_quotes.quotes)} quote(s)"]

    for mixtral_q in mixtral_quotes.quotes:
        mixtral_quotes_md.append(f"""**quotation:**    
    {mixtral_q.text}

    **title:**
    {mixtral_q.title}""")

    mo.md("\n\n\n".join(mixtral_quotes_md))
    return mixtral_q, mixtral_quotes_md


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        **mixtral** : ⛔quote  ⛔title

        Returning multiple things, all of them wrong. On a previous run, before I modified the prompt, it returned some text near the beginning of the first paragraph (also incorrect).
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Ollama server is [compatible with openai chat completions API](https://ollama.com/blog/openai-compatibility), including structured responses.""")
    return


@app.cell
def _():
    from openai import OpenAI


    ollama_oaiclient = OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama",  # required, but unused
    )
    return OpenAI, ollama_oaiclient


@app.cell
def _(QuoteList, ollama_oaiclient, openai, system_prompt, user_prompt):
    ollama_completion = ollama_oaiclient.beta.chat.completions.parse(
        model="llama3.2",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # response_format=QuoteList.model_json_schema(),  # this seems to be ignored
        tools=[
            openai.pydantic_function_tool(QuoteList),
        ],
    )
    return (ollama_completion,)


@app.cell
def _(ollama_completion):
    print(ollama_completion.model_dump_json(indent=2))
    return


@app.cell
def _(mo):
    mo.md(r"""The API is not exactly compatible, since the `tool_calls` is null. The content looks like a json dump of the QuoteList object with associated quotes, so it is enforcing the structure.""")
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## CSV output

        CSV output might be a simpler way to get structured output, but may be less reliable.

        Testing with the last paragraph of page text from the quote subset (page index 661, two quotes).

        The expected quote from this paragraph:
        > „Zur Lösung dieses Widerspruchs" fährt er fort, „bedarf es noch vieler Mittelglieder.“ Er versprach, diese Lösung später zu geben. 
        """
    )
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### ollama - llama3.2""")
    return


@app.cell
def _(chat, system_prompt):
    csv_prompt = """Identify any direct quotes of Karl Marx's works in this paragraph, along with the work title if known. Also include the source for the title (context reference or otherwise). Return the results in this CSV format:
    number,quote,title,title_source

    Nachdem Marx im ersten Bande des „Kapital“, Kapitel X, das Gesetz, des Mehrwerths festgestellt hatte, fügte er sogleich hinzu, „daß dies Gesetz offenbar, aller auf den Augenschein gegründeten Erfahrung widerspricht". „Zur Lösung dieses Widerspruchs" fährt er fort, „bedarf es noch vieler Mittelglieder.“ Er versprach, diese Lösung später zu geben. Die wenigen Nationalökonomen, denen diese Stelle auffiel, setzten ihre Zuversicht auf diesen ihnen unlösbar scheinenden Widerspruch, der nach ihrer Ansicht die Theorie zu Falle bringen mußte. Mehrere hofften, daß der Theore¬ tiker des Werthes dort mit seiner Dialektik und seinem Kommumnismus scheitern. werde, denen, wie sie überzeugt waren, jede wissenschaftliche Grundlage fehle. Herr Loria, der geniale Entdecker so mancher schon von Marx entdeckten Theorien, ging so weit, zu behaupten, daß derselbe, um seine Ohumacht nicht einzugestehen, sich entschlossen hätte, die beiden Bände, welche sein ökonomisches
    """

    csvresponse = chat(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": csv_prompt},
        ],
        model="llama3.2",
    )
    csvresponse
    return csv_prompt, csvresponse


@app.cell
def _(csvresponse):
    print(csvresponse.message.content)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### AI sandbox - gpt-4o""")
    return


@app.cell
def _(client, csv_prompt, system_prompt):
    # try ai sandbox gpt-4o with csv output

    gpt4o_csv_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": csv_prompt},
        ],
    )
    return (gpt4o_csv_completion,)


@app.cell
def _(gpt4o_csv_completion):
    print(gpt4o_csv_completion.choices[0].message.content)
    return


@app.cell
def _(mo):
    mo.md(r"""The second quote found is the expected one, but the full content is not returned.""")
    return


@app.cell
def _(mo):
    mo.md(r"""### AI sandbox - gpt-4o-min""")
    return


@app.cell
def _(client, csv_prompt, system_prompt):
    gpt4omini_csv_completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": csv_prompt},
        ],
    )
    return (gpt4omini_csv_completion,)


@app.cell
def _(gpt4omini_csv_completion):
    print(gpt4omini_csv_completion.choices[0].message.content)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(
        r"""
        The second quote is the expected response. It doesn't return the full text, but returns more of the quote than GPT4o did. They seem to be stopping at punctuation - likely because this quote as annotated includes text _between_ and _after_ the parts of the quote.

        > „Zur Lösung dieses Widerspruchs" fährt er fort, „bedarf es noch vieler Mittelglieder.“ Er versprach, diese Lösung später zu geben.

        From google translate:

        > "To resolve this contradiction," he continues, "many intermediate links are still needed." He promised to provide this solution later.
        """
    )
    return


if __name__ == "__main__":
    app.run()
