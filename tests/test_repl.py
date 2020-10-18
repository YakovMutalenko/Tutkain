import queue
import uuid

from . import mock
from .util import ViewTestCase
from Tutkain.src.repl.client import Client
from Tutkain.src.repl import connection


def select_keys(d, ks):
    return {k: d[k] for k in ks}


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

    def test_smoke(self):
        client = Client(self.srv.host, self.srv.port).go()
        printq = queue.Queue()
        connection.establish(self.view.window(), client, printq)
        printable = lambda: printq.get(timeout=1)["printable"]

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
                "new-session": str(uuid.uuid4()),
                "session": "none",
                "status": ["done"],
            }
        )

        # Client initializes user session
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])
        user_session_id = str(uuid.uuid4())

        self.srv.send(
            {
                "id": msg["id"],
                "new-session": user_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        self.assertEquals("Babashka 0.2.2\nbabashka.nrepl 0.0.4-SNAPSHOT\n", printable())

        # Client evaluates (inc 1)
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")

        # Server receives eval op
        self.assertEquals(
            {
                "op": "eval",
                "code": "(inc 1)",
                "ns": "user",
                "session": user_session_id,
                "id": 1,
            },
            select_keys(self.srv.recv(), {"op", "code", "ns", "session", "id"}),
        )

        # Server sends eval responses
        self.srv.send(
            {
                "id": 1,
                "ns": "user",
                "session": "a215e204-7c1e-479b-b86d-38ac7845f12c",
                "value": "2",
            }
        )

        # Not sure why Babashka sends this empty response
        self.srv.send(
            {"id": 1, "ns": "user", "session": "a215e204-7c1e-479b-b86d-38ac7845f12c"}
        )

        self.srv.send(
            {
                "id": 1,
                "session": "a215e204-7c1e-479b-b86d-38ac7845f12c",
                "status": ["done"],
            }
        )

        self.assertEquals("user=> (inc 1)\n", printable())
        self.assertEquals("2\n", printable())
