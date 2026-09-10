from sixgenbot.core.eventBus import EventBus


def test_delivers_to_everyone_listening():
    bus = EventBus()
    heard = []
    bus.subscribe("item.changed", lambda sku: heard.append(("a", sku)), owner="a")
    bus.subscribe("item.changed", lambda sku: heard.append(("b", sku)), owner="b")

    assert bus.emit("item.changed", sku="13-8 24") == 2
    assert heard == [("a", "13-8 24"), ("b", "13-8 24")]


def test_nobody_listening_is_not_an_error():
    assert EventBus().emit("nothing.cares") == 0


def test_one_broken_listener_does_not_stop_the_others():
    bus = EventBus()
    heard = []

    def broken(**_):
        raise RuntimeError("this listener is broken")

    bus.subscribe("sale.detected", broken, owner="broken")
    bus.subscribe("sale.detected", lambda **_: heard.append("ran"), owner="fine")

    assert bus.emit("sale.detected") == 1
    assert heard == ["ran"]


def test_reports_who_is_listening():
    bus = EventBus()
    bus.subscribe("sale.detected", lambda **_: None, owner="notifier")
    assert bus.listeners("sale.detected") == ["notifier"]
    assert bus.events == ["sale.detected"]
