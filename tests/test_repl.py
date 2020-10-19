import uuid
from .util import ReplTestCase


def select_keys(d, ks):
    return {k: d[k] for k in ks}


class TestBabashka(ReplTestCase):
    def handshake(self):
        # Client sends describe op
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server sends describe reply
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

        plugin_session_id = str(uuid.uuid4())

        self.srv.send(
            {
                "id": msg["id"],
                "new-session": plugin_session_id,
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

        self.assertEquals(
            "Babashka 0.2.2\nbabashka.nrepl 0.0.4-SNAPSHOT\n", self.take_print()
        )

        return plugin_session_id, user_session_id

    def test_eval(self):
        plugin_session_id, user_session_id = self.handshake()

        # Client evaluates (inc 1)
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")

        # # Server receives eval op
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

        self.assertEquals("user=> (inc 1)\n", self.take_print())
        self.assertEquals("2", self.take_print())
        # The eval response includes one empty reply.
        self.take_print()
        self.assertEquals("\n", self.take_print())


class TestArcadia(ReplTestCase):
    def handshake(self):
        # Client sends describe op
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server sends describe reply
        self.srv.send(
            {
                "id": msg["id"],
                "ops": {
                    "classpath": 1,
                    "clone": 1,
                    "complete": 1,
                    "describe": 1,
                    "eldoc": 1,
                    "eval": 1,
                    "info": 1,
                    "load-file": 1,
                },
                "session": "3a98c8e8-dc39-417d-9606-b8fa1ca17130",
                "status": ["done"],
                "versions": {
                    "clojure": {
                        "incremental": 0,
                        "major": 1,
                        "minor": 10,
                        "qualifier": "master",
                    },
                    "nrepl": {"incremental": 3, "major": 0, "minor": 2},
                },
            }
        )

        # Client initializes plugin session
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        plugin_session_id = str(uuid.uuid4())

        self.srv.send(
            {
                "id": msg["id"],
                "new-session": plugin_session_id,
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
                "status": ["done"],
            }
        )

        self.assertEquals("Clojure 1.10.0\nnREPL 0.2.3\n", self.take_print())

        return plugin_session_id, user_session_id

    def test_eval(self):
        plugin_session_id, user_session_id = self.handshake()

        # Client evaluates (inc 1)
        self.set_view_content("(inc 1)")
        self.set_selections((0, 0))
        self.view.run_command("tutkain_evaluate_form")

        # # Server receives eval op
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

        self.assertEquals("user=> (inc 1)\n", self.take_print())
        self.assertEquals("2", self.take_print())
        # The eval response includes one empty reply.
        self.take_print()
        self.assertEquals("\n", self.take_print())


class TestNetworkRepl(ReplTestCase):
    def handshake(self):
        # Client sends describe op
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server sends describe reply
        self.srv.send(
            {
                "aux": {"current-ns": "user"},
                "id": msg["id"],
                "ops": {
                    "add-middleware": {},
                    "clone": {},
                    "close": {},
                    "completions": {},
                    "describe": {},
                    "eval": {},
                    "interrupt": {},
                    "load-file": {},
                    "lookup": {},
                    "ls-middleware": {},
                    "ls-sessions": {},
                    "sideloader-provide": {},
                    "sideloader-start": {},
                    "stdin": {},
                    "swap-middleware": {},
                },
                "session": "7284b9a2-ce3d-4a59-8497-8f051cb999d8",
                "status": ["done"],
                "versions": {
                    "clojure": {
                        "incremental": 1,
                        "major": 1,
                        "minor": 10,
                        "version-string": "1.10.1",
                    },
                    "java": {
                        "incremental": "2",
                        "major": "11",
                        "minor": "0",
                        "version-string": "11.0.2",
                    },
                    "nrepl": {
                        "incremental": 3,
                        "major": 0,
                        "minor": 8,
                        "version-string": "0.8.3",
                    },
                },
            }
        )

        # Client initializes sideloader session
        msg = self.srv.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        sideloader_session_id = str(uuid.uuid4())

        self.srv.send(
            {
                "id": msg["id"],
                "new-session": sideloader_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals(
            {
                "id": 1,
                "op": "sideloader-start",
                "session": sideloader_session_id,
            },
            self.srv.recv(),
        )

        msg = self.srv.recv()

        self.assertEquals(
            {
                "op": "eval",
                "code": "(require 'tutkain.nrepl.util.pprint)",
                "session": sideloader_session_id,
            },
            select_keys(msg, {"op", "code", "session"}),
        )

    def test_eval(self):
        self.handshake()
