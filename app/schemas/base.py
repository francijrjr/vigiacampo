from pydantic import BaseModel, ConfigDict, model_validator
import re


class DadosEntrada(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True, from_attributes=True, extra="forbid")

    @model_validator(mode="before")
    @classmethod
    def rejeitar_nulos_obrigatorios(cls, dados):
        if isinstance(dados, dict):
            dados = dict(dados)
            if "email" in dados and isinstance(dados["email"], str):
                dados["email"] = dados["email"].strip() or None
            limites = {"client_id":64, "municipio":100, "codigo_area":50, "ciclo":50, "zona":50,
                       "numero":20, "complemento":100, "logradouro":255, "lado":20, "especie":100,
                       "produto":100, "numero_amostra":50, "full_name":255, "email":255, "observacoes":10000}
            for campo, limite in limites.items():
                valor = dados.get(campo)
                if isinstance(valor, str) and len(valor) > limite:
                    raise ValueError(f"O campo {campo} deve ter no máximo {limite} caracteres")
            if dados.get("hora_entrada") and not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d", dados["hora_entrada"]):
                raise ValueError("Informe a hora no formato HH:MM")
            if dados.get("email") and not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", dados["email"]):
                raise ValueError("Informe um e-mail válido")
            obrigatorios = {"municipio", "codigo_area", "ciclo", "data", "atividade", "status", "concluido",
                            "numero", "tipo", "tipo_visita", "pendencia", "full_name", "is_active", "password"}
            for campo in obrigatorios.intersection(dados):
                if dados[campo] is None or isinstance(dados[campo], str) and not dados[campo].strip():
                    raise ValueError(f"O campo {campo} não pode ficar vazio")
        return dados
