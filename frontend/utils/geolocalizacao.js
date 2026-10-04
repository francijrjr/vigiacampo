// Busca limitada no tempo: aproveita leituras melhores sem rastrear continuamente.
export function buscarLocalizacao({ atualizar, concluir, falhar }, {
  geolocation = navigator.geolocation,
  agendar = setTimeout,
  cancelar = clearTimeout,
  agora = Date.now,
} = {}) {
  let encerrado = false, melhor, observador;
  const limite = agendar(() => finalizar(), 20000);
  function parar() {
    if (encerrado) return;
    encerrado = true;
    cancelar(limite);
    if (observador !== undefined) geolocation.clearWatch(observador);
  }
  function finalizar(erro) {
    if (encerrado) return;
    parar();
    if (melhor) concluir(melhor);
    else falhar(erro || { code: 3 });
  }
  try {
    observador = geolocation.watchPosition((posicao) => {
      if (encerrado) return;
      const { latitude, longitude, accuracy } = posicao.coords;
      if (![latitude, longitude, accuracy, posicao.timestamp].every(Number.isFinite)
        || Math.abs(latitude) > 90 || Math.abs(longitude) > 180 || accuracy < 0
        || agora() - posicao.timestamp > 30000) return;
      if (melhor && accuracy >= melhor.coords.accuracy) return;
      melhor = posicao;
      atualizar(posicao);
      if (accuracy <= 50) finalizar();
    }, (erro) => {
      if (encerrado) return;
      // Permissão negada é definitiva; timeout/indisponibilidade podem ser transitórios.
      if (erro.code === 1) finalizar(erro);
    }, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
    if (encerrado) geolocation.clearWatch(observador);
  } catch (erro) {
    finalizar(erro);
  }
  return parar;
}
