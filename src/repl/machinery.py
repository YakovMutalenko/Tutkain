import base64
import os
import sublime

from threading import Thread
from .session import Session
from . import formatter
from ..log import log


def done(response):
    return response.get("status") == ["done"]


def handle_sideloader_provide_response(session, response):
    if "status" in response and "unexpected-provide" in response["status"]:
        name = response["name"]
        session.output({"err": f"unexpected provide: {name}\n"})


def sideloader_provide(session, response):
    if "name" in response:
        name = response["name"]

        op = {
            "id": response["id"],
            "op": "sideloader-provide",
            "type": response["type"],
            "name": name,
        }

        path = os.path.join(sublime.packages_path(), "tutkain/clojure/src", name)

        if os.path.isfile(path):
            log.debug({"event": "sideloader/provide", "path": path})

            with open(path, "rb") as file:
                op["content"] = base64.b64encode(file.read()).decode("utf-8")
        else:
            op["content"] = ""

        session.send(
            op,
            handler=lambda response: handle_sideloader_provide_response(
                session, response
            ),
        )


def create_sessions(client, session, response):
    info = response
    session.info = info
    session.output(response)

    def create_session(owner, response):
        new_session_id = response["new-session"]
        new_session = Session(new_session_id, client)
        new_session.info = info
        client.register_session(owner, new_session)

    session.send(
        {"op": "clone", "session": session.id},
        handler=lambda response: done(response) and create_session("plugin", response),
    )

    session.send(
        {"op": "clone", "session": session.id},
        handler=lambda response: done(response) and create_session("user", response),
    )


def sideload(client, session):
    def describe():
        session.send(
            {"op": "describe"},
            handler=lambda response: done(response)
            and create_sessions(client, session, response),
        )

    def add_tap():
        session.send(
            {"op": "tutkain/add-tap"},
            handler=lambda response: done(response) and describe(),
        )

    def add_middleware():
        session.send(
            {
                "op": "add-middleware",
                "middleware": [
                    "tutkain.nrepl.middleware.test/wrap-test",
                    "tutkain.nrepl.middleware.tap/wrap-tap",
                ],
            },
            handler=lambda response: done(response) and add_tap(),
        )

    session.send(
        {"op": "sideloader-start"},
        handler=lambda response: sideloader_provide(session, response),
    )

    session.send(
        {"op": "eval", "code": """(require 'tutkain.nrepl.util.pprint)"""},
        pprint=False,
        handler=lambda response: done(response) and add_middleware(),
    )


def initialize_sessions(client, capabilities, response):
    session_id = response.get("new-session")
    session = Session(session_id, client)

    if "sideloader-start" in capabilities["ops"]:
        client.register_session("sideloader", session)
        sideload(client, session)
    else:
        client.register_session("plugin", session)
        session.info = capabilities
        session.output(capabilities)

        def register_user_session(response):
            session = Session(response["new-session"], client)
            session.info = capabilities
            client.register_session("user", session)

        client.send(
            {"op": "clone"},
            handler=lambda response: done(response) and register_user_session(response),
        )


def clone(client, response):
    capabilities = response

    client.send(
        {"op": "clone"},
        handler=lambda response: done(response)
        and initialize_sessions(client, capabilities, response),
    )


def start(client, printq, tapq):
    format_loop = Thread(
        daemon=True,
        target=formatter.format_loop,
        args=(client.recvq, printq, tapq),
    )

    format_loop.name = "tutkain.connection.format_loop"
    format_loop.start()

    client.send(
        {"op": "describe"},
        handler=lambda response: done(response)
        and clone(client, response),
    )
