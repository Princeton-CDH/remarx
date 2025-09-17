from remarx.app.ui import app


def test_app():
    # Check application does not crash when run programmatically
    app.run()
