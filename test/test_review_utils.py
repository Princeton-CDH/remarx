from remarx.review_utils import get_span_indices

page_text = """Nachdem Marx im ersten Bande des „Kapital“, Kapitel X, das Gesetz,
des Mehrwerths festgestellt hatte, fügte er sogleich hinzu, „daß dies Gesetz offenbar,
aller auf den Augenschein gegründeten Erfahrung widerspricht". „Zur Lösung
dieses Widerspruchs" fährt er fort, „bedarf es noch vieler Mittelglieder.“ Er
versprach, diese Lösung später zu geben."""

sample = """Nachdem Marx im ersten Bande des „Kapital“, Kapitel X, das Gesetz,
des Mehrwerths festgestellt hatte"""


page_text_2 = """der nach ihrer Ansicht die Theorie zu Falle bringen mußte. Mehrere hofften, daß der Theore¬ tiker des Werthes dort mit seiner Dialektik und seinem Kommumnismus scheitern. werde, denen, wie sie überzeugt waren, jede wissenschaftliche Grundlage fehle. Herr Loria, der geniale Entdecker so mancher schon von Marx entdeckten Theorien, ging so weit, zu behaupten, daß derselbe, um seine Ohumacht nicht einzugestehen, sich entschlossen hätte, die beiden Bände, welche sein ökonomisches"""
sample_2 = """die Theorie zu Falle bringen mußte. Mehrere hofften, daß der Theore¬
werker des Werthes dort mit sei"""


def test_get_span_indices():
    start, end = get_span_indices(page_text, sample)
    assert start == 0
    assert end == 100
    assert page_text[start:end] == sample

    start, end = get_span_indices(page_text_2, sample_2)
    assert start == 23
    # doesn't match exactly!
    # assert page_text_2[start:end] == sample_2
