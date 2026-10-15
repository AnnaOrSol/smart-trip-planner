"""Unit tests for batching without live HTTP calls."""

import unittest
from services.routing_matrix import fetch_route_matrix


class TestRoutingMatrix(unittest.TestCase):
    def setUp(self):
        self.calls = []

    def fake_post(self, url, json, headers, timeout):
        self.calls.append(json)
        class Response:
            def raise_for_status(self):
                pass
            def json(self):
                return {"sources_to_targets": [
                    [{"distance": abs(src["lat"] - dst["lat"]),
                      "time": abs(src["lat"] - dst["lat"]) * 60 + 1}
                     for dst in json["targets"]]
                    for src in json["sources"]
                ]}
        return Response()

    def test_batches_reconstruct_complete_matrix(self):
        coords = [(float(i), 0.0) for i in range(16)]
        distances, times = fetch_route_matrix(
            coords, "pedestrian", self.fake_post, "test-url", 8
        )
        self.assertEqual(len(self.calls), 4)
        self.assertTrue(all(len(c["sources"]) * len(c["targets"]) <= 64
                            for c in self.calls))
        self.assertEqual(distances[0][15], 15.0)
        self.assertEqual(distances[15][0], 15.0)
        self.assertEqual(times[0][15], 16)
        self.assertEqual(times[7][8], 2)

    def test_partial_batches(self):
        coords = [(float(i), 0.0) for i in range(10)]
        distances, _ = fetch_route_matrix(
            coords, "auto", self.fake_post, "test-url", 8
        )
        self.assertEqual(len(self.calls), 4)
        self.assertEqual(distances[9][1], 8.0)

    def test_invalid_dimensions(self):
        def bad_post(*args, **kwargs):
            class Response:
                def raise_for_status(self):
                    pass
                def json(self):
                    return {"sources_to_targets": []}
            return Response()
        with self.assertRaisesRegex(ValueError, "dimensions"):
            fetch_route_matrix([(0, 0)], "auto", bad_post, "url")

    def test_empty_matrix(self):
        self.assertEqual(fetch_route_matrix([], "auto", self.fake_post, "url"), ([], []))
        self.assertEqual(self.calls, [])


if __name__ == "__main__":
    unittest.main()
