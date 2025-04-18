import marimo

__generated_with = "0.12.10"
app = marimo.App(width="medium", css_file="custom.css")


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

        The API version in the AI Sandbox sample code we were given older than that (but I don't know how to tell if this is current):  
        ```py
        SANDBOX_API_VERSION = "2024-02-01"
        ```
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

    system_prompt = "You are a helpful research assistant fluent in German. You help researchers identify important content in text from German scholarship."

    user_prompt = f"Identify and return any passages in this page of text that quote from texts by Karl Marx:\n{page_text}"
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


    # initialize an api client for AI sandbox

    SANDBOX_ENDPOINT = "https://api-ai-sandbox.princeton.edu/"
    SANDBOX_API_VERSION = "2024-02-01"

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
def _(Quote, client, openai, system_prompt, user_prompt):
    gpt4o_completion = client.beta.chat.completions.parse(
        model="gpt-4o",
        # model="gpt-4o-mini",
        # model="Meta-Llama-3-1-8B-Instruct-nwxcg",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # response_format=Quote,  # not supported by our API version
        tools=[
            openai.pydantic_function_tool(Quote),
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
    **quotation:**

    {gpt4o_parsed.text}

    **title:**
    {gpt4o_parsed.title}
    """)
    return (gpt4o_parsed,)


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""### gpt-4o-mini""")
    return


@app.cell
def _(Quote, client, openai, system_prompt, user_prompt):
    gpt4omini_completion = client.beta.chat.completions.parse(
        model="gpt-4o-mini",
        # model="Meta-Llama-3-1-8B-Instruct-nwxcg",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        # response_format=Quote,  # not supported by our API version
        tools=[
            openai.pydantic_function_tool(Quote),
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
    **quotation:**

    {gpt4omini_parsed.text}

    **title:**
    {gpt4omini_parsed.title}
    """)
    return (gpt4omini_parsed,)


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

        Setup requires installing [ollama](https://ollama.com/), and then start the server and download and run models.  (I did some version of this but it may not be the best way to do things, since I'm new to using Ollama. 😅)

        ```console
        ollama serve
        ollama run llama3.2
        ollama run mixtral
        ```

        You can use `ollama ps` to check which models are running and how much longer they will be running; default keepalive time is 5 minutes.
        """
    )
    return


@app.cell
def _(BaseModel, Quote, system_prompt, user_prompt):
    from ollama import chat


    # Supports nested models; we need to support multiple quotes on a page, so try a list of quotes
    # using the Quote model defined earlier
    class QuoteList(BaseModel):
        quotes: list[Quote]


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
    return QuoteList, chat, identify_quotes


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

    mo.md("\n\n".join(llama_quotes_md))
    return llama_q, llama_quotes_md


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

    mo.md("\n\n".join(mixtral_quotes_md))
    return mixtral_q, mixtral_quotes_md


@app.cell
def _(mo):
    mo.md(
        r"""
        ## CSV output?

        CSV output might be a simpler way to get structured output, but may be less reliable.
        """
    )
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


if __name__ == "__main__":
    app.run()
