export const hoje = () => {
  const data = new Date();
  const ano = data.getFullYear();
  const mes = String(data.getMonth() + 1).padStart(2, "0");
  const dia = String(data.getDate()).padStart(2, "0");
  return `${ano}-${mes}-${dia}`;
};
export const dataBr = (valor) =>
  valor ? new Date(`${valor}T12:00:00`).toLocaleDateString("pt-BR") : "—";
