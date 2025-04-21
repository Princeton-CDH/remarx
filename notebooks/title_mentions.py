import marimo

__generated_with = "0.12.10"
app = marimo.App()


@app.cell
def _():
    # Notebook for exploring title mention prompts
    return


@app.cell
def _():
    import marimo as mo
    from remarx.sandbox_utils import submit_prompt
    from remarx.notebook_utils import display_bracketed_response
    return display_bracketed_response, mo, submit_prompt


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""Below is a sample page of text with several title mentions including _Das Kapital_ and _The Communist Manifesto_.""")
    return


@app.cell(hide_code=True)
def _():
    # Note: pages may not have regular separations across files!
    sample_page = """
    Rothkoller.
    ürst
    falls gar kein Gewicht darauf zu legen. Und nun gestattet ihnen Marx selbst
    — sie müssen offenbar sehr erstaunen, wenn sie die Stelle im „Kapital“ lesen,
    und sich im tiefsten Grunde ihres Herzens blamirt fühlen, daß sie bisher viel
    marxistischer waren, als Marx selbst, der offenbar auch nach 1848 noch einiges
    beobachtete und dachte — von diesem Parteidogma abzuweichen“, und so seiten¬
    lang weiter.
    Hören wir nun nach dem „alten“ Max auch den „jungen“ Marx über
    Kooperativfabriken der Arbeiter. In der Inauguraladresse der Internationalen
    Arbeiterassoziation heißt es: „Wir sprechen von der Kooperativbewegung, von den
    auf dem Prinzip der Kooperation beruhenden, durch wenige unverzagte, wenn auch


    ununterstützte Hände ins Leben gerufenen Fabriken. Der Werth dieser großen
    sozialen ixperimente kann nicht hoch genug veranschlagt werden. Durch die That,
    statt der Gründe, haben sie bewiesen, daß Produktion in großem Maßstabe und
    in Uebereinstimmung mit den Geboten der modernen Wissenschaft stattfinden kann
    ohne die Existenz einer Klasse von Unternehmern, die einer Klasse von Arbeitern
    zu thun giebt, daß die Arbeitsmittel, um Früchte zu tragen, nicht als Werkzeug
    der Herrschaft über und der Ausbeutung gegen den Arbeitenden selbst nonopoli¬
    sirt zu werden brauchen, und daß Lohnarbeit, wie Sklavenarbeit wie Leibeigen¬
    schaft, nur eine vorübergehende und untergeordnete Form ist, die dem Untergange
    geweiht, verschwinden muß vor der assoziirten Arbeit, die ihre schwere Aufgabe
    mit williger Hand, leichtem Sinn und fröhlichem Herzen erfüllt." So der „junge
    Maxx in einer weltbekannten Urkunde, die am Eingange der modernen inter¬
    nationalen Arbeiterbewegung steht, und da soll sich die deutsche Sozialdemokratie


    „im tiefsten Grunde ihres Herzens blamirt“ fühlen, wenn der „alte“ Marx im
    dritten Bande des „Kapital“ sich in gleichem Sinne ausspricht. Ach, Herr Platter!
    Mit dem viertel oder halben Dutzend „Widersprüche", die Herr Platter
    sonst noch aus sozialdemokratischen Schriften herausklaubt, steht es ebenso, wie
    mit den beiden hier gegebenen Proben. Wir verzichten gern auf jede weitere
    rerzitiums, und gehen auf den Kern dessen ein, was
    Korrektur dieses Schüler
    Herr Platter eigentlich will. Er überschreibt den zweiten Hauptabschnitt seines
    Buches, der sich mit dem Sozialismus beschäftigt: Gewalt oder Arbeit? Das
    soll heißen: Marx und die deutsche Sozialdemokratie sind auf dem Holzwege,
    wenn sie politische Macht erobern wollen, um die bürgerliche Gesellschaft durch


    „Gewalt“ von oben her in die sozialistische Gesellschaft umzukrempeln; die Eman¬
    zipation der Arbeiterklasse ist nur möglich durch friedliche „Arbeit“ von unten
    auf, durch Gewerkvereine, Konsumgenossenschaften und Kooperativfabriken. Man
    merkt jetzt, weshalb Herr Platter aus allen möglichen Schriften von Marx, vom
    Kommunistischen manifest bis zum dritten Bande des „Kapital“, alle mög¬
    lichen Zitate herauschleppt, aber um die Literatur der Internationalen in weitem
    Bogen herumgeht. Auch nicht mit einem Sterbenswörtchen erfahren die Leser
    seines Buches, daß es eine solche Literatur giebt. Und doch müßte ein Mann
    der Wissenschaft, der über Marx als Praktiker und Taktiker der Arbeiterfrage
    sprechen will, in allererster Reihe auf die Literatur der Internationalen zurück¬
    gehen. Wir reden hier nicht von den Zeilenreißern der bürgerlichen Tages= und
    Wochenpresse, die es halten mögen, wie sie wollen, aber ein Professor der Staats¬
    wissenschaften, der den praktischen Arbeiterpolitiker Marx kritisiren will, der muß
    so viel Royalität und so viele Kenntnisse besitzen, um diesen Politiker da zu
    suchen, wo er zu finden ist. Selbstverständlich hat Herr Platter aber seine guten
    Gründe, sich anzustellen, als gebe es keine Literatur der Internationalen. Denn
    wenn er sich dieser Literatur auch nur auf Kanonenschußweite nähern würde, so
    """
    return (sample_page,)


@app.cell(hide_code=True)
def _(mo):
    # For viewing "expected" annotations
    annotated_sample_page = """
    Rothkoller.
    ürst
    falls gar kein Gewicht darauf zu legen. Und nun gestattet ihnen Marx selbst
    — sie müssen offenbar sehr erstaunen, wenn sie die Stelle im <mark>„Kapital“</mark> lesen,
    und sich im tiefsten Grunde ihres Herzens blamirt fühlen, daß sie bisher viel
    marxistischer waren, als Marx selbst, der offenbar auch nach 1848 noch einiges
    beobachtete und dachte — von diesem Parteidogma abzuweichen“, und so seiten¬
    lang weiter.
    Hören wir nun nach dem „alten“ Max auch den „jungen“ Marx über
    Kooperativfabriken der Arbeiter. In der <mark>Inauguraladresse der Internationalen
    Arbeiterassoziation</mark> heißt es: „Wir sprechen von der Kooperativbewegung, von den
    auf dem Prinzip der Kooperation beruhenden, durch wenige unverzagte, wenn auch


    ununterstützte Hände ins Leben gerufenen Fabriken. Der Werth dieser großen
    sozialen ixperimente kann nicht hoch genug veranschlagt werden. Durch die That,
    statt der Gründe, haben sie bewiesen, daß Produktion in großem Maßstabe und
    in Uebereinstimmung mit den Geboten der modernen Wissenschaft stattfinden kann
    ohne die Existenz einer Klasse von Unternehmern, die einer Klasse von Arbeitern
    zu thun giebt, daß die Arbeitsmittel, um Früchte zu tragen, nicht als Werkzeug
    der Herrschaft über und der Ausbeutung gegen den Arbeitenden selbst nonopoli¬
    sirt zu werden brauchen, und daß Lohnarbeit, wie Sklavenarbeit wie Leibeigen¬
    schaft, nur eine vorübergehende und untergeordnete Form ist, die dem Untergange
    geweiht, verschwinden muß vor der assoziirten Arbeit, die ihre schwere Aufgabe
    mit williger Hand, leichtem Sinn und fröhlichem Herzen erfüllt." So der „junge
    Maxx in einer weltbekannten Urkunde, die am Eingange der modernen inter¬
    nationalen Arbeiterbewegung steht, und da soll sich die deutsche Sozialdemokratie


    „im tiefsten Grunde ihres Herzens blamirt“ fühlen, wenn der „alte“ Marx im
    <mark>dritten Bande des „Kapital“</mark> sich in gleichem Sinne ausspricht. Ach, Herr Platter!
    Mit dem viertel oder halben Dutzend „Widersprüche", die Herr Platter
    sonst noch aus sozialdemokratischen Schriften herausklaubt, steht es ebenso, wie
    mit den beiden hier gegebenen Proben. Wir verzichten gern auf jede weitere
    rerzitiums, und gehen auf den Kern dessen ein, was
    Korrektur dieses Schüler
    Herr Platter eigentlich will. Er überschreibt den zweiten Hauptabschnitt seines
    Buches, der sich mit dem Sozialismus beschäftigt: Gewalt oder Arbeit? Das
    soll heißen: Marx und die deutsche Sozialdemokratie sind auf dem Holzwege,
    wenn sie politische Macht erobern wollen, um die bürgerliche Gesellschaft durch


    „Gewalt“ von oben her in die sozialistische Gesellschaft umzukrempeln; die Eman¬
    zipation der Arbeiterklasse ist nur möglich durch friedliche „Arbeit“ von unten
    auf, durch Gewerkvereine, Konsumgenossenschaften und Kooperativfabriken. Man
    merkt jetzt, weshalb Herr Platter aus allen möglichen Schriften von Marx, vom
    <mark>Kommunistischen manifest</mark> bis zum <mark>dritten Bande des „Kapital“</mark>, alle mög¬
    lichen Zitate herauschleppt, aber um die Literatur der Internationalen in weitem
    Bogen herumgeht. Auch nicht mit einem Sterbenswörtchen erfahren die Leser
    seines Buches, daß es eine solche Literatur giebt. Und doch müßte ein Mann
    der Wissenschaft, der über Marx als Praktiker und Taktiker der Arbeiterfrage
    sprechen will, in allererster Reihe auf die Literatur der Internationalen zurück¬
    gehen. Wir reden hier nicht von den Zeilenreißern der bürgerlichen Tages= und
    Wochenpresse, die es halten mögen, wie sie wollen, aber ein Professor der Staats¬
    wissenschaften, der den praktischen Arbeiterpolitiker Marx kritisiren will, der muß
    so viel Royalität und so viele Kenntnisse besitzen, um diesen Politiker da zu
    suchen, wo er zu finden ist. Selbstverständlich hat Herr Platter aber seine guten
    Gründe, sich anzustellen, als gebe es keine Literatur der Internationalen. Denn
    wenn er sich dieser Literatur auch nur auf Kanonenschußweite nähern würde, so
    """
    mo.md(annotated_sample_page)
    return (annotated_sample_page,)


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Basic Prompt (zero-shot)
        Note querying with the full page of text is fairly slow.
        """
    )
    return


