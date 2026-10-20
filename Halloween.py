import math
import random
import sys

import pygame

# ----------------------------------------------------------------------------
# Configuración
# ----------------------------------------------------------------------------
ANCHO, ALTO = 1100, 680
FPS = 60

# (nombre, color característico)
# El valor de cada personaje es su NIVEL DE PODER ficticio: 1 = el más débil, 15 = el más fuerte.
# La posición en la lista + 1 es el valor que se ordena.
PERSONAJES = [
    ("Zombie",              (130, 150, 70)),   # 1  verde podrido
    ("Ghostface",           (235, 235, 235)),  # 2  blanco
    ("Jack el Destripador", (110, 110, 110)),  # 3  niebla de Londres
    ("Jigsaw",              (160, 30, 30)),    # 4  rojo de la marioneta
    ("Chucky",              (230, 120, 40)),   # 5  cabello naranja
    ("Annabelle",           (225, 190, 200)),  # 6  vestido rosa pálido
    ("Frankenstein",        (110, 170, 90)),   # 7  piel verde
    ("Michael Myers",       (70, 100, 160)),   # 8  mono azul
    ("Jason",               (190, 190, 170)),  # 9  máscara de hockey
    ("Drácula",             (110, 20, 60)),    # 10 capa vino
    ("Freddy Krueger",      (178, 34, 34)),    # 11 rojo del suéter
    ("La Monja",            (60, 60, 80)),     # 12 hábito oscuro
    ("Slenderman",          (150, 150, 165)),  # 13 traje gris
    ("Valak",               (90, 50, 130)),    # 14 morado oscuro
    ("Pennywise",           (230, 60, 60)),    # 15 globo rojo
]

FONDO_ARRIBA = (14, 8, 24)
FONDO_ABAJO = (38, 16, 8)
NARANJA = (255, 140, 30)
TEXTO = (240, 232, 220)
TEXTO_SUAVE = (160, 150, 150)
COLOR_COMPARA = (255, 235, 90)
COLOR_INTERCAMBIO = (255, 255, 255)
COLOR_ORDENADO = (120, 255, 140)

margen_x = 50
base_y = ALTO - 190
alto_max = 300
RIEL_Y = 120      # riel del brazo mecánico
VIGA_Y = 140      # viga que sostiene los dos brazos
LEVANTE = 20      # cuánto suben las barras cuando el brazo las agarra


# ----------------------------------------------------------------------------
# Heap Sort como generador: cada yield es un paso de la animación
# ----------------------------------------------------------------------------
def heapify(a, n, i):
    """Mantiene la propiedad de max-heap en el subárbol con raíz i."""
    mayor = i
    izq = 2 * i + 1
    der = 2 * i + 2

    if izq < n:
        yield ("comparar", mayor, izq)
        if a[izq] > a[mayor]:
            mayor = izq
    if der < n:
        yield ("comparar", mayor, der)
        if a[der] > a[mayor]:
            mayor = der

    if mayor != i:
        a[i], a[mayor] = a[mayor], a[i]
        yield ("intercambiar", i, mayor)
        yield from heapify(a, n, mayor)


