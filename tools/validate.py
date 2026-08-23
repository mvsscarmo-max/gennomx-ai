#!/usr/bin/env python3
"""Entrypoint unico de validacao do Protocolo VLAEG IA-ready 4.0.

    python validate.py                       # o projeto que contem este arquivo
    python validate.py --root /caminho/proj  # QUALQUER projeto, de fora dele
    python validate.py --only skills
    python validate.py --currency            # + passagem de vigencia do estado
    python validate.py --json                # saida estruturada

Sem --root, a raiz e descoberta subindo ate o primeiro diretorio com AGENTS.md.
Com --root, valida o projeto apontado — e o modo de uso a partir do Kit, sem
instalar nada no projeto alvo.

Sai 0 quando nao ha erro, 1 quando ha. Validador vermelho impede declarar
trabalho concluido (docs/quality-gates.md).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import print_report, repo_root  # noqa: E402

import currency  # noqa: E402
import validate_ai_ready  # noqa: E402
import validate_coordination  # noqa: E402
import validate_links  # noqa: E402
import validate_skills  # noqa: E402
import validate_state  # noqa: E402
import validate_protocol  # noqa: E402
import verify  # noqa: E402

MODULES = {
    "ai-ready": validate_ai_ready,
    "coordination": validate_coordination,
    "skills": validate_skills,
    "state": validate_state,
    "links": validate_links,
    "g13": verify,
    "protocol": validate_protocol,
}


def main() -> int:
    # Windows cp1252 no console quebra inventário/avisos com setas e acentos (G11 R2).
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if callable(reconfigure):
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError, AttributeError):
                pass

    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--root", metavar="CAMINHO",
                    help="raiz do projeto a validar; sem isto, sobe ate achar AGENTS.md")
    ap.add_argument("--only", choices=sorted(MODULES), help="roda apenas um validador")
    ap.add_argument("--currency", action="store_true",
                    help="roda a passagem de vigencia (docs/state-currency.md)")
    ap.add_argument("--json", action="store_true", help="saida estruturada")
    ap.add_argument("--quiet", action="store_true", help="so o resumo por validador")
    args = ap.parse_args()

    if args.root:
        root = Path(args.root).expanduser().resolve()
        if not root.is_dir():
            ap.error(f"--root nao e um diretorio: {root}")
        if not (root / "AGENTS.md").is_file():
            # Falha cedo e com a causa nomeada: sem nucleo residente nao ha o que
            # validar, e um relatorio de 40 erros esconderia essa causa unica.
            print(f"ERRO: {root} nao tem AGENTS.md — nao e um projeto VLAEG IA-ready.",
                  file=sys.stderr)
            print("      Rode scripts/vlaeg_init.py para criar a estrutura minima,",
                  file=sys.stderr)
            print("      ou scripts/vlaeg_adopt.py para inventariar um projeto existente.",
                  file=sys.stderr)
            return 2
    else:
        root = repo_root()

    selected = {args.only: MODULES[args.only]} if args.only else MODULES

    reports = []
    if not args.json:
        print("Protocolo VLAEG IA-ready 4.0 — validacao")
        print(f"raiz: {root}\n")

    for name, mod in selected.items():
        rep = mod.run(root)
        reports.append(rep)
        if not args.json:
            print_report(rep, verbose=not args.quiet)

    if args.currency:
        if not args.json:
            print()
        rep = currency.run(root)
        reports.append(rep)
        if not args.json:
            print_report(rep, verbose=not args.quiet)
            if not args.quiet:
                print()
                print(currency.build_inventory(root, rep))

    total_err = sum(len(r.errors) for r in reports)
    total_warn = sum(len(r.warns) for r in reports)
    total_checks = sum(r.checked for r in reports)

    if args.json:
        print(json.dumps({
            "root": str(root),
            "checks": total_checks,
            "errors": total_err,
            "warnings": total_warn,
            "reports": [{"name": r.name, "checked": r.checked,
                         "issues": [i.as_dict() for i in r.issues]} for r in reports],
        }, ensure_ascii=False, indent=2))
        return 1 if total_err else 0

    print()
    print("=" * 72)
    if total_err:
        print(f"FALHOU — {total_err} erro(s), {total_warn} aviso(s) "
              f"em {total_checks} verificacoes.")
        print("Trabalho nao pode ser declarado concluido com validador vermelho.")
    else:
        print(f"OK — {total_checks} verificacoes, 0 erros, {total_warn} aviso(s).")
    print("=" * 72)
    return 1 if total_err else 0


if __name__ == "__main__":
    sys.exit(main())
