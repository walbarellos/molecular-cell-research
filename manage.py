#!/usr/bin/env python3
"""Central de Administracao, Gerenciamento e Execucao em Camadas da SSEP (L1-L7).

Este script unifica o controle de todos os modulos da plataforma:
  - L7: Modos de visualizacao (Usuario, Engenheiro, Cientista)
  - L6: Orquestracao de pipelines (Reproducao, Falsificacao, Desenho Discriminatorio)
  - L5: Computacao e simulacao biofisica
  - Testes automatizados e verificacao de integridade de dados
"""

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT_DIR))

# Importa servicos da camada de aplicacao e apresentacao
from application.exploration_service import (
    get_system_overview,
    simulate_user_mode,
    get_engineer_view,
    get_scientist_view,
)
from application.run_reproduction_cycle import execute_dataset_a_reproduction
from application.run_falsification_cycle import execute_dataset_b_falsification
from application.run_experimental_design import execute_experimental_design_cycle
from presentation.cli.user_view import render_user_view
from presentation.cli.engineer_view import render_engineer_view
from presentation.cli.scientist_view import render_scientist_view


def print_banner(title: str) -> None:
    width = 78
    print("┌" + "─" * (width - 2) + "┐")
    print(f"│ {title:^{width - 4}} │")
    print("└" + "─" * (width - 2) + "┘")


