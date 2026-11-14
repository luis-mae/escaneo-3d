import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from tools.verificar_manifiesto import verificar_manifiesto


class TestVerificarManifiesto(TestCase):
    def test_integridad_y_cambios(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fotos = root / 'fotos'
            fotos.mkdir()
            img = fotos / 'foto.jpg'
            img.write_bytes(b'foto-original')
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'schema_version': 1, 'imagenes': [
                {'archivo': 'foto.jpg', 'sha256': hashlib.sha256(img.read_bytes()).hexdigest(), 'bytes': img.stat().st_size}]}))
            self.assertEqual(verificar_manifiesto(manifest, fotos)['estado'], 'integro')
            img.write_bytes(b'foto-cambiada')
            self.assertEqual(verificar_manifiesto(manifest, fotos)['archivos'][0]['estado'], 'modificado')
            img.unlink()
            self.assertEqual(verificar_manifiesto(manifest, fotos)['archivos'][0]['estado'], 'faltante')

    def test_bloquea_rutas_externas(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            manifest = root / 'manifest.json'
            manifest.write_text(json.dumps({'schema_version': 1, 'imagenes': [{'archivo': '../secreto'}]}))
            with self.assertRaises(ValueError):
                verificar_manifiesto(manifest, root)
