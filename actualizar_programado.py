from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from actualizar_nacional import main


try:
    ZONA_HORARIA = ZoneInfo("America/Santo_Domingo")
except ZoneInfoNotFoundError:
    ZONA_HORARIA = timezone(timedelta(hours=-4), "America/Santo_Domingo")
MINUTOS_DESPUES_DEL_SORTEO = 0
MINUTOS_BUSCANDO = 60


@dataclass(frozen=True)
class SorteoProgramado:
    nombre: str
    hora: time
    dias: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 6)


SORTEOS: tuple[SorteoProgramado, ...] = (
    SorteoProgramado("Anguila Manana", time(10, 0)),
    SorteoProgramado("LoteDom", time(12, 0)),
    SorteoProgramado("La Primera Dia", time(12, 0)),
    SorteoProgramado("La Suerte 12:30", time(12, 30)),
    SorteoProgramado("King Lottery 12:30", time(12, 30)),
    SorteoProgramado("Loteria Real", time(12, 55)),
    SorteoProgramado("Anguila Medio Dia", time(13, 0)),
    SorteoProgramado("Florida Dia", time(13, 30)),
    SorteoProgramado("Nacional Tarde", time(14, 30)),
    SorteoProgramado("Nueva York Tarde", time(14, 30)),
    SorteoProgramado("Leidsa Domingo", time(15, 55), (6,)),
    SorteoProgramado("La Suerte 6:00", time(18, 0)),
    SorteoProgramado("Anguila Tarde", time(18, 0)),
    SorteoProgramado("Nacional Domingo", time(18, 0), (6,)),
    SorteoProgramado("King Lottery 7:30", time(19, 30)),
    SorteoProgramado("Loteka", time(19, 55)),
    SorteoProgramado("La Primera Noche", time(20, 0)),
    SorteoProgramado("Leidsa Noche", time(20, 55), (0, 1, 2, 3, 4, 5)),
    SorteoProgramado("Anguila Noche", time(21, 0)),
    SorteoProgramado("Nacional Noche", time(21, 0), (0, 1, 2, 3, 4, 5)),
    SorteoProgramado("Florida Noche", time(21, 45)),
    SorteoProgramado("Nueva York Noche", time(22, 30)),
    SorteoProgramado("Mega Millions", time(23, 0), (1, 4)),
    SorteoProgramado("PowerBall", time(23, 0), (2, 5)),
)


def esta_en_ventana_de_actualizacion(ahora: datetime, sorteo: SorteoProgramado) -> bool:
    if ahora.weekday() not in sorteo.dias:
        return False

    inicio_sorteo = datetime.combine(ahora.date(), sorteo.hora, tzinfo=ZONA_HORARIA)
    inicio_busqueda = inicio_sorteo + timedelta(minutes=MINUTOS_DESPUES_DEL_SORTEO)
    fin_busqueda = inicio_busqueda + timedelta(minutes=MINUTOS_BUSCANDO)

    return inicio_busqueda <= ahora <= fin_busqueda


def sorteos_activos(ahora: datetime) -> list[SorteoProgramado]:
    return [
        sorteo
        for sorteo in SORTEOS
        if esta_en_ventana_de_actualizacion(ahora, sorteo)
    ]


def main_programado() -> None:
    ahora = datetime.now(ZONA_HORARIA)
    activos = sorteos_activos(ahora)

    print(f"Hora RD: {ahora:%Y-%m-%d %H:%M:%S}")

    if not activos:
        print("No hay sorteos dentro de la ventana de busqueda.")
        return

    nombres = ", ".join(sorteo.nombre for sorteo in activos)
    print(f"Buscando actualizaciones para: {nombres}")
    main()


if __name__ == "__main__":
    main_programado()