def heap_sort(a):
    n = len(a)
    # Fase 1: construir el max-heap
    for i in range(n // 2 - 1, -1, -1):
        yield ("fase", "Construyendo el heap")
        yield from heapify(a, n, i)
    # Fase 2: extraer el máximo repetidamente
    for fin in range(n - 1, 0, -1):
        yield ("fase", "Extrayendo el máximo")
        a[0], a[fin] = a[fin], a[0]
        yield ("intercambiar", 0, fin)
        yield ("ordenado", fin)
        yield from heapify(a, fin, 0)
    yield ("ordenado", 0)
    yield ("fin",)


# ----------------------------------------------------------------------------
# Utilidades de dibujo
# ----------------------------------------------------------------------------
def degradado_vertical(superficie, c1, c2):
    for y in range(ALTO):
        t = y / ALTO
        color = tuple(int(c1[k] + (c2[k] - c1[k]) * t) for k in range(3))
        pygame.draw.line(superficie, color, (0, y), (ANCHO, y))


def aclarar(color, f):
    return tuple(min(255, int(c + (255 - c) * f)) for c in color)


def oscurecer(color, f):
    return tuple(int(c * (1 - f)) for c in color)


def dibujar_luna(sup):
    cx, cy, r = ANCHO - 130, 105, 48
    brillo = pygame.Surface((r * 5, r * 5), pygame.SRCALPHA)
    for k in range(10, 0, -1):
        pygame.draw.circle(brillo, (255, 200, 120, 6), (r * 2 + r // 2, r * 2 + r // 2), r + k * 7)
    sup.blit(brillo, (cx - r * 2 - r // 2, cy - r * 2 - r // 2))
    pygame.draw.circle(sup, (255, 214, 140), (cx, cy), r)
    pygame.draw.circle(sup, (240, 190, 115), (cx - 15, cy - 8), 9)
    pygame.draw.circle(sup, (240, 190, 115), (cx + 14, cy + 15), 6)


def dibujar_murcielago(sup, x, y, escala, aleteo):
    ala = 14 * escala
    alto_ala = (6 + 7 * math.sin(aleteo)) * escala
    c = (8, 5, 14)
    pygame.draw.ellipse(sup, c, (x - 4 * escala, y - 4 * escala, 8 * escala, 10 * escala))
    pygame.draw.polygon(sup, c, [(x - 2 * escala, y), (x - ala, y - alto_ala),
                                 (x - ala * 0.55, y + 2 * escala), (x - ala * 0.3, y - 1)])
    pygame.draw.polygon(sup, c, [(x + 2 * escala, y), (x + ala, y - alto_ala),
                                 (x + ala * 0.55, y + 2 * escala), (x + ala * 0.3, y - 1)])


def dibujar_calabaza_pequena(sup, x, y, r):
    pygame.draw.ellipse(sup, (214, 100, 15), (x - r, y - r * 0.8, r * 2, r * 1.6))
    pygame.draw.ellipse(sup, (240, 130, 30), (x - r * 0.55, y - r * 0.8, r * 1.1, r * 1.6), 2)
    pygame.draw.rect(sup, (60, 90, 30), (x - 2, y - r * 1.0, 4, r * 0.35))
    ojo = [(x - r * 0.5, y - r * 0.1), (x - r * 0.15, y - r * 0.1), (x - r * 0.33, y - r * 0.4)]
    pygame.draw.polygon(sup, (40, 15, 0), ojo)
    ojo2 = [(x + r * 0.5, y - r * 0.1), (x + r * 0.15, y - r * 0.1), (x + r * 0.33, y - r * 0.4)]
    pygame.draw.polygon(sup, (40, 15, 0), ojo2)
    pygame.draw.polygon(sup, (40, 15, 0), [(x - r * 0.4, y + r * 0.25), (x + r * 0.4, y + r * 0.25),
                                           (x + r * 0.2, y + r * 0.5), (x - r * 0.2, y + r * 0.5)])


def dibujar_telarana(sup, esquina_x, esquina_y, dx, dy, tam):
    color = (90, 80, 105)
    for k in range(5):
        ang = (math.pi / 2) * k / 4
        fx = esquina_x + dx * tam * math.cos(ang)
        fy = esquina_y + dy * tam * math.sin(ang)
        pygame.draw.line(sup, color, (esquina_x, esquina_y), (fx, fy), 1)
    for r in range(1, 5):
        pts = []
        for k in range(5):
            ang = (math.pi / 2) * k / 4
            rr = tam * r / 4
            pts.append((esquina_x + dx * rr * math.cos(ang), esquina_y + dy * rr * math.sin(ang)))
        pygame.draw.lines(sup, color, False, pts, 1)


def crear_fondo():
    fondo = pygame.Surface((ANCHO, ALTO))
    degradado_vertical(fondo, FONDO_ARRIBA, FONDO_ABAJO)
    dibujar_luna(fondo)
    dibujar_telarana(fondo, 0, 0, 1, 1, 130)
    dibujar_telarana(fondo, ANCHO, 0, -1, 1, 110)
    # suelo
    pygame.draw.rect(fondo, (22, 10, 6), (0, base_y + 8, ANCHO, ALTO))
    pygame.draw.line(fondo, NARANJA, (0, base_y + 8), (ANCHO, base_y + 8), 2)
    # siluetas de árboles secos
    for bx, altura in [(70, 90), (190, 60), (ANCHO - 260, 70), (ANCHO - 70, 100)]:
        pygame.draw.rect(fondo, (10, 6, 16), (bx - 3, base_y - altura + 8, 6, altura))
        pygame.draw.line(fondo, (10, 6, 16), (bx, base_y - altura + 25), (bx - 22, base_y - altura + 5), 3)
        pygame.draw.line(fondo, (10, 6, 16), (bx, base_y - altura + 40), (bx + 24, base_y - altura + 18), 3)
    return fondo


def texto_vertical(sup, fuente, texto, color, x_centro, y_base):
    img = fuente.render(texto, True, color)
    img = pygame.transform.rotate(img, 90)
    sup.blit(img, (x_centro - img.get_width() // 2, y_base - img.get_height()))


def dibujar_brazo(sup, x1, y1, x2, y2, grip, ancho_barra_px, activo):
    """Riel + carro + viga + dos brazos telescópicos con pinza.
    (x, y) = centro de la barra y su borde superior (donde apoya la pinza)."""
    metal = (112, 118, 135)
    metal_osc = (52, 55, 70)
    metal_claro = (178, 184, 200)

    # riel superior
    x_ini, x_fin = margen_x - 30, ANCHO - margen_x + 30
    pygame.draw.rect(sup, metal_osc, (x_ini, RIEL_Y - 4, x_fin - x_ini, 8), border_radius=4)
    pygame.draw.line(sup, metal_claro, (x_ini + 3, RIEL_Y - 2), (x_fin - 3, RIEL_Y - 2), 1)
    for sx in (x_ini, x_fin):
        pygame.draw.rect(sup, metal_osc, (sx - 5, RIEL_Y - 11, 10, 22), border_radius=3)

    xa, xb = min(x1, x2), max(x1, x2)
    xm = (x1 + x2) / 2

    # carro sobre el riel y varilla hacia la viga
    pygame.draw.rect(sup, metal_osc, (xm - 4, RIEL_Y + 6, 8, VIGA_Y - RIEL_Y), border_radius=2)
    pygame.draw.rect(sup, metal, (xm - 26, RIEL_Y - 10, 52, 20), border_radius=5)
    pygame.draw.rect(sup, metal_claro, (xm - 24, RIEL_Y - 9, 48, 4), border_radius=2)
    for dx in (-16, 16):
        pygame.draw.circle(sup, metal_osc, (int(xm + dx), RIEL_Y + 10), 4)
        pygame.draw.circle(sup, metal_claro, (int(xm + dx), RIEL_Y + 10), 1)

    # viga horizontal (une los dos brazos)
    pygame.draw.rect(sup, metal, (xa - 14, VIGA_Y - 6, xb - xa + 28, 12), border_radius=5)
    pygame.draw.rect(sup, metal_claro, (xa - 12, VIGA_Y - 5, xb - xa + 24, 3), border_radius=2)

    # luz del brazo: naranja en reposo, amarilla/blanca cuando trabaja
    luz = NARANJA if not activo else (COLOR_INTERCAMBIO if grip > 0.8 else COLOR_COMPARA)

    for (x, y) in ((x1, y1), (x2, y2)):
        tope = y - 8                              # parte de arriba de la placa de la pinza
        largo = max(0, tope - VIGA_Y)
        # tubo exterior e interior (telescópico)
        pygame.draw.rect(sup, metal_osc, (x - 6, VIGA_Y, 12, largo * 0.55), border_radius=3)
        pygame.draw.rect(sup, metal, (x - 3, VIGA_Y + largo * 0.35, 6, largo * 0.65), border_radius=2)
        pygame.draw.circle(sup, metal_claro, (int(x), VIGA_Y), 5)
        # placa de la pinza
        mitad = ancho_barra_px / 2 + (1 - grip) * 8
        pygame.draw.rect(sup, metal, (x - mitad - 5, tope, 2 * mitad + 10, 8), border_radius=3)
        pygame.draw.circle(sup, luz, (int(x), int(tope + 4)), 3)
        # mordazas (naranja industrial) con gancho hacia adentro
        pygame.draw.rect(sup, NARANJA, (x - mitad - 5, tope, 5, 36), border_radius=2)
        pygame.draw.rect(sup, NARANJA, (x + mitad, tope, 5, 36), border_radius=2)
        pygame.draw.rect(sup, (255, 190, 90), (x - mitad - 5, tope + 30, 12, 6), border_radius=2)
        pygame.draw.rect(sup, (255, 190, 90), (x + mitad - 7, tope + 30, 12, 6), border_radius=2)


# ----------------------------------------------------------------------------
# Programa principal
# ----------------------------------------------------------------------------
def nuevo_arreglo(modo="aleatorio"):
    n = len(PERSONAJES)
    valores = list(range(1, n + 1))
    if modo == "aleatorio":
        random.shuffle(valores)
    elif modo == "inverso":
        valores.reverse()
    elif modo == "casi":
        for _ in range(3):
            i, j = random.sample(range(n), 2)
            valores[i], valores[j] = valores[j], valores[i]
    return valores


def main():
    pygame.init()
    pantalla = pygame.display.set_mode((ANCHO, ALTO))
    pygame.display.set_caption("Heap Sort  |  Noche de Halloween")
    reloj = pygame.time.Clock()

    f_titulo = pygame.font.SysFont("georgia", 34, bold=True)
    f_sub = pygame.font.SysFont("georgia", 16, italic=True)
    f_nombre = pygame.font.SysFont("consolas", 12, bold=True)
    f_valor = pygame.font.SysFont("consolas", 16, bold=True)
    f_info = pygame.font.SysFont("consolas", 15)

    fondo = crear_fondo()
    n = len(PERSONAJES)
    ancho_barra = (ANCHO - 2 * margen_x) // n
    separacion = 6
    barra_w = ancho_barra - separacion

    def x_slot(i):
        return margen_x + i * ancho_barra + separacion // 2

    def altura(v):
        return int(alto_max * v / n)

    # Estado de la animación
    valores = nuevo_arreglo("aleatorio")
    generador = None
    corriendo = False
    terminado = False
    comparando = ()
    intercambiando = ()
    ordenados = set()
    fase = "Presiona ESPACIO para comenzar"
    comparaciones = 0
    intercambios = 0
    velocidad = 6  # pasos por segundo
    acumulado = 0.0
    tiempo = 0.0

    # Posición dibujada de cada barra (por valor) para que se deslicen suave
    x_dib = {v: float(x_slot(i)) for i, v in enumerate(valores)}
    subida = {v: 0.0 for v in range(1, n + 1)}

    # Brazo mecánico: sostiene dos barras (por valor) o descansa
    sostiene = None
    reposo = (ANCHO / 2 - 70, VIGA_Y + 40, ANCHO / 2 + 70, VIGA_Y + 40)
    brazo = {"x1": reposo[0], "y1": reposo[1], "x2": reposo[2], "y2": reposo[3], "grip": 0.0}

    # Murciélagos
    murcielagos = [[random.randint(0, ANCHO), random.randint(30, 200),
                    random.uniform(0.6, 1.4), random.uniform(1.0, 2.2)] for _ in range(5)]

    def reiniciar(modo):
        nonlocal valores, generador, corriendo, terminado, comparando
        nonlocal intercambiando, ordenados, fase, comparaciones, intercambios, sostiene
        valores = nuevo_arreglo(modo)
        generador = None
        corriendo = False
        terminado = False
        comparando = ()
        intercambiando = ()
        ordenados = set()
        sostiene = None
        fase = "Presiona ESPACIO para comenzar"
        comparaciones = 0
        intercambios = 0
        for i, v in enumerate(valores):
            x_dib[v] = float(x_slot(i))
            subida[v] = 0.0

    def paso():
        nonlocal comparando, intercambiando, fase, comparaciones, intercambios
        nonlocal terminado, corriendo, sostiene
        try:
            evento = next(generador)
        except StopIteration:
            terminado = True
            corriendo = False
            return
        tipo = evento[0]
        comparando = ()
        intercambiando = ()
        if tipo == "comparar":
            comparando = (evento[1], evento[2])
            comparaciones += 1
            sostiene = (valores[evento[1]], valores[evento[2]])
        elif tipo == "intercambiar":
            i, j = evento[1], evento[2]
            intercambiando = (i, j)
            intercambios += 1
            # el brazo sigue agarrando las mismas barras que se están moviendo
            par = (valores[i], valores[j])
            if sostiene and sostiene[0] in par:
                sostiene = (sostiene[0], par[1] if par[0] == sostiene[0] else par[0])
            elif sostiene and sostiene[1] in par:
                sostiene = (par[1] if par[0] == sostiene[1] else par[0], sostiene[1])
            else:
                sostiene = par
        elif tipo == "ordenado":
            ordenados.add(evento[1])
        elif tipo == "fase":
            fase = evento[1]
        elif tipo == "fin":
            terminado = True
            corriendo = False
            sostiene = None
            fase = "¡Todos ordenados! Los monstruos descansan"

    def luminosidad(c):
        return 0.299 * c[0] + 0.587 * c[1] + 0.114 * c[2]

    while True:
        dt = reloj.tick(FPS) / 1000.0
        tiempo += dt

        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if ev.type == pygame.KEYDOWN:
                if ev.key == pygame.K_ESCAPE:
                    pygame.quit()
                    sys.exit()
                elif ev.key == pygame.K_SPACE and not terminado:
                    if generador is None:
                        generador = heap_sort(valores)
                    corriendo = not corriendo
                elif ev.key == pygame.K_r:
                    reiniciar("aleatorio")
                elif ev.key == pygame.K_n:
                    reiniciar("casi")
                elif ev.key == pygame.K_v:
                    reiniciar("inverso")
                elif ev.key in (pygame.K_PLUS, pygame.K_EQUALS, pygame.K_KP_PLUS):
                    velocidad = min(120, velocidad + 2)
                elif ev.key in (pygame.K_MINUS, pygame.K_KP_MINUS):
                    velocidad = max(1, velocidad - 2)

        if corriendo:
            acumulado += dt * velocidad
            while acumulado >= 1 and corriendo:
                acumulado -= 1
                paso()

        # ---------------- movimiento suave ----------------
        k_barra = 1 - math.exp(-dt * (12 + velocidad * 1.5))
        k_brazo = 1 - math.exp(-dt * (14 + velocidad * 2))
        agarradas = set(sostiene) if (sostiene and intercambiando) else set()
        for i, v in enumerate(valores):
            x_dib[v] += (x_slot(i) - x_dib[v]) * k_barra
            objetivo = LEVANTE if v in agarradas else 0
            subida[v] += (objetivo - subida[v]) * k_barra

        if sostiene:
            v1, v2 = sostiene
            t1 = (x_dib[v1] + barra_w / 2, base_y - altura(v1) - subida[v1])
            t2 = (x_dib[v2] + barra_w / 2, base_y - altura(v2) - subida[v2])
            t_grip = 1.0 if intercambiando else 0.55
        else:
            t1 = (reposo[0], reposo[1])
            t2 = (reposo[2], reposo[3])
            t_grip = 0.0
        def seguir(kx, ky, t):
            dx = t[0] - brazo[kx]
            dy = t[1] - brazo[ky]
            if intercambiando and dx * dx + dy * dy < 70 * 70:
                # ya agarró la barra: se mueve junto con ella
                brazo[kx], brazo[ky] = t
            else:
                brazo[kx] += dx * k_brazo
                brazo[ky] += dy * k_brazo

        seguir("x1", "y1", t1)
        seguir("x2", "y2", t2)
        brazo["grip"] += (t_grip - brazo["grip"]) * k_brazo

        # ---------------- dibujo ----------------
        pantalla.blit(fondo, (0, 0))

        # murciélagos
        for m in murcielagos:
            m[0] += 40 * m[3] * dt
            if m[0] > ANCHO + 40:
                m[0] = -40
                m[1] = random.randint(30, 200)
            dibujar_murcielago(pantalla, m[0], m[1] + 12 * math.sin(tiempo * m[3]),
                               m[2], tiempo * 9 * m[3])

        # título
        sombra = f_titulo.render("HEAP SORT", True, (90, 35, 0))
        titulo = f_titulo.render("HEAP SORT", True, NARANJA)
        pantalla.blit(sombra, (margen_x + 2, 26))
        pantalla.blit(titulo, (margen_x, 24))
        dibujar_calabaza_pequena(pantalla, margen_x + titulo.get_width() + 34, 46, 20)
        sub = f_sub.render("Noche de monstruos  ·  Altura = nivel de poder (ficticio) de 1 a 15", True, TEXTO_SUAVE)
        pantalla.blit(sub, (margen_x, 68))
        ayuda = f_info.render("ESPACIO play/pausa · R aleatorio · N casi ordenado · V inverso · +/- velocidad", True, TEXTO_SUAVE)
        pantalla.blit(ayuda, (margen_x, 92))

        # barras (las que sostiene el brazo se dibujan al final, encima de las demás)
        orden = sorted(range(n), key=lambda i: valores[i] in agarradas)
        for i in orden:
            v = valores[i]
            nombre, color = PERSONAJES[v - 1]
            h = altura(v)
            x = int(x_dib[v])
            rect = pygame.Rect(x, int(base_y - h - subida[v]), barra_w, h)

            c = color
            if i in comparando:
                c = aclarar(color, 0.35)
            if i in intercambiando:
                c = aclarar(color, 0.6)

            # resplandor para barras activas
            if i in comparando:
                glow_color = COLOR_COMPARA
                glow = pygame.Surface((rect.width + 24, rect.height + 24), pygame.SRCALPHA)
                pygame.draw.rect(glow, (*glow_color, 60), glow.get_rect(), border_radius=10)
                pantalla.blit(glow, (rect.x - 12, rect.y - 12))

            pygame.draw.rect(pantalla, c, rect, border_radius=6)
            # franja de brillo y borde para dar volumen
            pygame.draw.rect(pantalla, aclarar(c, 0.25),
                             (rect.x + 3, rect.y + 4, max(3, rect.width // 5), max(2, rect.height - 8)),
                             border_radius=3)
            pygame.draw.rect(pantalla, oscurecer(c, 0.4), rect, 2, border_radius=6)

            # borde verde si ya está en su posición final
            if i in ordenados:
                pygame.draw.rect(pantalla, COLOR_ORDENADO, rect, 2, border_radius=6)

            # valor (nivel de poder) dentro de la barra, arriba
            col_txt = (20, 12, 28) if luminosidad(c) > 140 else TEXTO
            tv = f_valor.render(str(v), True, col_txt)
            pantalla.blit(tv, (rect.centerx - tv.get_width() // 2, rect.y + 4))

            # nombre vertical bajo la barra
            tn = f_nombre.render(nombre, True, TEXTO_SUAVE if i not in ordenados else COLOR_ORDENADO)
            tn = pygame.transform.rotate(tn, -90)
            pantalla.blit(tn, (int(x + barra_w / 2) - tn.get_width() // 2, base_y + 16))

        # brazo mecánico (encima de todo)
        dibujar_brazo(pantalla, brazo["x1"], brazo["y1"], brazo["x2"], brazo["y2"],
                      brazo["grip"], barra_w, sostiene is not None)

        # panel de información
        pygame.draw.rect(pantalla, (20, 10, 28), (0, ALTO - 36, ANCHO, 36))
        pygame.draw.line(pantalla, NARANJA, (0, ALTO - 36), (ANCHO, ALTO - 36), 1)
        info = f"Fase: {fase}    Comparaciones: {comparaciones}    Intercambios: {intercambios}    Velocidad: {velocidad}/s"
        pantalla.blit(f_info.render(info, True, TEXTO), (margen_x, ALTO - 27))

        pygame.display.flip()


if __name__ == "__main__":
    main()