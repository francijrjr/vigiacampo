import { api } from "../models/api.js";

export async function baixar(caminho, nome) {
  const arquivo = await api(caminho, { arquivo: true });
  const url = URL.createObjectURL(arquivo);
  const link = document.createElement("a");
  link.href = url;
  link.download = nome;
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
