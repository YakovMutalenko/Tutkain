from sublime import Region, DRAW_NO_OUTLINE
import uuid

from .. import formatter
from ..log import log


def print_characters(view, characters):
    if characters is not None:
        view.run_command("append", {"characters": characters, "scroll_to_end": True})


def append_to_view(view, characters):
    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def print_response(view, response):
    if view:
        if {
            "value",
            "nrepl.middleware.caught/throwable",
            "in",
            "versions",
            "summary",
        } & response.keys():
            append_to_view(view, formatter.format(response))
        elif "status" in response and "interrupted" in response["status"]:
            append_to_view(view, ":tutkain/interrupted\n")
        elif "status" in response and "session-idle" in response["status"]:
            append_to_view(view, ":tutkain/nothing-to-interrupt\n")
        else:
            characters = formatter.format(response)

            if characters:
                append_to_view(view, characters)

                size = view.size()
                key = str(uuid.uuid4())
                regions = [Region(size - len(characters), size)]
                scope = (
                    "tutkain.repl.stderr"
                    if "err" in response
                    else "tutkain.repl.stdout"
                )

                view.add_regions(key, regions, scope=scope, flags=DRAW_NO_OUTLINE)


def print_loop(client):
    try:
        while True:
            response = client.recvq.get()

            if response is None:
                break

            log.debug({"event": "printer/recv", "data": response})

            session = client.sessions.get(response.get("session"))

            if "tap" in response and settings().get("tap_panel"):
                window = session.view.window()
                tap.show_panel(window, client)
                append_to_view(tap.find_panel(window, client), response["tap"])
            elif session:
                print_response(session.view, response)

                view_size = session.view.size()

                if "status" in response and "done" in response["status"]:
                    last_char = session.view.substr(Region(view_size - 1, view_size))

                    if not last_char == "\n":
                        append_to_view(session.view, "\n")
            else:
                view = get_active_repl_view(session.view.window())
                print_response(view, response)
    finally:
        log.debug({"event": "thread/exit"})
