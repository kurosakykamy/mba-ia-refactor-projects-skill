from config.settings import Settings


def validar_produto(dados):
    erros = []

    if "nome" not in dados:
        erros.append("Nome é obrigatório")
    elif len(dados["nome"]) < 2:
        erros.append("Nome muito curto")
    elif len(dados["nome"]) > 200:
        erros.append("Nome muito longo")

    if "preco" not in dados:
        erros.append("Preço é obrigatório")
    else:
        try:
            if float(dados["preco"]) < 0:
                erros.append("Preço não pode ser negativo")
        except (TypeError, ValueError):
            erros.append("Preço deve ser numérico")

    if "estoque" not in dados:
        erros.append("Estoque é obrigatório")
    else:
        try:
            if int(dados["estoque"]) < 0:
                erros.append("Estoque não pode ser negativo")
        except (TypeError, ValueError):
            erros.append("Estoque deve ser numérico")

    categoria = dados.get("categoria", "geral")
    if categoria not in Settings.CATEGORIAS_VALIDAS:
        erros.append(f"Categoria inválida. Válidas: {Settings.CATEGORIAS_VALIDAS}")

    return erros