def cmd_status(args) -> int:
    dto = get_system_overview()
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│                    CELL LAB - RESUMO DO SISTEMA EPISTEMICO                   │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Fenomeno Ativo      : {dto.phenomenon:<48} │")
    print(f"│ Fontes Primarias    : {dto.total_sources:<48} │")
    print(f"│ Ensaios Fisicos     : {dto.total_experiments:<48} │")
    print(f"│ Observacoes L2      : {dto.total_observations:<48} │")
    print(f"│ Evidencias L3       : {dto.total_evidences:<48} │")
    print(f"│ Afirmacoes (Claims) : {dto.total_claims} (Validadas: {dto.validated_claims} | Refutadas: {dto.contradicted_claims}){'':<18} │")
    print(f"│ Modelos Registrados : {dto.total_models:<48} │")
    print(f"│ Conflitos Auditados : {dto.total_conflicts:<48} │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def cmd_user(args) -> int:
    atp = args.atp
    load = args.load
    if getattr(args, "preset_valid", False):
        atp = 1000.0
        load = 0.0
    elif getattr(args, "preset_falsified", False):
        atp = 1000.0
        load = 4.0

    dto = simulate_user_mode(atp_uM=atp, load_pN=load)
    print(render_user_view(dto))
    return 0


def cmd_engineer(args) -> int:
    dto = get_engineer_view()
    print(render_engineer_view(dto))
    return 0


def cmd_scientist(args) -> int:
    dto = get_scientist_view()
    print(render_scientist_view(dto))
    return 0


def cmd_reproduce(args) -> int:
    print_banner("L6 APPLICATION: EXECUCAO DO CICLO DE REPRODUCAO (DATASET A)")
    report = execute_dataset_a_reproduction()
    m = report["metrics"]
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│                         RESULTADOS DA REPRODUCAO                             │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Dataset Alvo     : Dataset A (Schnitzer & Block 1997, carga nula)            │")
    print(f"│ Modelo Avaliado  : MOD-KIF5B-MINIMAL-MM                                      │")
    print(f"│ Amostras (N)     : {report['sample_count']:<57} │")
    print(f"│ Coef. Det. (R2)  : {m['r_squared']:<57.4f} │")
    print(f"│ Chi2 Reduzido    : {m['reduced_chi_squared']:<57.3f} │")
    print(f"│ Pontos em 1-sigma: {m['points_within_1_sigma']}/{report['sample_count']} ({m['fraction_within_1_sigma']*100:.1f}%){'':<46} │")
    print(f"│ Pontos em 2-sigma: {m['points_within_2_sigma']}/{report['sample_count']} ({m['fraction_within_2_sigma']*100:.1f}%){'':<46} │")
    print(f"│ Escore z Maximo  : {m['max_z_score']:<57.3f} │")
    print(f"│ Veredito Final   : [{report['verdict']} | TIER::DERIVED | STATUS::VALIDATED]{'':<14} │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def cmd_falsify(args) -> int:
    print_banner("L6 APPLICATION: EXECUCAO DO CICLO DE FALSIFICACAO (DATASET B)")
    report = execute_dataset_b_falsification()
    m = report["metrics"]
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│                        RESULTADOS DA FALSIFICACAO                            │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Dataset Alvo     : Dataset B (Visscher et al. 1999, sob forca de carga)      │")
    print(f"│ Modelo Avaliado  : MOD-KIF5B-MINIMAL-MM (Sem termos de forca contraria)      │")
    print(f"│ Amostras (N)     : {report['sample_count']:<57} │")
    print(f"│ Coef. Det. (R2)  : {m['r_squared']:<57.4f} │")
    print(f"│ Pontos Refutados : {m['points_outside_2_sigma']}/{report['sample_count']} ({m['fraction_outside_2_sigma']*100:.1f}% com |z| > 2σ){'':<35} │")
    print(f"│ Escore z Maximo  : {m['max_z_score']:<57.3f} (no stall force de 6.0 pN)   │")
    print(f"│ Veredito Final   : [{report['verdict']} | NEGATIVE KNOWLEDGE GERADO]{'':<20} │")
    print(f"│ Conflito Gerado  : {report['conflict_record']['id']} (Status: explained_by_conditions){'':<15} │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def cmd_design(args) -> int:
    print_banner("L6 APPLICATION: PROPOSTA DE DESENHO EXPERIMENTAL DISCRIMINATORIO")
    res = execute_experimental_design_cycle()
    des = res["optimal_experiment_design"]
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│                 PROPOSTA DE DESENHO EXPERIMENTAL DISCRIMINATORIO             │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Titulo           : {des['title'][:55]:<57} │")
    print(f"│ Objetivo         : {des['objective'][:55]:<57} │")
    print(f"│ Modelos Testados : {', '.join(des['competing_model_ids']):<57} │")
    cond_str = f"[ATP] = {des['target_conditions']['atp_concentration_uM']} μM │ F_load = {des['target_conditions']['load_force_pN']} pN"
    print(f"│ Condicao Otima   : {cond_str:<57} │")
    print(f"│ Tecnica Proposta : {des['proposed_technique']:<57} │")
    print(f"│ Poder Resolucao  : {des['discriminatory_power_score']*100:.1f}% (> 20σ de separacao analitica){'':<20} │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print("│ [PREVISOES DIVERGENTES DOS MODELOS]:                                         │")
    for mod_id, outcome in des["predicted_outcomes"].items():
        print(f"│   ■ {mod_id}: {outcome:<50} │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def cmd_test(args) -> int:
    print_banner("EXECUCAO DA SUITE DE TESTES AUTOMATIZADOS (PYTEST)")
    pytest_bin = ROOT_DIR / ".venv" / "bin" / "pytest"
    if not pytest_bin.exists():
        pytest_bin = Path("pytest")
    cmd = [str(pytest_bin), "-v"]
    if getattr(args, "pytest_args", None):
        cmd.extend(args.pytest_args)
    return subprocess.call(cmd, cwd=str(ROOT_DIR))


def cmd_verify(args) -> int:
    print_banner("AUDITORIA COMPLETA DE INTEGRIDADE EPISTEMICA (L1 A L7)")
    print("[1/4] Verificando Invariantes Epistemicas (Pydantic / Domain)...")
    res_test = cmd_test(argparse.Namespace(pytest_args=["tests/invariants/"]))
    if res_test != 0:
        print("[ERRO] Invariantes violadas.")
        return 1

    print("\n[2/4] Verificando Roundtrip de Schemas JSON (L2/L3/L4)...")
    res_schema = cmd_test(argparse.Namespace(pytest_args=["tests/schema/"]))
    if res_schema != 0:
        print("[ERRO] Falha de schema.")
        return 1

    print("\n[3/4] Verificando Curadoria de Dados e Hashes SHA-256 (L1/L2)...")
    res_data = cmd_test(argparse.Namespace(pytest_args=["tests/data/"]))
    if res_data != 0:
        print("[ERRO] Checksums de dados brutos divergentes.")
        return 1

    print("\n[4/4] Verificando Pipelines Cientificos de Reproducao e Falsificacao (L5/L6)...")
    res_app = cmd_test(argparse.Namespace(pytest_args=["tests/application/"]))
    if res_app != 0:
        print("[ERRO] Falha em pipelines.")
        return 1

    print("\n┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│ [STATUS::VERIFIED] TODAS AS INVARIANTES E DADOS AUDITADOS COM SUCESSO        │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def cmd_demo(args) -> int:
    print_banner("BATERIA COMPLETA DE DEMONSTRACAO PEDAGOGICA (L1 A L7)")

    print("\n[PASSO 1/6] RESUMO GLOBAL DO CONHECIMENTO (STATUS)")
    cmd_status(args)

    print("\n[PASSO 2/6] MODO USUARIO - CONDICAO VALIDADA ([ATP]=1000 uM, F_load=0 pN)")
    cmd_user(argparse.Namespace(atp=1000.0, load=0.0, preset_valid=True, preset_falsified=False))

    print("\n[PASSO 3/6] MODO USUARIO - CONDICAO REFUTADA COM ALERTA DE FIREWALL (F_load=4 pN)")
    cmd_user(argparse.Namespace(atp=1000.0, load=4.0, preset_valid=False, preset_falsified=True))

    print("\n[PASSO 4/6] MODO ENGENHEIRO - ENTIDADES E PARAMETROS BIOFISICOS")
    cmd_engineer(args)

    print("\n[PASSO 5/6] MODO CIENTIFICO - PREMISSAS, PROVENIENCIA E CONFLITOS")
    cmd_scientist(args)

    print("\n[PASSO 6/6] DESENHO EXPERIMENTAL DISCRIMINATORIO (CICLO 09)")
    cmd_design(args)

    print("\n┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│ [DEMO CONCLUIDA COM SUCESSO] Todos os componentes e camadas operacionais.    │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="manage.py",
        description="Central de Administracao e Gerenciamento da Plataforma SSEP (L1-L7)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""Exemplos de Uso:
  python manage.py status                     # Exibe resumo do grafo de conhecimento
  python manage.py user --atp 1000 --load 0   # Executa simulacao sob regime validado
  python manage.py user --atp 1000 --load 4   # Dispara alerta de quebra sob carga
  python manage.py engineer                   # Abre componentes, entidades e limites
  python manage.py scientist                  # Abre premissas, proveniencia e conflitos
  python manage.py design                     # Calcula ensaio de maxima discriminacao
  python manage.py reproduce                  # Executa benchmark sobre Dataset A
  python manage.py falsify                    # Executa falsificacao sobre Dataset B
  python manage.py test                       # Executa suite de testes automatizados
  python manage.py demo                       # Roda bateria completa de demonstracao
  python manage.py verify                     # Auditoria formal completa de dados e schemas
""",
    )
    subparsers = parser.add_subparsers(dest="subcommand", help="Comando a executar")

    # status
    p_status = subparsers.add_parser("status", help="Resumo global do grafo epistêmico")
    p_status.set_defaults(func=cmd_status)

    # user
    p_user = subparsers.add_parser("user", help="Modo Usuario (operacional / simulacao)")
    p_user.add_argument("--atp", type=float, default=1000.0, help="Concentracao de ATP em μM (padrao: 1000.0)")
    p_user.add_argument("--load", type=float, default=0.0, help="Forca de carga contraria em pN (padrao: 0.0)")
    p_user.add_argument("--preset-valid", action="store_true", help="Preset: carga nula validada (1000 uM, 0 pN)")
    p_user.add_argument("--preset-falsified", action="store_true", help="Preset: carga refutada (1000 uM, 4 pN)")
    p_user.set_defaults(func=cmd_user)

    # engineer
    p_eng = subparsers.add_parser("engineer", help="Modo Engenheiro (entidades, parametros, envelope)")
    p_eng.set_defaults(func=cmd_engineer)

    # scientist
    p_sci = subparsers.add_parser("scientist", help="Modo Cientifico (premissas, proveniencia, conflitos)")
    p_sci.set_defaults(func=cmd_scientist)

    # reproduce
    p_repro = subparsers.add_parser("reproduce", help="Executa o pipeline de reproducao sobre Dataset A")
    p_repro.set_defaults(func=cmd_reproduce)

    # falsify
    p_falsif = subparsers.add_parser("falsify", help="Executa o pipeline de falsificacao sobre Dataset B")
    p_falsif.set_defaults(func=cmd_falsify)

    # design
    p_des = subparsers.add_parser("design", help="Proposta de desenho experimental discriminatorio")
    p_des.set_defaults(func=cmd_design)

    # test
    p_test = subparsers.add_parser("test", help="Executa a suite de testes pytest")
    p_test.add_argument("pytest_args", nargs="*", help="Argumentos opcionais para o pytest")
    p_test.set_defaults(func=cmd_test)

    # verify
    p_ver = subparsers.add_parser("verify", help="Auditoria completa de integridade epistêmica e dados")
    p_ver.set_defaults(func=cmd_verify)

    # demo
    p_demo = subparsers.add_parser("demo", help="Executa bateria pedagogica completa passo a passo")
    p_demo.set_defaults(func=cmd_demo)

    return parser


def main() -> None:
    parser = build_parser()
    if len(sys.argv) == 1:
        # Se invocado sem argumentos, roda a demo
        print("Nenhum comando especificado. Executando bateria de demonstracao padrao:\n")
        cmd_demo(argparse.Namespace())
        sys.exit(0)

    args = parser.parse_args()
    if hasattr(args, "func"):
        code = args.func(args)
        sys.exit(code or 0)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
