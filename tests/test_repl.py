import sublime
import uuid

from inspect import cleandoc
from .util import ReplTestCase
from Tutkain.src.repl import b64encode_file


ROOT = sublime.packages_path()


def select_keys(d, ks):
    return {k: d[k] for k in ks}


class TestBabashka(ReplTestCase):
    def handshake(self):
        repl = self.start_repl()

        # Client sends describe op
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server sends describe reply
        self.server.send(
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
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        plugin_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": plugin_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        # Client initializes user session
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        user_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": user_session_id,
                "session": "none",
                "status": ["done"],
            }
        )

        self.assertEquals(
            "Babashka 0.2.2\nbabashka.nrepl 0.0.4-SNAPSHOT\n", repl.take_print()
        )

        return repl, plugin_session_id, user_session_id

    def test_eval(self):
        repl, plugin_session_id, user_session_id = self.handshake()

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
            select_keys(self.server.recv(), {"op", "code", "ns", "session", "id"}),
        )

        # Server sends eval responses
        self.server.send(
            {
                "id": 1,
                "ns": "user",
                "session": user_session_id,
                "value": "2",
            }
        )

        self.server.send({"id": 1, "ns": "user", "session": user_session_id})

        self.server.send(
            {
                "id": 1,
                "session": user_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals("user=> (inc 1)\n", repl.take_print())
        self.assertEquals("2", repl.take_print())
        self.assertEquals("\n", repl.take_print())


class TestArcadia(ReplTestCase):
    def handshake(self):
        repl = self.start_repl()

        # Client sends describe op
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server sends describe reply
        self.server.send(
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
                "session": str(uuid.uuid4()),
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
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        plugin_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": plugin_session_id,
                "status": ["done"],
            }
        )

        # Client initializes user session
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        user_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": user_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals("Clojure 1.10.0\nnREPL 0.2.3\n", repl.take_print())

        return repl, plugin_session_id, user_session_id

    def test_eval(self):
        repl, plugin_session_id, user_session_id = self.handshake()

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
            select_keys(self.server.recv(), {"op", "code", "ns", "session", "id"}),
        )

        # Server sends eval responses
        self.server.send(
            {
                "id": 1,
                "ns": "user",
                "session": user_session_id,
                "value": "2",
            }
        )

        # Not sure why Babashka sends this empty response
        self.server.send({"id": 1, "ns": "user", "session": user_session_id})

        self.server.send(
            {
                "id": 1,
                "session": user_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals("user=> (inc 1)\n", repl.take_print())
        self.assertEquals("2", repl.take_print())
        self.assertEquals("\n", repl.take_print())


class TestDefault(ReplTestCase):
    def test_sideloading_handshake(self):
        repl = self.start_repl()

        # Client sends describe op.
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        # Server sends describe reply.
        self.server.send(
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
                "session": str(uuid.uuid4()),
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

        # Client initializes sideloader session.
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        sideloader_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # Client sends sideloader-start.
        self.assertEquals(
            {
                "id": 1,
                "op": "sideloader-start",
                "session": sideloader_session_id,
            },
            self.server.recv(),
        )

        # Client requires pprint namespace.
        self.assertEquals(
            {
                "op": "eval",
                "id": 2,
                "code": "(require 'tutkain.nrepl.util.pprint)",
                "session": sideloader_session_id,
            },
            select_keys(self.server.recv(), {"op", "id", "code", "session"}),
        )

        # Server can't find the pprint namespace, requests it from the client.
        self.server.send(
            {
                "id": 1,
                "name": "tutkain/nrepl/util/pprint__init.class",
                "session": sideloader_session_id,
                "status": ["sideloader-lookup"],
                "type": "resource",
            }
        )

        # Client doesn't have the .class file, sends an empty response.
        self.assertEquals(
            {
                "id": 3,
                "op": "sideloader-provide",
                "type": "resource",
                "name": "tutkain/nrepl/util/pprint__init.class",
                "content": "",
                "session": sideloader_session_id,
            },
            self.server.recv(),
        )

        # Server acknowledges the empty response.
        self.server.send(
            {
                "id": 3,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # Server requests a .clj file.
        self.server.send(
            {
                "id": 1,
                "name": "tutkain/nrepl/util/pprint.clj",
                "session": sideloader_session_id,
                "status": ["sideloader-lookup"],
                "type": "resource",
            }
        )

        # Client has it, sends it.
        self.assertEquals(
            {
                "id": 4,
                "op": "sideloader-provide",
                "type": "resource",
                "name": "tutkain/nrepl/util/pprint.clj",
                "content": b64encode_file(
                    f"{ROOT}/Tutkain/clojure/src/tutkain/nrepl/util/pprint.clj"
                ),
                "session": sideloader_session_id,
            },
            self.server.recv(),
        )

        # Server acknoledges the provide.
        self.server.send(
            {
                "id": 4,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # The request that required the pprint namespace is done.
        #
        # We'll ignore sideloading Fipp here.
        self.server.send({"id": 2, "session": sideloader_session_id, "value": "nil"})
        self.server.send({"id": 2, "ns": "user", "session": sideloader_session_id})
        self.server.send(
            {"id": 2, "session": sideloader_session_id, "status": ["done"]}
        )

        # Client asks server to add middleware.
        self.assertEquals(
            {
                "op": "add-middleware",
                "middleware": [
                    "tutkain.nrepl.middleware.test/wrap-test",
                    "tutkain.nrepl.middleware.tap/wrap-tap",
                ],
                "session": sideloader_session_id,
                "id": 5,
            },
            self.server.recv(),
        )

        # Server doesn't have the middleware, asks the client for it.
        self.server.send(
            {
                "id": 1,
                "name": "tutkain/nrepl/middleware/test__init.class",
                "session": sideloader_session_id,
                "status": ["sideloader-lookup"],
                "type": "resource",
            }
        )

        # Client doesn't have the .class file, sends an empty response.
        self.assertEquals(
            {
                "id": 6,
                "op": "sideloader-provide",
                "type": "resource",
                "name": "tutkain/nrepl/middleware/test__init.class",
                "content": "",
                "session": sideloader_session_id,
            },
            self.server.recv(),
        )

        # Server asks the client for the .clj file.
        self.server.send(
            {
                "id": 1,
                "name": "tutkain/nrepl/middleware/test.clj",
                "session": sideloader_session_id,
                "status": ["sideloader-lookup"],
                "type": "resource",
            }
        )

        # Client has the class file, sends it to the server
        self.assertEquals(
            {
                "id": 7,
                "op": "sideloader-provide",
                "type": "resource",
                "name": "tutkain/nrepl/middleware/test.clj",
                "content": b64encode_file(
                    f"{ROOT}/Tutkain/clojure/src/tutkain/nrepl/middleware/test.clj"
                ),
                "session": sideloader_session_id,
            },
            self.server.recv(),
        )

        # Server acknoledges the provide.
        self.server.send(
            {
                "id": 7,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # Server tells the client there's nothing more to sideload.
        self.server.send(
            {
                "id": 5,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # Client sends tutkain/add-tap.
        self.assertEquals(
            {"id": 8, "op": "tutkain/add-tap", "session": sideloader_session_id},
            self.server.recv(),
        )

        # Server acknowledges the request.
        self.server.send(
            {
                "id": 8,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals(
            {"id": 9, "op": "describe", "session": sideloader_session_id},
            self.server.recv(),
        )

        self.server.send(
            {
                "aux": {"current-ns": "user"},
                "id": 9,
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
                    "tutkain/add-tap": {},
                    "tutkain/test": {},
                },
                "session": sideloader_session_id,
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

        # Clone plugin session
        msg = self.server.recv()
        self.assertEquals({"op", "session", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        plugin_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": plugin_session_id,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # Clone user session
        msg = self.server.recv()
        self.assertEquals({"op", "session", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        user_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": user_session_id,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals("Clojure 1.10.1\nnREPL 0.8.3\n", repl.take_print())

    def handshake(self):
        repl = self.start_repl()

        # Client sends describe op.
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("describe", msg["op"])

        describe = {
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
                "tutkain/add-tap": {},
                "tutkain/test": {},
            },
            "session": str(uuid.uuid4()),
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

        # Server responds, telling the client everything is already sideloaded.
        self.server.send(describe)

        # Clone plugin session
        msg = self.server.recv()
        self.assertEquals({"op", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        sideloader_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": sideloader_session_id,
                "session": str(uuid.uuid4()),
                "status": ["done"],
            }
        )

        # Client sends sideloader-start.
        self.assertEquals(
            {
                "id": 1,
                "op": "sideloader-start",
                "session": sideloader_session_id,
            },
            self.server.recv(),
        )

        # Client requires pprint namespace.
        self.assertEquals(
            {
                "op": "eval",
                "id": 2,
                "code": "(require 'tutkain.nrepl.util.pprint)",
                "session": sideloader_session_id,
            },
            select_keys(self.server.recv(), {"op", "id", "code", "session"}),
        )

        self.send_eval_responses(sideloader_session_id, 2, "user", "nil")

        # Client asks server to add middleware.
        self.assertEquals(
            {
                "op": "add-middleware",
                "middleware": [
                    "tutkain.nrepl.middleware.test/wrap-test",
                    "tutkain.nrepl.middleware.tap/wrap-tap",
                ],
                "session": sideloader_session_id,
                "id": 3,
            },
            self.server.recv(),
        )

        self.server.send(
            {
                "id": 3,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals(
            {
                "op": "tutkain/add-tap",
                "session": sideloader_session_id,
                "id": 4,
            },
            self.server.recv(),
        )

        self.server.send(
            {
                "id": 4,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals(
            {
                "op": "describe",
                "session": sideloader_session_id,
                "id": 5,
            },
            self.server.recv(),
        )

        describe["id"] = 5
        describe["session"] = sideloader_session_id
        self.server.send(describe)

        # Clone plugin session
        msg = self.server.recv()
        self.assertEquals({"op", "session", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        plugin_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": plugin_session_id,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        # Clone user session
        msg = self.server.recv()
        self.assertEquals({"op", "session", "id"}, msg.keys())
        self.assertEquals("clone", msg["op"])

        user_session_id = str(uuid.uuid4())

        self.server.send(
            {
                "id": msg["id"],
                "new-session": user_session_id,
                "session": sideloader_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals("Clojure 1.10.1\nnREPL 0.8.3\n", repl.take_print())

        return repl, plugin_session_id, user_session_id

    def test_evaluate_form(self):
        repl, plugin_session_id, user_session_id = self.handshake()

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
            select_keys(self.server.recv(), {"op", "code", "ns", "session", "id"}),
        )

        # Server sends eval responses
        self.server.send(
            {
                "id": 1,
                "ns": "user",
                "session": user_session_id,
                "value": "2",
            }
        )

        self.server.send({"id": 1, "ns": "user", "session": user_session_id})

        self.server.send(
            {
                "id": 1,
                "session": user_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals("user=> (inc 1)\n", repl.take_print())
        self.assertEquals("2", repl.take_print())
        self.assertEquals("\n", repl.take_print())

    def test_evaluate_view(self):
        repl, plugin_session_id, user_session_id = self.handshake()

        self.set_view_content(
            "(ns app.core) (defn square [x] (* x x)) (comment (square 2))"
        )

        self.view.run_command("tutkain_evaluate_view")

        self.assertEquals(
            {
                "op": "load-file",
                "file": "(ns app.core) (defn square [x] (* x x)) (comment (square 2))",
                "session": plugin_session_id,
                "id": 1,
            },
            self.server.recv(),
        )

        self.server.send(
            {
                "id": 1,
                "ns": "user",
                "session": plugin_session_id,
                "value": "nil",
            }
        )

        self.server.send(
            {
                "id": 1,
                "session": plugin_session_id,
                "status": ["done"],
            }
        )

        self.assertEquals(":tutkain/loaded", repl.take_print())
        self.assertEquals("\n", repl.take_print())

    def test_evaluate_form_before_view(self):
        repl, plugin_session_id, user_session_id = self.handshake()

        self.set_view_content(
            cleandoc(
                """
            (ns my.ns (:require [clojure.set :as set]))

            (defn x [y z] (set/subset? y z))

            (comment
              (x #{1} #{1 2}))
            """
            )
        )

        self.set_selections((45, 45))
        self.view.run_command("tutkain_evaluate_form")

        self.assertEquals(
            {
                "op": "eval",
                "code": "(defn x [y z] (set/subset? y z))",
                "ns": "my.ns",
                "session": user_session_id,
                "id": 1,
            },
            select_keys(self.server.recv(), {"op", "code", "ns", "session", "id"}),
        )

        # Server can't find namespace.
        self.server.send(
            {
                "id": 1,
                "ns": "my.ns",
                "session": user_session_id,
                "status": ["namespace-not-found", "done", "error"],
            }
        )

        # This is an nREPL bug: it sends to "done" responses when it can't find the namespace the
        # user sends.
        self.server.send(
            {
                "id": 1,
                "ns": "my.ns",
                "session": user_session_id,
                "status": ["done"],
            }
        )

        # Client evaluates ns form.
        self.assertEquals(
            {
                "op": "eval",
                "code": "(ns my.ns (:require [clojure.set :as set]))",
                "session": user_session_id,
                "id": 2,
            },
            select_keys(self.server.recv(), {"op", "code", "session", "id"}),
        )

        self.server.send({"id": 2, "session": user_session_id, "value": "nil"})
        self.server.send({"id": 2, "ns": "my.ns", "session": user_session_id})
        self.server.send({"id": 2, "session": user_session_id, "status": ["done"]})

        # Client retries sending the original form.
        self.assertEquals(
            {
                "op": "eval",
                "code": "(defn x [y z] (set/subset? y z))",
                "ns": "my.ns",
                "session": user_session_id,
                "id": 3,
            },
            select_keys(self.server.recv(), {"op", "code", "ns", "session", "id"}),
        )

        self.send_eval_responses(user_session_id, 3, "my.ns", "#'my.ns/x\n")

        self.assertEquals(
            [
                "my.ns=> (defn x [y z] (set/subset? y z))\n",
                "\n",  # This is the extraneous "done" response.
                "#'my.ns/x",
                "\n",
            ],
            repl.take_prints(4),
        )
