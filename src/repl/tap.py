def panel_name(window, client):
    return client and f"tutkain.{client.id()}"


def find_panel(window, client):
    name = panel_name(window, client)
    return name and window.find_output_panel(name)


def show_panel(window, client):
    name = panel_name(window, client)
    name and window.run_command("show_panel", {"panel": f"output.{name}"})

def create_panel(window, client):
    if not find_panel(window, client):
        name = panel_name(window, client)
        panel = window.create_output_panel(name)
        panel.settings().set("line_numbers", False)
        panel.settings().set("gutter", False)
        panel.settings().set("is_widget", True)
        panel.settings().set("scroll_past_end", False)
        panel.assign_syntax("Clojure (Tutkain).sublime-syntax")
