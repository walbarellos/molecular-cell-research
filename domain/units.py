"""Padronizacao de unidades fisicas e biofisicas."""

from enum import Enum


class StandardUnit(str, Enum):
    # Distancia
    NANOMETER = "nm"
    MICROMETER = "um"
    MILLIMETER = "mm"
    METER = "m"

    # Velocidade
    NANOMETER_PER_SECOND = "nm/s"
    MICROMETER_PER_SECOND = "um/s"
    METER_PER_SECOND = "m/s"

    # Tempo
    MILLISECOND = "ms"
    SECOND = "s"
    MINUTE = "min"
    HOUR = "h"

    # Concentracao
    PICOMOLAR = "pM"
    NANOMOLAR = "nM"
    MICROMOLAR = "uM"
    MILLIMOLAR = "mM"
    MOLAR = "M"

    # Forca
    PICONEWTON = "pN"
    NANONEWTON = "nN"
    NEWTON = "N"

    # Temperatura
    CELSIUS = "degC"
    KELVIN = "K"

    # Energia
    JOULE = "J"
    KILOJOULE_PER_MOLE = "kJ/mol"
    KCAL_PER_MOLE = "kcal/mol"
    KB_T = "k_B*T"

    # Cinética / Taxas
    PER_SECOND = "1/s"
    PER_MICROMOLAR_SECOND = "1/(uM*s)"
    PER_MILLIMOLAR_SECOND = "1/(mM*s)"

    # Adimensional / Contagem
    DIMENSIONLESS = "dimensionless"
    PERCENT = "%"
    COUNT = "count"
