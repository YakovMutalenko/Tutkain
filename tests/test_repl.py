from inspect import cleandoc
import io
import sublime
import time

from . import mock
from .util import ViewTestCase
from Tutkain import package as tutkain


class TestBabashka(ViewTestCase):
    @classmethod
    def setUpClass(self):
        self.srv = mock.Server()
        super().setUpClass()

    @classmethod
    def tearDownClass(self):
        self.srv.shutdown()
        self.view.window().run_command("tutkain_disconnect")
        super().tearDownClass()

    def active_repl_view_content(self):
        view = tutkain.get_active_repl_view(self.view.window())

        if view:
            return view.substr(sublime.Region(0, view.size()))

    def test_smoke(self):
        self.view.window().run_command(
            "tutkain_connect", {"host": self.srv.host, "port": self.srv.port}
        )

        # Client sends describe op
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server responds to describe
        self.srv.send(
            {
                "id": msg["id"],
                "ops": {
                    "clone": {},
                    "close": {},
                    "complete": {},
                    "describe": {},
                    "eldoc": {},
                    "eval": {},
                    "load-file": {},
                    "ls-sessions": {},
                },
                "session": "none",
                "status": ["done"],
                "versions": {"babashka": "0.2.2", "babashka.nrepl": "0.0.4-SNAPSHOT"},
            }
        )

        # Client initializes plugin session
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        self.srv.send(
            {
                "id": msg["id"],
                "new-session": "fad4be68-6bca-4469-820e-47cecbc064a5",
                "session": "none",
                "status": ["done"],
            }
        )

        # Client initializes user session
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        self.assertEqualsEventually(
            """Babashka 0.2.2
babashka.nrepl 0.0.4-SNAPSHOT\n""",
            self.active_repl_view_content
        )

        # Client evaluates (inc 1)
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")

        time.sleep(5)

        # msg = self.srv.recv()
        # self.assertEquals({}, msg)
