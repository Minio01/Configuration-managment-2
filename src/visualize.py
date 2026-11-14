"""Визуализация графа: Mermaid, ASCII-дерево и изображение SVG."""

from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

NODE_HEIGHT = 32
LEVEL_GAP = 64
NODE_GAP = 24
CHAR_WIDTH = 8
NODE_PADDING = 24
MARGIN = 20
FONT_SIZE = 13
TEXT_SHIFT = 5
CURVE_OFFSET = 40
CYCLE_START = 0.3
CYCLE_END = 0.7
NODE_FILL = "#e8f0fe"
ROOT_FILL = "#c6dafc"
STROKE = "#3b5b8c"
CYCLE_STROKE = "#c0392b"


def back_edges(graph):
    """Вернуть множество рёбер, замыкающих найденные циклы."""
    return {(cycle[-2], cycle[-1]) for cycle in graph.cycles}


def to_mermaid(graph):
    """Сформировать описание графа на языке диаграмм Mermaid."""
    ids = {name: f"n{index}" for index, name in enumerate(graph.nodes())}
    cyclic = back_edges(graph)
    lines = ["graph TD"]
    for name, node_id in ids.items():
        lines.append(f'    {node_id}["{name}"]')
    for name in graph.nodes():
        for dep in graph.dependencies(name):
            arrow = "-.->" if (name, dep) in cyclic else "-->"
            lines.append(f"    {ids[name]} {arrow} {ids[dep]}")
    return "\n".join(lines)


def ascii_tree(graph):
    """Сформировать ASCII-дерево зависимостей корневого пакета."""
    lines = [graph.root]
    add_branches(graph, graph.root, "", lines)
    return "\n".join(lines)


def add_branches(graph, name, prefix, lines, path=None):
    """Рекурсивно добавить в lines ветви дерева для пакета name."""
    path = (path or []) + [name]
    deps = graph.dependencies(name)
    for index, dep in enumerate(deps):
        last = index == len(deps) - 1
        mark = " (cycle)" if dep in path else ""
        lines.append(f"{prefix}{'`-- ' if last else '|-- '}{dep}{mark}")
        if not mark:
            child_prefix = prefix + ("    " if last else "|   ")
            add_branches(graph, dep, child_prefix, lines, path)


def assign_levels(graph):
    """Распределить пакеты по уровням (длина самого длинного пути)."""
    order = list(reversed(graph.load_order()))
    position = {name: index for index, name in enumerate(order)}
    levels = {name: 0 for name in order}
    for name in order:
        for dep in graph.dependencies(name):
            if position[dep] > position[name]:
                levels[dep] = max(levels[dep], levels[name] + 1)
    rows = {}
    for name in graph.nodes():
        rows.setdefault(levels[name], []).append(name)
    return [rows[level] for level in sorted(rows)]


def node_width(name):
    """Ширина прямоугольника узла для имени пакета."""
    return len(name) * CHAR_WIDTH + NODE_PADDING


def layout(graph):
    """Вычислить координаты узлов: имя -> (x, y, ширина)."""
    rows = assign_levels(graph)
    row_widths = [
        sum(node_width(name) for name in row) + NODE_GAP * (len(row) - 1)
        for row in rows
    ]
    total_width = max(row_widths) + 2 * MARGIN
    boxes = {}
    for level, row in enumerate(rows):
        x = (total_width - row_widths[level]) / 2
        y = MARGIN + level * (NODE_HEIGHT + LEVEL_GAP)
        for name in row:
            boxes[name] = (x, y, node_width(name))
            x += node_width(name) + NODE_GAP
    height = MARGIN * 2 + len(rows) * NODE_HEIGHT
    height += (len(rows) - 1) * LEVEL_GAP
    return boxes, total_width, height


def svg_node(name, box, is_root):
    """SVG-элементы прямоугольника и подписи узла."""
    x, y, width = box
    fill = ROOT_FILL if is_root else NODE_FILL
    return (
        f'<rect x="{x:.1f}" y="{y}" width="{width}" height="{NODE_HEIGHT}" '
        f'rx="6" fill="{fill}" stroke="{STROKE}"/>\n'
        f'<text x="{x + width / 2:.1f}" '
        f'y="{y + NODE_HEIGHT / 2 + TEXT_SHIFT}" '
        f'text-anchor="middle">{escape(name)}</text>'
    )


def svg_edge(source, target, cyclic):
    """SVG-элемент стрелки от узла source к узлу target."""
    sx, sy, sw = source
    tx, ty, tw = target
    if not cyclic:
        return (
            f'<line x1="{sx + sw / 2:.1f}" y1="{sy + NODE_HEIGHT}" '
            f'x2="{tx + tw / 2:.1f}" y2="{ty}" stroke="{STROKE}" '
            'marker-end="url(#arrow)"/>'
        )
    start = (sx + sw, sy + NODE_HEIGHT * CYCLE_START)
    end = (tx + tw, ty + NODE_HEIGHT * CYCLE_END)
    control = max(start[0], end[0]) + CURVE_OFFSET
    return (
        f'<path d="M {start[0]:.1f} {start[1]} C {control:.1f} {start[1]} '
        f'{control:.1f} {end[1]} {end[0]:.1f} {end[1]}" fill="none" '
        f'stroke="{CYCLE_STROKE}" stroke-dasharray="5 3" '
        'marker-end="url(#arrow-cycle)"/>'
    )


def svg_marker(marker_id, color):
    """SVG-описание наконечника стрелки."""
    return (
        f'<marker id={quoteattr(marker_id)} viewBox="0 0 10 10" refX="10" '
        'refY="5" markerWidth="8" markerHeight="8" orient="auto">'
        f'<path d="M 0 0 L 10 5 L 0 10 z" fill="{color}"/></marker>'
    )


def to_svg(graph):
    """Сформировать изображение графа в формате SVG."""
    boxes, width, height = layout(graph)
    cyclic = back_edges(graph)
    width += CURVE_OFFSET if cyclic else 0
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height}" viewBox="0 0 {width:.0f} {height}" '
        f'font-family="sans-serif" font-size="{FONT_SIZE}">',
        f'<rect width="100%" height="100%" fill="white"/>',
        "<defs>" + svg_marker("arrow", STROKE)
        + svg_marker("arrow-cycle", CYCLE_STROKE) + "</defs>",
    ]
    for name in graph.nodes():
        for dep in graph.dependencies(name):
            edge = (name, dep)
            parts.append(svg_edge(boxes[name], boxes[dep], edge in cyclic))
    for name in graph.nodes():
        parts.append(svg_node(name, boxes[name], name == graph.root))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def save_svg(graph, path):
    """Сохранить изображение графа в SVG-файл."""
    Path(path).write_text(to_svg(graph), encoding="utf-8")
