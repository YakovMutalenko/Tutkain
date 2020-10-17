from ..log import log
from sublime import DRAW_NO_OUTLINE, Region

def format(response):
    if "status" in response and "interrupted" in response["status"]:
        return ":tutkain/interrupted\n"
    if "status" in response and "session-idle" in response["status"]:
        return ":tutkain/nothing-to-interrupt\n"
    if "value" in response:
        return response["value"].replace("\r", "")
    if "summary" in response:
        return response["summary"] + "\n"
    if "tap" in response:
        return response["tap"]
    if "nrepl.middleware.caught/throwable" in response:
        return response["nrepl.middleware.caught/throwable"]
    if "out" in response:
        return response["out"]
    if "in" in response:
        ns = response.get("ns") or ""
        return "{}=> {}\n".format(ns, response["in"])
    if "err" in response:
        return response.get("err")
    if "versions" in response:
        result = []

        versions = response.get("versions")

        clojure_version = versions.get("clojure")
        nrepl_version = versions.get("nrepl")
        babashka_version = versions.get("babashka")

        if clojure_version:
            major = clojure_version.get("major")
            minor = clojure_version.get("minor")
            incremental = clojure_version.get("incremental")
            result.append(f"""Clojure {major}.{minor}.{incremental}""")
        elif babashka_version:
            result.append(f"""Babashka {babashka_version}""")
            result.append(f"""babashka.nrepl {versions.get("babashka.nrepl")}""")

        if nrepl_version:
            major = nrepl_version.get("major")
            minor = nrepl_version.get("minor")
            incremental = nrepl_version.get("incremental")
            result.append(f"""nREPL {major}.{minor}.{incremental}""")

        return "\n".join(result)


def format_loop(window, client, printq):
    try:
        log.debug({"event": "thread/start"})

        while True:
            response = client.recvq.get()

            if response is None:
                break

            # if "tap" in response and settings().get("tap_panel"):
            #     window = session.view.window()
            #     tap.show_panel(window, client)
            #     append_to_view(tap.find_panel(window, client), response["tap"])

            log.debug({"event": "fmtq/recv", "data": response})

            session = client.sessions.get(response.get("session"))

            if session:
                view = session.view
            else:
                view = state.get_active_repl_view(window)

            printq.put({"view": view, "printable": format(response), "response": response})
    finally:
        printq.put({"view": view, "printable": ":tutkain/disconnected\n"})
        printq.put(None)
        log.debug({"event": "thread/exit"})
