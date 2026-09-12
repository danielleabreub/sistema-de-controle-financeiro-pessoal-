#!/usr/bin/env python3
"""
Sistema de Controle Financeiro Pessoal
========================================
CLI em Python puro (sem dependências externas) para gerenciar receitas e
despesas, categorias, saldo e relatórios mensais.

Os dados são persistidos em um arquivo JSON local (financas.json).

Como usar:
    python controle_financeiro.py
"""

import json
import os
from datetime import datetime
from collections import defaultdict

ARQUIVO_DADOS = "financas.json"


# ---------------------------------------------------------------------------
# Persistência
# ---------------------------------------------------------------------------

def carregar_dados():
    """Carrega os dados do arquivo JSON. Cria estrutura vazia se não existir."""
    if os.path.exists(ARQUIVO_DADOS):
        with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                print("Aviso: arquivo de dados corrompido. Iniciando um novo.")
    return {"transacoes": [], "proximo_id": 1}


def salvar_dados(dados):
    """Salva os dados no arquivo JSON."""
    with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Funções principais
# ---------------------------------------------------------------------------

CATEGORIAS_RECEITA = ["Salário", "Freelance", "Investimentos", "Presente", "Outros"]
CATEGORIAS_DESPESA = [
    "Alimentação", "Moradia", "Transporte", "Saúde",
    "Educação", "Lazer", "Assinaturas", "Outros"
]


def escolher_categoria(tipo):
    categorias = CATEGORIAS_RECEITA if tipo == "receita" else CATEGORIAS_DESPESA
    print("\nCategorias disponíveis:")
    for i, cat in enumerate(categorias, 1):
        print(f"  {i}. {cat}")
    while True:
        escolha = input("Escolha o número da categoria: ").strip()
        if escolha.isdigit() and 1 <= int(escolha) <= len(categorias):
            return categorias[int(escolha) - 1]
        print("Opção inválida. Tente novamente.")


def ler_valor(mensagem):
    while True:
        valor_str = input(mensagem).strip().replace(",", ".")
        try:
            valor = float(valor_str)
            if valor <= 0:
                print("O valor deve ser maior que zero.")
                continue
            return round(valor, 2)
        except ValueError:
            print("Valor inválido. Digite apenas números (ex: 150.50).")


def ler_data():
    hoje = datetime.now().strftime("%d/%m/%Y")
    data_str = input(f"Data (dd/mm/aaaa) [Enter para hoje, {hoje}]: ").strip()
    if not data_str:
        return hoje
    try:
        datetime.strptime(data_str, "%d/%m/%Y")
        return data_str
    except ValueError:
        print("Data inválida. Usando a data de hoje.")
        return hoje


def adicionar_transacao(dados, tipo):
    print(f"\n--- Nova {tipo} ---")
    descricao = input("Descrição: ").strip() or "Sem descrição"
    valor = ler_valor("Valor: R$ ")
    categoria = escolher_categoria(tipo)
    data = ler_data()

    transacao = {
        "id": dados["proximo_id"],
        "tipo": tipo,
        "descricao": descricao,
        "valor": valor,
        "categoria": categoria,
        "data": data,
    }
    dados["transacoes"].append(transacao)
    dados["proximo_id"] += 1
    salvar_dados(dados)
    print(f"\n{tipo.capitalize()} de R$ {valor:.2f} registrada com sucesso!")


def listar_transacoes(dados, filtro_mes=None):
    transacoes = dados["transacoes"]
    if filtro_mes:
        transacoes = [t for t in transacoes if t["data"][3:] == filtro_mes]

    if not transacoes:
        print("\nNenhuma transação encontrada.")
        return

    transacoes_ordenadas = sorted(
        transacoes, key=lambda t: datetime.strptime(t["data"], "%d/%m/%Y")
    )

    print(f"\n{'ID':<5}{'Data':<12}{'Tipo':<10}{'Categoria':<15}{'Descrição':<25}{'Valor':>12}")
    print("-" * 79)
    for t in transacoes_ordenadas:
        sinal = "+" if t["tipo"] == "receita" else "-"
        print(
            f"{t['id']:<5}{t['data']:<12}{t['tipo']:<10}{t['categoria']:<15}"
            f"{t['descricao'][:24]:<25}{sinal}R$ {t['valor']:>8.2f}"
        )


