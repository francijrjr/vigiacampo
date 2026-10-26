// Mantém casas anexas junto ao número principal: 100, 100 A, 100 B, 101.
function partesDoNumero(valor) {
  const texto = String(valor || "").trim().toLocaleUpperCase("pt-BR");
  const encontrado = texto.match(/^(\d+)(?:\s*[-/]?\s*(.*))?$/);
  if (!encontrado) return [Number.MAX_SAFE_INTEGER, texto, texto];
  return [Number(encontrado[1]), encontrado[2] ? "1" : "0", encontrado[2] || ""];
}

export function ordenarImoveisPorNumero(imoveis) {
  return [...imoveis].sort((primeiro, segundo) => {
    const a = partesDoNumero(primeiro.numero);
    const b = partesDoNumero(segundo.numero);
    for (let indice = 0; indice < a.length; indice += 1) {
      const comparacao = typeof a[indice] === "number"
        ? a[indice] - b[indice]
        : a[indice].localeCompare(b[indice], "pt-BR", { numeric: true });
      if (comparacao) return comparacao;
    }
    return (primeiro.id || 0) - (segundo.id || 0);
  });
}
