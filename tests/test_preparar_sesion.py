import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from tools.preparar_sesion import preparar_sesion


class TestPrepararSesion(unittest.TestCase):
    def test_manifest_y_huella(self):
        with tempfile.TemporaryDirectory() as t:
            base = Path(t)
            fotos = base / 'fotos'
            fotos.mkdir()
            (fotos / 'uno.jpg').write_bytes(b'foto de prueba')
            destino = base / 'resultado' / 'manifest.json'
            with patch('tools.preparar_sesion.seleccionar', return_value={'seleccionadas': ['uno.jpg'], 'descartadas': []}):
                data = preparar_sesion(fotos, destino, min_fotos=2)
            self.assertEqual(data['estado'], 'requiere_revision')
            self.assertEqual(len(data['imagenes'][0]['sha256']), 64)
            self.assertEqual(json.loads(destino.read_text())['schema_version'], 1)

    def test_destino_dentro_de_fotos_rechazado(self):
        with tempfile.TemporaryDirectory() as t:
            carpeta = Path(t)
            with self.assertRaises(ValueError):
                preparar_sesion(carpeta, carpeta / 'manifest.json')


if __name__ == '__main__':
    unittest.main()
