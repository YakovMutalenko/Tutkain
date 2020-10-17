from sublime import Region, DRAW_NO_OUTLINE
import uuid

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
        while True:
            item = printq.get()

            if item is None:
                break

            view = item.get("view")
            printable = item.get("printable")
            response = item.get("response")

            if response and view and "status" in response and "done" in response["status"]:
                view_size = view.size()
                last_char = view.substr(Region(view_size - 1, view_size))

                if last_char != "\n":
                    print("#!ASDASDASDAS", last_char.encode())
                    if printable is None:
                        printable = "\n"
                    else:
                        printable += "\n"

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
    finally:
        log.debug({"event": "thread/exit"})
