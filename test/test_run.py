from src.mainwindow import Application
from src.textconfig import TextConfigureApp


def test_run_Application(tk_root):
    app = Application(master=tk_root)
    app.update()
    app.destroy()


def test_run_TextConfigureApp(tk_root):
    app = TextConfigureApp(master=tk_root)
    app.update()
    app.destroy()