@app.cell
def _():
    # load prompt
    with open("prompts/title_mentions/basic.txt") as f0:
        basic_prompt = f0.read()
    print(basic_prompt)
    return basic_prompt, f0


@app.cell
def _(basic_prompt, sample_page, submit_prompt):
    # get response
    basic_response = submit_prompt(
        task_prompt=basic_prompt, user_prompt=sample_page
    )
    return (basic_response,)


@app.cell
def _(basic_response):
    print(basic_response)
    print()
    print(basic_response.choices[0].message.content)
    return


@app.cell
def _(basic_response, display_bracketed_response):
    display_bracketed_response(basic_response)
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## One-shot Prompt
        Trying adding an example to the prompt taken from a different volume than the sample page.
        """
    )
    return


@app.cell
def _():
    # load prompt
    with open("prompts/title_mentions/one_shot.txt") as f1:
        one_shot_prompt = f1.read()
    print(one_shot_prompt)
    return f1, one_shot_prompt


@app.cell
def _(one_shot_prompt, sample_page, submit_prompt):
    # get response
    one_shot_response = submit_prompt(
        task_prompt=one_shot_prompt, user_prompt=sample_page
    )
    return (one_shot_response,)


@app.cell
def _(one_shot_response):
    print(one_shot_response)
    print()
    print(one_shot_response.choices[0].message.content)
    return


@app.cell
def _(display_bracketed_response, one_shot_response):
    # Finds the texts of interest but does not include volume-level information.
    # Misses the additional speech (https://www.marxists.org/deutsch/archiv/marx-engels/1864/10/inaugadr.htm) in the first paragraph
    display_bracketed_response(one_shot_response)
    return


@app.cell
def _(mo):
    mo.md(
        """
        ## Switching to smaller text chunks
        Prompting with a full page appears to take a fairly long time (~30s), so explore response times for smaller chunks.

        **Results: Faster responses for smaller text chunks.**
        """
    )
    return


@app.cell
def _(sample_page):
    text_chunks = sample_page.split("\n\n")
    return (text_chunks,)


@app.cell
def _(basic_prompt, display_bracketed_response, submit_prompt, text_chunks):
    # Skipped speech
    display_bracketed_response(
        submit_prompt(task_prompt=basic_prompt, user_prompt=text_chunks[0])
    )
    return


@app.cell
def _(basic_prompt, display_bracketed_response, submit_prompt, text_chunks):
    display_bracketed_response(
        submit_prompt(task_prompt=basic_prompt, user_prompt=text_chunks[1])
    )
    return


@app.cell
def _(basic_prompt, display_bracketed_response, submit_prompt, text_chunks):
    # Skips volume information
    display_bracketed_response(
        submit_prompt(task_prompt=basic_prompt, user_prompt=text_chunks[2])
    )
    return


@app.cell
def _(basic_prompt, display_bracketed_response, submit_prompt, text_chunks):
    # Skips volume information
    display_bracketed_response(
        submit_prompt(task_prompt=basic_prompt, user_prompt=text_chunks[3])
    )
    return


@app.cell
def _(mo):
    mo.md(
        r"""
        ## Conclusions
        - Volume-level information is generally ignored.
        - Prompting to use square brackets for annotations appears to work, will be relatively easy to convert for viewing assuming the underlying text does not include square brackets.
        - Not clear that adding an example to the prompt helps.
        - The newer prompt template appears to take a lot more time, but it seems to be relative to the length of the input passage.
        - Annotations do not appear to be particularly stable between runs.
            - Spurious annotations may appear in passages without any title references
            - The speech written by Karl Marx is not necessarily identified
        """
    )
    return


if __name__ == "__main__":
    app.run()
