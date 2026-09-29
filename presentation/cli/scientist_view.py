"""Renderizador CLI para o Modo Cientifico (L7)."""

from presentation.api.view_models import ScientistViewDTO


def render_scientist_view(dto: ScientistViewDTO) -> str:
    lines = []
    lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
    lines.append("│               CELL LAB - MODO CIENTIFICO (PROVENIENCIA E FALHAS)             │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append(f"│ Modelo Ativo: {dto.active_model_id}")
    lines.append("│ [PREMISSAS SIMPLIFICADORAS DECLARADAS] (INV-MODEL-001):")
    for idx, asm in enumerate(dto.assumptions, 1):
        lines.append(f"│   {idx}. {asm}")

    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [Trilha de Proveniencia Epistemica Ponta a Ponta]:")
    chain = dto.provenance_chain
    lines.append(f"│   Fonte Primaria  : {chain['source']}")
    lines.append(f"│   Ensaio Fisico   : {chain['experiment']}")
    lines.append(f"│   Amostra Obs.    : {chain['sample_observation']}")
    lines.append(f"│   Evidencia L3    : {chain['evidence']}")
    lines.append(f"│   Afirmacao L4    : {chain['claim']}")
    lines.append(f"│   Modelo L5       : {chain['model']}")
    lines.append(f"│   Simulacao L5    : {chain['simulation']}")
    lines.append(f"│   Predicao L5     : {chain['prediction_sample']}")

    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [AFIRMACOES CIENTIFICAS] (Claims Ativos no Grafo):")
    for c in dto.active_claims:
        ep = c["epistemic_record"]
        status_tag = f"[TIER::{ep['data_tier']} | STATUS::{ep['status']}]"
        lines.append(f"│   ■ ID: {c['id']} {status_tag}")
        lines.append(f"│     Afirmacao: \"{c['statement']}\"")
        if c.get("supporting_evidence_ids"):
            lines.append(f"│     Evidencias de Suporte : {len(c['supporting_evidence_ids'])} fontes primarias")
        if c.get("conflicting_evidence_ids"):
            lines.append(f"│     Evidencias de Conflito: {len(c['conflicting_evidence_ids'])} fontes primarias")

    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [REGISTRO DE CONFLITOS E FALSIFICACAO] (INV-CONFLICT-001):")
    for conf in dto.conflicts:
        lines.append(f"│   ▲ Conflito ID: {conf['id']} (Status: {conf['resolution_status']})")
        lines.append(f"│     Evidencia A : {conf['evidence_a_id']} (Carga Zero)")
        lines.append(f"│     Evidencia B : {conf['evidence_b_id']} (Sob Carga Contraria)")
        lines.append(f"│     Discrepancia: {conf['divergence_metric']}")
        lines.append(f"│     Diagnostico : {conf['resolution_notes']}")

    lines.append("└──────────────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
