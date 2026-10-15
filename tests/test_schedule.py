import unittest
from ui.schedule import build_schedule


class TestSchedule(unittest.TestCase):
    def test_waiting_and_return(self):
        route, visits = build_schedule(
            [0, 1, 0], [[0, 10], [10, 0]], [0, 30],
            [(0, 1440), (600, 700)], 540
        )
        self.assertEqual(route, [(0, 540), (1, 600), (0, 640)])
        self.assertEqual(visits[0]["wait"], 50)
