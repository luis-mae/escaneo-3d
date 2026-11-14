import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from tools.cola_persistente import ColaPersistente
from tools.resultados_aislados import preparar, publicar, PublicacionRechazada


class ResultadosAisladosTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.cola = ColaPersistente(self.base / "cola.sqlite")
        self.id = "a" * 32
        self.cola.agregar(self.id, "owner")

    def tearDown(self):
        self.tmp.cleanup()

    def test_publicacion_lease_vigente(self):
        _, token = self.cola.reclamar_con_token("w")
        carpeta = preparar(self.base, self.id, token)
        (carpeta / "malla.obj").write_text("v 0 0 0\n")
        salida = publicar(self.base, self.id, "w", token, self.cola)
        self.assertEqual((salida / "malla.obj").read_text(), "v 0 0 0\n")

    def test_rechaza_lease_vencido(self):
        with patch("tools.cola_persistente.time.time", return_value=100):
            _, token = self.cola.reclamar_con_token("w", segundos_lease=10)
        preparar(self.base, self.id, token)
        with patch("time.time", return_value=111):
            with self.assertRaises(PublicacionRechazada):
                publicar(self.base, self.id, "w", token, self.cola)

    def test_rechaza_directorio_de_publicacion_enlace_simbolico(self):
        _, token = self.cola.reclamar_con_token("w")
        carpeta = preparar(self.base, self.id, token)
        (carpeta / "malla.obj").write_text("malla")
        externo = self.base / "externo"
        externo.mkdir()
        publicados = self.base / "publicados"
        publicados.mkdir()
        (publicados / self.id).symlink_to(externo, target_is_directory=True)
        with self.assertRaises(PublicacionRechazada):
            publicar(self.base, self.id, "w", token, self.cola)
        self.assertTrue(carpeta.exists())
        self.assertFalse((externo / "resultado").exists())

    def test_rechaza_traversal(self):
        with self.assertRaises(ValueError):
            preparar(self.base, "../salida", "b" * 32)

    def test_no_sobrescribe_resultado(self):
        _, token = self.cola.reclamar_con_token("w")
        preparar(self.base, self.id, token)
        publicar(self.base, self.id, "w", token, self.cola)
        preparar(self.base, self.id, "b" * 32)
        with self.assertRaises(FileExistsError):
            publicar(self.base, self.id, "w", "b" * 32, self.cola)


if __name__ == "__main__":
    unittest.main()
