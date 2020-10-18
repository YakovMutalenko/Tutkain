import base64
import os
import sublime

from threading import Thread
from .session import Session
from . import formatter
from . import printer
from ..log import log
from .. import state


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


def create_sessions(client, session, view, response):
    info = response
    session.info = info
    session.output(response)

    def create_session(owner, response):
        new_session_id = response["new-session"]
        new_session = Session(new_session_id, client)
        new_session.info = info
        state.set_session_view(new_session_id, view)
        client.register_session(owner, new_session)

    session.send(
        {"op": "clone", "session": session.id},
        handler=lambda response: done(response) and create_session("plugin", response),
    )

    session.send(
        {"op": "clone", "session": session.id},
        handler=lambda response: done(response) and create_session("user", response),
    )


def sideload(client, session, view):
    def describe():
        session.send(
            {"op": "describe"},
            handler=lambda response: done(response)
            and create_sessions(client, session, view, response),
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


def initialize_sessions(client, printq, view, capabilities, response):
    session_id = response.get("new-session")
    session = Session(session_id, client)
    state.set_session_view(session_id, view)

    if "sideloader-start" in capabilities["ops"]:
        client.register_session("sideloader", session)
        sideload(client, session, view)
    else:
        client.register_session("plugin", session)
        session.info = capabilities
        session.output(capabilities)

        def register_session(response):
            session = Session(response["new-session"], client)
            session.info = capabilities
            state.set_session_view(session.id, view)
            client.register_session("user", session)

        client.send(
            {"op": "clone"},
            handler=lambda response: done(response) and register_session(response),
        )


def clone(client, printq, view, response):
    capabilities = response

    client.send(
        {"op": "clone"},
        handler=lambda response: done(response)
        and initialize_sessions(client, printq, view, capabilities, response),
    )


def handshake(client, printq, view):
    client.send(
        {"op": "describe"},
        handler=lambda response: done(response) and clone(client, printq, view, response),
    )


def create_output_view(window, client):
    active_view = window.active_view()

    view_count = len(window.views_in_group(1))
    suffix = "" if view_count == 0 else f" ({view_count})"

    view = window.new_file()
    view.set_name(f"REPL | {client.host}:{client.port}{suffix}")
    view.settings().set("line_numbers", False)
    view.settings().set("gutter", False)
    view.settings().set("is_widget", True)
    view.settings().set("scroll_past_end", False)
    view.settings().set("tutkain_repl_output_view", True)
    view.set_read_only(True)
    view.set_scratch(True)

    view.assign_syntax("Clojure (Tutkain).sublime-syntax")

    # Move the output view into the second row.
    window.set_view_index(view, 1, view_count)

    # Activate the output view and the view that was active prior to
    # creating the output view.
    window.focus_view(view)
    window.focus_view(active_view)

    return view


def establish(window, client, printq):
    view = create_output_view(window, client)
    state.set_view_client(view, client)

    format_loop = Thread(daemon=True, target=formatter.format_loop, args=(window, client.recvq, printq,))
    format_loop.name = "tutkain.connection.format_loop"
    format_loop.start()

    handshake(client, printq, view)
