import queue
import re
import sublime
import time

from . import mock
from Tutkain.src import state
from Tutkain.src.repl.client import Client
from Tutkain.src import repl

from unittest import TestCase


def wait_until(pred, delay=0.25, retries=50):
    retries_left = retries

    while retries_left >= 0:
        if pred():
            return True
        else:
            time.sleep(delay)
            retries_left -= 1

    return False


def wait_until_equals(a, b, delay=0.25, retries=50):
    return wait_until(lambda: a == b(), delay, retries)


def wait_until_matches(a, b, delay=0.25, retries=50):
    return wait_until(lambda: re.search(a, b()), delay, retries)


def wait_until_contains(a, b, delay=0.25, retries=50):
    def f():
        x = b()
        return x and a in x

    return wait_until(f, delay, retries)


class ViewTestCase(TestCase):
    @classmethod
    def setUpClass(self):
        sublime.run_command("new_window")
        self.view = sublime.active_window().new_file()
        self.view.set_name("tutkain.clj")
        self.view.set_scratch(True)
        self.view.sel().clear()
        self.view.window().focus_view(self.view)
        self.view.assign_syntax("Clojure (Tutkain).sublime-syntax")

    @classmethod
    def tearDownClass(self):
        if self.view:
            self.view.window().run_command("close_window")

    def setUp(self):
        self.clear_view()

    def content(self, view):
        return view and view.substr(sublime.Region(0, view.size()))

    def view_content(self):
        return self.content(self.view)

    def clear_view(self):
        self.view.run_command("select_all")
        self.view.run_command("right_delete")

    def set_view_content(self, chars):
        self.clear_view()
        self.view.run_command("append", {"characters": chars})

    def set_selections(self, *pairs):
        self.view.sel().clear()

        for begin, end in pairs:
            self.view.sel().add(sublime.Region(begin, end))

    def selections(self):
        return [(region.begin(), region.end()) for region in self.view.sel()]

    def selection(self, i):
        return self.view.substr(self.view.sel()[i])

    def assertEqualsEventually(self, a, b):
        if not wait_until_equals(a, b):
            raise AssertionError(f"'{a}' != '{b()}'")

    def assertMatchesEventually(self, a, b):
        if not wait_until_matches(a, b):
            raise AssertionError(f"'{a}' does not match '{b()}'")

    def assertContainsEventually(self, a, b):
        if not wait_until_contains(a, b):
            raise AssertionError(f"'{a}' does not contain '{b()}'")


class Repl():
    def __init__(self, window, host, port):
        client = Client(host, port).go()

        self.printq = queue.Queue()
        self.tapq = queue.Queue()

        self.view = repl.views.create(window, client)

        state.set_view_client(self.view, client)
        state.set_active_repl_view(self.view)

        repl.machinery.start(client, self.printq, self.tapq)

    def take_print(self):
        return self.printq.get(timeout=1)["printable"]

    def take_prints(self, n):
        xs = []

        for _ in range(n):
            xs.append(self.take_print())

        return xs

    def take_tap(self):
        return self.tapq.get(timeout=1)


class ReplTestCase(ViewTestCase):
    def start_repl(self):
        return Repl(self.view.window(), self.server.host, self.server.port)

    def setUp(self):
        super().setUp()
        self.server = mock.Server()

    def tearDown(self):
        self.server.shutdown()
        self.view.window().run_command("tutkain_disconnect")
        super().tearDown()

    def send_eval_responses(self, session_id, id, ns, value):
        self.server.send({"id": id, "session": session_id, "value": value})
        self.server.send({"id": id, "ns": ns, "session": session_id})
        self.server.send({"id": id, "session": session_id, "status": ["done"]})
