"""Fake broker for testing the merge + UI with zero credentials."""
from .base import Broker


class MockBroker(Broker):
    broker = "mock"

    def __init__(self, name, rows):
        self.name = name
        self._rows = rows

    def holdings(self):
        return self._rows

    def positions(self):
        return []
