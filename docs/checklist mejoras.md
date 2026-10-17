# Checklist de mejoras: enemigos, trampas y salas oscuras

Pedido del jugador (17/10/2026), en tres bloques. Completado el mismo día:
cada punto quedó implementado, con su prueba y su anotación en los
documentos correspondientes (`DECISIONES.md` 35-37, `README.md`,
`docs/guia vista.md` §13).

## 1. Enemigos por todo el mapa (y que no solo cuiden la puerta)

- [x] Al entrar a una sala se **precargan las salas vecinas** (dormidas, §2.4):
      existen en el modelo antes de visitarlas, sin gastar peticiones extra de
      contenido.
      → `RoomLoader.asegurar_salas`, `ProveedorSesion._precargar_vecinas`,
      `Sesion._registrar_vecinas` + gancho al cambiar de sala en `Sesion.paso`.
      Pruebas: `test_vecinas_precargadas_dormidas_sin_visitar`,
      `test_al_entrar_a_vecina_se_precargan_sus_vecinas`.
- [x] Los **errantes y rastreadores** recorren ahora todo el mapa cargado
      (antes solo podían moverse entre salas ya visitadas).
      → La vecina dormida ya está en `estado.salas`; la IA no cambió (§2.8).
      Pruebas: `test_errante_cruza_desde_sala_vecina`,
      `test_rastreadora_sigue_el_rastro_entre_salas`.
- [x] Los enemigos activados al entrar usan su **velocidad real de ficha**
      (antes todos actuaban con la velocidad por defecto 5).
      → `intentar_mover` pasa el catálogo a `activar_sala`.
      Prueba: `test_dormidos_despiertan_al_entrar_con_velocidad_real`.
- [x] El guardián sigue esperando en su sala (§2.8) y no abandona el objeto
      que custodia: eso es su comportamiento, no un defecto.
      → Sin cambios de IA; cubierto por las pruebas de enemigos existentes.
- [x] Pruebas: precarga dormida sin marcar visita; vecina no se activa sola;
      errante de sala vecina se mueve; rastreador persigue el rastro; las
      pruebas de revisita y de puntaje siguen pasando.
      → Las de revisita (`test_revisita...`) y la ruta de victoria del
      integrador siguen en verde (193 pytest + 98 PASS del script).

## 2. Trampas que hacen daño, envenenan o queman

- [x] Al **pasar por encima** de una trampa armada (vista) se dispara de
      inmediato: intención `pisar <instancia>` (además del disparo al entrar,
      §2.10).
      → `VistaApp._revisar_trampas` (+ `RADIO_TRAMPA`, guarda «parado
      encima»), `Sesion._intencion`, consola de `Fachada` y `consola.py`.
      Prueba: `test_caminar_sobre_trampa_la_dispara`.
- [x] El motor aplica **daño** y, según la ficha de la trampa, también
      **veneno** (pulsos cada 80 durante 400, lo cura el antídoto) o
      **quemadura** (80×3 = 240; el antídoto no la cura).
      → `Trap.veneno/quemadura` (+ `fuego`), `efectos.quemar` /
      `ejecutar_quemadura`, rama `quemadura` en `Fachada.avanzar`.
      Pruebas: `test_trampa_venenosa_dana_y_envenena`,
      `test_trampa_de_llamas_dana_y_quema`, `test_quemadura_ticks_y_apagado`.
- [x] Deshacer restaura vida y efectos del jugador y cancela los pulsos
      programados.
      → `deshacer.py` op `trampa` (guardaba `veneno_antes`/`quemadura_antes`).
      Prueba: `test_deshacer_trampa_restaura_vida_y_efectos`.
- [x] `paquete_demo`/falso: una trampa de veneno que envenena de verdad y una
      trampa de llamas que quema (para probarlo sin API).
      → `veneno-01` con `veneno=2`; nueva `llamas-01` (`t1-2` en la sala 1)
      con `quemadura=3`; paquete offline regenerado (16 fichas).
- [x] Avisos visibles en la vista al recibir daño (toast + destello rojo).
      → `VistaApp.enviar` (caída de vida ⇒ `dano_ttl` + aviso) y borde rojo
      en `dibujar`.
- [x] Pruebas: daño + veneno + quemadura + rearme + deshacer; pasar por encima
      en la vista; caminar fuera de trampas sigue siendo gratis.
      → Las de arriba + `test_caminar_no_cuesta_vida_ni_tiempo` (sigue verde)
      + rearme cubierto por `test_trampa_dana_desarma_y_rearma`.

## 3. Sala oscura iluminada con antorchas (offline y API)

- [x] El modelo acepta el campo `oscura` (o `oscuridad`) de la sala de la API
      y lo conserva en `SalaViva` (serializa en guardado).
      → `Room.oscura`, `RoomContentEntry.oscura` (se mezcla en
      `hidratar_contenido`) y merge del cargador.
      Pruebas: `test_sala_oscura_se_hereda_y_serializa`,
      `test_contenido_marca_sala_oscura`.
- [x] La foto (`K5`) expone `sala_oscura` a la vista.
      → `FotoEstado.sala_oscura` en `Fachada.foto()`.
- [x] En la vista, una sala oscura se dibuja con velo negro y halo de luz
      alrededor del jugador; con la antorcha encendida la sala se ilumina.
      → `capas.dibujar_oscuridad` (+ `antorcha_encendida`) llamada en
      `pantallas.pantalla_juego`.
      Prueba: `test_sala_oscura_velo_y_antorcha`.
- [x] La consola avisa de la oscuridad y de cómo encender una antorcha.
      → `consola.renderizar` («a oscuras; enciende una antorcha…» /
      «iluminada por tu antorcha»).
      Prueba: `test_consola_avisa_sala_oscura`.
- [x] `paquete_demo`: la «Capilla oscura» (sala 3) queda realmente oscura y la
      antorcha de la sala 1 dura lo suficiente para usarla.
      → `oscura=True` en la sala 3; antorcha `duracion=1200`; paquete
      regenerado con `scripts/exportar_paquete.py`.
      Prueba: `test_antorcha_dura_y_termina` (ajustada a 1200).
- [x] Pruebas: parseo del campo, serialización, render con/sin antorcha,
      consola, y la ruta offline sigue ganando.
      → Las de arriba + ruta de victoria en `test_sesion`/`test_vista` y el
      script de integración (98 PASS) con vida suficiente aun con la trampa
      de veneno de la sala 3.

## Verificación final

- `python -m pytest -q` → **193 passed, 1 skipped** (el skip es
  `test_api_real`, que gasta presupuesto real y queda pendiente de tu OK).
- Script de integración de 98 checks → **98 PASS, 0 FAIL**.
- `paquete_demo/` regenerado; `python -m src.main --jugar --offline
  paquete_demo/` y `--vista --offline paquete_demo/` funcionan sin red.
