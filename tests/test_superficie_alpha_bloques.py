"""Regression tests for chunked alpha-shape construction."""
import unittest
import numpy as np
from tools.superficie_concava import superficie_alpha


class AlphaShapeChunkedTests(unittest.TestCase):
    def test_tetrahedron_large_alpha(self):
        points = np.array([[0., 0., 0.], [1., 0., 0.],
                           [0., 1., 0.], [0., 0., 1.]])
        vertices, faces, accepted = superficie_alpha(points, 2.0)
        self.assertEqual(len(vertices), 4)
        self.assertEqual(accepted, 1)
        self.assertEqual(len(faces), 4)
        self.assertEqual(len({tuple(sorted(face)) for face in faces}), 4)

    def test_tetrahedron_small_alpha(self):
        points = np.array([[0., 0., 0.], [1., 0., 0.],
                           [0., 1., 0.], [0., 0., 1.]])
        _, faces, accepted = superficie_alpha(points, 0.01)
        self.assertEqual(accepted, 0)
        self.assertEqual(len(faces), 0)

    def test_large_cloud_exercises_multiple_batches(self):
        rng = np.random.default_rng(19)
        points = rng.uniform(-1, 1, (900, 3))
        vertices, faces, accepted = superficie_alpha(points, 0.5)
        self.assertGreater(accepted, 0)
        self.assertGreater(len(faces), 0)
        self.assertTrue(np.isfinite(vertices).all())

    def test_rejects_invalid_alpha(self):
        points = np.eye(4, 3)
        for alpha in (0, -1, float("nan")):
            with self.assertRaises(ValueError):
                superficie_alpha(points, alpha)


if __name__ == "__main__":
    unittest.main()
