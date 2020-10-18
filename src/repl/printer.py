import uuid
from sublime import Region, DRAW_NO_OUTLINE
from ..log import log
from .. import state


def print_characters(view, characters):
    if characters is not None:
        view.run_command("append", {"characters": characters, "scroll_to_end": True})


def append_to_view(view, characters):
    if view and characters:
        view.set_read_only(False)
        print_characters(view, characters)
        view.set_read_only(True)
        view.run_command("move_to", {"to": "eof"})


def print_loop(printq):
    try:
        log.debug({'event': 'thread/start'})

        while True:
            item = printq.get()

            if item is None:
                break

            view = item.get("view")
            printable = item.get("printable")
            response = item.get("response")

            append_to_view(view, printable)

            if response and {"out", "err"} & response.keys():
                size = view.size()
                key = str(uuid.uuid4())
                regions = [Region(size - len(printable), size)]
                scope = (
                    "tutkain.repl.stderr"
                    if "err" in response
                    else "tutkain.repl.stdout"
                )
                view.add_regions(key, regions, scope=scope, flags=DRAW_NO_OUTLINE)

            # if "tap" in response and settings().get("tap_panel"):
            #     window = session.view.window()
            #     tap.show_panel(window, client)
            #     append_to_view(tap.find_panel(window, client), response["tap"])
    finally:
        # view = state.get_active_repl_view(window)

        # if view:
        #     append_to_view(view, ':tutkain/disconnected\n')

        log.debug({"event": "thread/exit"})
