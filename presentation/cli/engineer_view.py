"""Renderizador CLI para o Modo Engenheiro (L7)."""

from presentation.api.view_models import EngineerViewDTO


def render_engineer_view(dto: EngineerViewDTO) -> str:
    lines = []
    lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
    lines.append("│                   CELL LAB - MODO ENGENHEIRO (COMPONENTES)                   │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [ENTIDADES BIOLOGICAS E FISICAS CATALOGADAS]                                 │")
    for ent in dto.entities:
        ext_ids = ", ".join(f"{x['database_name']}:{x['accession_code']}" for x in ent.get("external_identifiers", []))
        lines.append(f"│   ■ [{ent['entity_type'].upper()}] {ent['canonical_name']} ({ent['systematic_name']})")
        if ext_ids:
            lines.append(f"│     Identificadores Externos: {ext_ids}")

    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append(f"│ Modelo Ativo: {dto.model_name}")
    lines.append("│ [PARAMETROS BIOFISICOS CALIBRADOS]")
    for p in dto.parameters:
        bounds = f"[{p['sensitivity_bounds'][0]}, {p['sensitivity_bounds'][1]}]" if p.get("sensitivity_bounds") else "N/A"
        lines.append(f"│   ■ {p['name']} = {p['calibrated_value']} {p['unit']} (origem: {p['origin']})")
        lines.append(f"│     Descricao: {p['description']}")
        lines.append(f"│     Faixa de Sensibilidade: {bounds}")

    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [ENVELOPE OPERACIONAL VALIDADO]")
    env = dto.operating_envelope
    lines.append(f"│   ■ Faixa de [ATP] : {env['validated_atp_range_uM'][0]} a {env['validated_atp_range_uM'][1]} μM")
    lines.append(f"│   ■ Forca de Carga : {env['validated_load_force_pN']} pN (unloaded)")
    lines.append(f"│   ■ Temperatura    : {env['temperature_degC']} °C")
    lines.append(f"│   ■ Tampao         : {env['buffer']}")
    lines.append(f"│   ■ Stall Force    : ~{env['stall_force_empiric_pN']} pN (limite experimental)")
    lines.append(f"│   ■ Evidencias de Suporte : {dto.supporting_evidence_count} registros primarios")
    lines.append("└──────────────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
