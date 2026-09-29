"""Renderizador CLI para o Modo Usuario (L7)."""

from presentation.api.view_models import UserViewDTO


def render_user_view(dto: UserViewDTO) -> str:
    lines = []
    lines.append("┌──────────────────────────────────────────────────────────────────────────────┐")
    lines.append("│                    CELL LAB - MODO USUARIO (OPERACIONAL)                     │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append(f"│ Fenomeno: Transporte Molecular KIF5B │ Estado: {dto.operational_state:<33} │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [PARAMETROS DE ENTRADA]                                                      │")
    lines.append(f"│   Concentracao de ATP : {dto.atp_concentration_uM:>8.1f} μM                                      │")
    lines.append(f"│   Forca de Carga      : {dto.load_force_pN:>8.2f} pN                                      │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [RESULTADO DA SIMULACAO]                                                     │")
    lines.append(f"│   Velocidade Calculada: {dto.predicted_velocity_um_s:>7.4f} ± {dto.predicted_uncertainty_um_s:.4f} μm/s                               │")
    lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
    lines.append("│ [FIREWALL EPISTEMICO]                                                        │")
    lines.append(f"│   Tier de Dados       : [TIER::{dto.data_tier}]                                       │")
    lines.append(f"│   Status Epistemico   : [EPISTEMIC::{dto.epistemic_status}]                                   │")
    valid_str = "SIM (Dentro do Envelope)" if dto.is_within_validated_envelope else "NAO (Regime Refutado)"
    lines.append(f"│   Envelope Validado   : {valid_str:<45} │")

    if dto.epistemic_warning:
        lines.append("├──────────────────────────────────────────────────────────────────────────────┤")
        lines.append("│ [ALERTA DE FRONTEIRA]                                                        │")
        warn = dto.epistemic_warning
        # Split across lines cleanly
        part1 = warn[:72]
        part2 = warn[72:144]
        part3 = warn[144:216]
        lines.append(f"│   ▲ {part1:<72} │")
        if part2.strip():
            lines.append(f"│     {part2:<72} │")
        if part3.strip():
            lines.append(f"│     {part3:<72} │")

    lines.append("└──────────────────────────────────────────────────────────────────────────────┘")
    return "\n".join(lines)
