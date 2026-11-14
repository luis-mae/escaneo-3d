import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from tools.reconstruir_sesion import ejecutar


class SesionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.fotos = self.base / 'fotos'
        self.fotos.mkdir()
        entradas = []
        for nombre in ['a.jpg', 'b.jpg', 'c.jpg']:
            path = self.fotos / nombre
            path.write_bytes(nombre.encode())
            entradas.append({'archivo': nombre, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
        self.manifest = self.base / 'manifest.json'
        self.manifest.write_text(json.dumps({'imagenes': entradas}))

    def test_genera_pares_y_ply(self):
        def fake(a, b, focal):
            return {'estado': 'experimental', 'aceptados': 1, 'puntos': [[1, 2, 3]]}
        out = self.base / 'out'
        result = ejecutar(self.manifest, self.fotos, out, 800, fake)
        self.assertEqual(result['pares_con_nube'], 2)
        self.assertTrue((out / 'par_001.ply').exists())
        self.assertTrue((out / 'informe.json').exists())

    def test_rechaza_imagen_modificada(self):
        (self.fotos / 'a.jpg').write_bytes(b'cambio')
        with self.assertRaisesRegex(ValueError, 'cambió'):
            ejecutar(self.manifest, self.fotos, self.base / 'out', 800)

    def test_error_parcial_no_interrumpe(self):
        def fake(a, b, focal):
            if a.name == 'a.jpg':
                raise ValueError('par fallido')
            return {'estado': 'insuficiente', 'motivo': 'sin textura'}
        result = ejecutar(self.manifest, self.fotos, self.base / 'out', 800, fake)
        self.assertEqual([p['estado'] for p in result['pares']], ['error', 'insuficiente'])

    def test_rechaza_salida_en_fotos(self):
        with self.assertRaisesRegex(ValueError, 'fuera'):
            ejecutar(self.manifest, self.fotos, self.fotos / 'out', 800)

    def test_rechaza_focal_invalida(self):
        with self.assertRaises(ValueError):
            ejecutar(self.manifest, self.fotos, self.base / 'out', 0)


if __name__ == '__main__':
    unittest.main()
