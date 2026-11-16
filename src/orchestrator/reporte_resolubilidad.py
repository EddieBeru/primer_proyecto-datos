"""Representación textual compartida por CLI e interfaz."""

from src.estructuras.tabla_indice import TablaIndice


def texto_reporte(resultado):
    estado = {"resoluble": "RESOLUBLE", "no_resoluble": "NO RESOLUBLE",
              "incompleta": "VERIFICACIÓN INCOMPLETA"}[resultado.estado]
    lineas = [f"Cripta: {resultado.cripta_id}", f"Resultado: {estado}"]
    if resultado.estado == "incompleta":
        lineas.extend((f"Motivo: {resultado.motivo}",))
        return "\n".join(lineas)
    if resultado.estado == "resoluble":
        lineas.append("Orden de llaves:")
        if resultado.orden_llaves:
            for i, (llave, ubicacion) in enumerate(resultado.orden_llaves, 1):
                lineas.append(f"{i}. {llave}; {_texto_ubicacion(ubicacion)}")
        else:
            lineas.append("ninguna")
        return "\n".join(lineas)
    lineas.append(f"Motivo: {resultado.motivo}")
    lineas.append("Llaves no obtenibles:")
    lineas.extend(resultado.llaves_no_obtenibles or ("ninguna",))
    lineas.append("Frontera bloqueada:")
    if resultado.frontera:
        lineas.extend(f"sala {origen} / {direccion} -> sala {destino}; requiere {llave}"
                      for origen, direccion, destino, llave in resultado.frontera)
    else:
        lineas.append("ninguna")
    lineas.append("Ubicaciones:")
    ubicaciones = resultado.ubicaciones
    presentes = TablaIndice()
    for ubicacion in ubicaciones:
        presentes[ubicacion.id] = True
        lineas.append(f"{ubicacion.id}: {_texto_ubicacion(ubicacion)}")
    for llave in resultado.llaves_no_obtenibles:
        if llave not in presentes:
            lineas.append(f"{llave}: ubicación no declarada")
    if not ubicaciones and not resultado.llaves_no_obtenibles:
        lineas.append("ninguna")
    lineas.append("Ciclo bloqueante:")
    if resultado.ciclo:
        lineas.append(" -> ".join(resultado.ciclo))
        for evidencia in resultado.alternativas_bloqueadas:
            if evidencia[0] == "puerta":
                _, origen, direccion, destino, llave = evidencia
                lineas.append(f"sala {origen} / {direccion} -> sala {destino}; requiere {llave}")
            elif evidencia[0] == "ubicacion":
                _, llave, sala_id, enemigo = evidencia
                detalle = f"{llave}: ubicación sala {sala_id}"
                if enemigo is not None:
                    detalle += f"; enemigo {enemigo} (sala inicial)"
                lineas.append(detalle)
    else:
        lineas.append("ninguno")
    return "\n".join(lineas)


def _texto_ubicacion(ubicacion):
    if ubicacion is None:
        return "ubicación no declarada"
    texto = f"sala {ubicacion.sala}"
    if ubicacion.enemigo is not None:
        texto += f"; enemigo {ubicacion.enemigo} (sala inicial)"
    return texto
