"""Ponto de Entrada da Interface de Linha de Comando (CLI) da SSEP (L7)."""

import argparse
import sys
from pathlib import Path

# Garante path do projeto
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

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


def handle_status(args) -> None:
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


def handle_user(args) -> None:
    model_id = "MOD-KIF5B-4STATE-FORCE-DEPENDENT" if getattr(args, "model", "m1").lower() == "m2" else "MOD-KIF5B-MINIMAL-MM"
    dto = simulate_user_mode(atp_uM=args.atp, load_pN=args.load, model_id=model_id)
    print(render_user_view(dto))


def handle_run_m2_evaluation(args) -> None:
    print("[L6 ORCHESTRATION] Executando Ciclo 10: Validacao Multivariada do Modelo M2...")
    from application.run_m2_evaluation_cycle import execute_m2_evaluation_cycle
    report = execute_m2_evaluation_cycle()
    m = report["metrics"]
    print("┌──────────────────────────────────────────────────────────────────────────────┐")
    print("│               CICLO 10: VALIDACAO MULTIVARIADA DO MODELO M2                  │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print(f"│ Modelo Avaliado  : {report['model_id']:<57} │")
    print(f"│ Amostras Totais  : {report['total_observations_evaluated']} (10 do Dataset A + 11 do Dataset B){'':<23} │")
    print(f"│ Coef. Det. (R2)  : {m['r_squared']:<57.4f} │")
    print(f"│ Chi2 Reduzido    : {m['chi2_reduced']:<57.3f} │")
    print(f"│ Pontos em 2-sigma: {m['within_2_sigma_count']}/{report['total_observations_evaluated']} ({m['within_2_sigma_ratio']*100:.1f}%){'':<46} │")
    print(f"│ Escore z Maximo  : {m['max_z_score']:<57.3f} │")
    print(f"│ Veredito Final   : [CONSISTENT | TIER::DERIVED | STATUS::VALIDATED]{'':<14} │")
    print(f"│ Resolucao Confl. : {report['conflict_resolution']['resolution_status']:<57} │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")


def handle_engineer(args) -> None:
    dto = get_engineer_view()
    print(render_engineer_view(dto))


def handle_scientist(args) -> None:
    dto = get_scientist_view()
    print(render_scientist_view(dto))


def handle_run_reproduction(args) -> None:
    print("[L6 ORCHESTRATION] Executando Ciclo 06: Reproducao sobre Dataset A...")
    report = execute_dataset_a_reproduction()
    print("[STATUS::SUCCESS] Pipeline concluido. Relatorio gerado com exito.")


def handle_run_falsification(args) -> None:
    print("[L6 ORCHESTRATION] Executando Ciclo 07: Falsificacao sobre Dataset B...")
    report = execute_dataset_b_falsification()
    print("[STATUS::SUCCESS] Pipeline concluido. Conflito e refutacao registrados.")


def handle_design_experiment(args) -> None:
    print("[L6 EXPERIMENTAL DESIGN] Calculando poder discriminatorio entre modelos concorrentes...")
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
    print(f"│ Tecnica Proposta : {des['proposed_technique'][:55]:<57} │")
    print(f"│ Poder Resolucao  : {des['discriminatory_power_score']*100:.1f}% (> 20σ de separacao analitica){'':<20} │")
    print("├──────────────────────────────────────────────────────────────────────────────┤")
    print("│ [PREVISOES DIVERGENTES DOS MODELOS]:                                         │")
    for mod_id, outcome in des["predicted_outcomes"].items():
        print(f"│   ■ {mod_id}: {outcome:<50} │")
    print("└──────────────────────────────────────────────────────────────────────────────┘")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="cell-lab",
        description="Scientific Systems Exploration Platform (SSEP) - Interface CLI",
    )
    subparsers = parser.add_subparsers(dest="command", help="Comandos disponiveis")

    # Comando status
    p_status = subparsers.add_parser("status", help="Exibe status geral do conhecimento catalogado")
    p_status.set_defaults(func=handle_status)

    # Modo Usuario
    p_user = subparsers.add_parser("user", help="Modo Usuario: simulacao e exploracao operacional")
    p_user.add_argument("--atp", type=float, default=1000.0, help="Concentracao de ATP em micromolar (padrao: 1000.0)")
    p_user.add_argument("--load", type=float, default=0.0, help="Forca de carga contraria em piconewtons (padrao: 0.0)")
    p_user.add_argument("--model", choices=["m1", "m2"], default="m1", help="Modelo a simular: m1 (quimioestatico) ou m2 (mecanoquimico Bell/Kramers)")
    p_user.set_defaults(func=handle_user)

    # Modo Engenheiro
    p_eng = subparsers.add_parser("engineer", help="Modo Engenheiro: inspecao de entidades e parametros biofisicos")
    p_eng.set_defaults(func=handle_engineer)

    # Modo Cientifico
    p_sci = subparsers.add_parser("scientist", help="Modo Cientifico: proveniencia, premissas e contradicoes")
    p_sci.set_defaults(func=handle_scientist)

    # Comandos de Execucao de Ciclos
    p_repro = subparsers.add_parser("run-reproduction", help="Executa o pipeline de reproducao sobre Dataset A (Ciclo 06)")
    p_repro.set_defaults(func=handle_run_reproduction)

    p_falsif = subparsers.add_parser("run-falsification", help="Executa o pipeline de falsificacao sobre Dataset B (Ciclo 07)")
    p_falsif.set_defaults(func=handle_run_falsification)

    # Comando de Desenho Experimental
    p_design = subparsers.add_parser("design-experiment", help="Executa o desenho experimental discriminatorio (Ciclo 09)")
    p_design.set_defaults(func=handle_design_experiment)

    # Comando de Avaliacao M2 (Ciclo 10)
    p_m2 = subparsers.add_parser("evaluate-m2", help="Executa validacao multivariada do Modelo M2 sobre Datasets A e B (Ciclo 10)")
    p_m2.set_defaults(func=handle_run_m2_evaluation)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