def remover_transacao(dados):
    listar_transacoes(dados)
    id_str = input("\nDigite o ID da transação a remover (ou Enter para cancelar): ").strip()
    if not id_str:
        return
    if not id_str.isdigit():
        print("ID inválido.")
        return
    id_alvo = int(id_str)
    tamanho_antes = len(dados["transacoes"])
    dados["transacoes"] = [t for t in dados["transacoes"] if t["id"] != id_alvo]
    if len(dados["transacoes"]) < tamanho_antes:
        salvar_dados(dados)
        print("Transação removida com sucesso!")
    else:
        print("Transação não encontrada.")


def calcular_saldo(dados):
    receitas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "receita")
    despesas = sum(t["valor"] for t in dados["transacoes"] if t["tipo"] == "despesa")
    return receitas, despesas, receitas - despesas


def exibir_resumo(dados):
    receitas, despesas, saldo = calcular_saldo(dados)
    print("\n=== Resumo Geral ===")
    print(f"Total de receitas: R$ {receitas:.2f}")
    print(f"Total de despesas: R$ {despesas:.2f}")
    sinal = "" if saldo >= 0 else "-"
    print(f"Saldo atual:       {sinal}R$ {abs(saldo):.2f}")
    if saldo < 0:
        print("Atenção: suas despesas estão maiores que suas receitas!")


def relatorio_por_categoria(dados, tipo):
    transacoes = [t for t in dados["transacoes"] if t["tipo"] == tipo]
    if not transacoes:
        print(f"\nNenhuma {tipo} registrada ainda.")
        return

    totais = defaultdict(float)
    for t in transacoes:
        totais[t["categoria"]] += t["valor"]

    total_geral = sum(totais.values())
    print(f"\n=== {tipo.capitalize()}s por categoria ===")
    for categoria, valor in sorted(totais.items(), key=lambda x: -x[1]):
        percentual = (valor / total_geral) * 100 if total_geral else 0
        barra = "█" * int(percentual // 4)
        print(f"{categoria:<15} R$ {valor:>10.2f}  ({percentual:5.1f}%) {barra}")
    print(f"{'TOTAL':<15} R$ {total_geral:>10.2f}")


def relatorio_mensal(dados):
    mes = input("Digite o mês/ano (mm/aaaa): ").strip()
    if len(mes) != 7 or mes[2] != "/":
        print("Formato inválido. Use mm/aaaa (ex: 09/2026).")
        return

    transacoes_mes = [t for t in dados["transacoes"] if t["data"][3:] == mes]
    if not transacoes_mes:
        print(f"\nNenhuma transação encontrada para {mes}.")
        return

    receitas = sum(t["valor"] for t in transacoes_mes if t["tipo"] == "receita")
    despesas = sum(t["valor"] for t in transacoes_mes if t["tipo"] == "despesa")

    print(f"\n=== Relatório de {mes} ===")
    listar_transacoes(dados, filtro_mes=mes)
    print(f"\nReceitas do mês: R$ {receitas:.2f}")
    print(f"Despesas do mês: R$ {despesas:.2f}")
    print(f"Saldo do mês:    R$ {receitas - despesas:.2f}")


# ---------------------------------------------------------------------------
# Menu principal
# ---------------------------------------------------------------------------

def exibir_menu():
    print("\n" + "=" * 40)
    print("   SISTEMA DE CONTROLE FINANCEIRO")
    print("=" * 40)
    print("1. Adicionar receita")
    print("2. Adicionar despesa")
    print("3. Listar todas as transações")
    print("4. Remover transação")
    print("5. Ver saldo e resumo geral")
    print("6. Relatório de despesas por categoria")
    print("7. Relatório de receitas por categoria")
    print("8. Relatório mensal")
    print("0. Sair")
    print("=" * 40)


def main():
    dados = carregar_dados()

    while True:
        exibir_menu()
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            adicionar_transacao(dados, "receita")
        elif opcao == "2":
            adicionar_transacao(dados, "despesa")
        elif opcao == "3":
            listar_transacoes(dados)
        elif opcao == "4":
            remover_transacao(dados)
        elif opcao == "5":
            exibir_resumo(dados)
        elif opcao == "6":
            relatorio_por_categoria(dados, "despesa")
        elif opcao == "7":
            relatorio_por_categoria(dados, "receita")
        elif opcao == "8":
            relatorio_mensal(dados)
        elif opcao == "0":
            print("\nAté logo! Seus dados foram salvos em", ARQUIVO_DADOS)
            break
        else:
            print("Opção inválida. Tente novamente.")

        input("\nPressione Enter para continuar...")


if __name__ == "__main__":
    main()
