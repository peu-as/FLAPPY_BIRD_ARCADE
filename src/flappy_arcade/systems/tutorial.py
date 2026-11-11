"""Dicas de tutorial já vistas (seção "tutorial" do save)."""


class RegistroDicas:
    def __init__(self, save):
        self._save = save

    @property
    def _vistas(self):
        secao = self._save.section('tutorial')
        if not isinstance(secao.get('vistas'), list):
            secao['vistas'] = []
        return secao['vistas']

    def vista(self, ident):
        return ident in self._vistas

    def marcar(self, ident):
        if ident not in self._vistas:
            self._vistas.append(ident)
            self._save.save()
