import test from "node:test";
import assert from "node:assert/strict";
import { buscarLocalizacao } from "../frontend/utils/geolocalizacao.js";

function simular() {
  const eventos = [], removidos = [];
  let receber, erro, expirar, opcoes;
  const cancelar = buscarLocalizacao({
    atualizar: (p) => eventos.push(["atualizar", p.coords.accuracy]),
    concluir: (p) => eventos.push(["concluir", p.coords.accuracy]),
    falhar: (e) => eventos.push(["erro", e.code]),
  }, {
    geolocation: {
      watchPosition: (sucesso, falha, config) => { receber = sucesso; erro = falha; opcoes = config; return 7; },
      clearWatch: (id) => removidos.push(id),
    },
    agendar: (callback, ms) => { assert.equal(ms, 20000); expirar = callback; return 8; },
    cancelar: (id) => assert.equal(id, 8),
    agora: () => 100000,
  });
  return { eventos, removidos, cancelar, erro, expirar, opcoes,
    posicao: (accuracy, extras = {}) => receber({ coords: { latitude: -3.73, longitude: -38.53, accuracy }, timestamp: 100000, ...extras }) };
}

test("refina a primeira estimativa e ignora leituras piores", () => {
  const s = simular();
  s.posicao(5000); s.posicao(8000); s.posicao(120); s.posicao(8);
  assert.deepEqual(s.eventos, [["atualizar", 5000], ["atualizar", 120], ["atualizar", 8], ["concluir", 8]]);
  assert.deepEqual(s.removidos, [7]);
  assert.deepEqual(s.opcoes, { enableHighAccuracy: true, timeout: 10000, maximumAge: 0 });
});
test("encerra uma estimativa imprecisa no limite de tempo", () => {
  const s = simular(); s.posicao(5000); s.expirar(); s.posicao(8);
  assert.deepEqual(s.eventos, [["atualizar", 5000], ["concluir", 5000]]);
  assert.deepEqual(s.removidos, [7]);
});
test("descarta localização antiga e coordenadas inválidas", () => {
  const s = simular();
  s.posicao(8, { timestamp: 1000 });
  s.posicao(NaN);
  s.posicao(8, { coords: { latitude: 100, longitude: 0, accuracy: 8 } });
  s.expirar();
  assert.deepEqual(s.eventos, [["erro", 3]]);
});
test("fechar cancela a busca e ignora callbacks tardios", () => {
  const s = simular(); s.cancelar(); s.posicao(8); s.erro({ code: 1 }); s.expirar();
  assert.deepEqual(s.eventos, []);
  assert.deepEqual(s.removidos, [7]);
});
test("permissão negada encerra imediatamente", () => {
  const s = simular(); s.erro({ code: 1 }); s.posicao(8);
  assert.deepEqual(s.eventos, [["erro", 1]]);
  assert.deepEqual(s.removidos, [7]);
});
test("indisponibilidade transitória permite recuperar a localização", () => {
  const s = simular(); s.erro({ code: 2 }); s.posicao(8);
  assert.deepEqual(s.eventos, [["atualizar", 8], ["concluir", 8]]);
});
