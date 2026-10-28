"""Построение графа зависимостей рекурсивным обходом в глубину (DFS)."""


class GraphError(Exception):
    """Ошибка построения графа зависимостей."""


class DependencyGraph:
    """Граф зависимостей: пакет -> список его прямых зависимостей."""

    def __init__(self, root):
        """Создать пустой граф с корневым пакетом root."""
        self.root = root
        self.edges = {}
        self.cycles = []

    def nodes(self):
        """Вернуть пакеты графа в порядке их обнаружения."""
        return list(self.edges)

    def dependencies(self, name):
        """Вернуть прямые зависимости пакета."""
        return self.edges.get(name, [])


def is_excluded(name, substring):
    """Проверить, исключается ли пакет фильтром по подстроке."""
    return bool(substring) and substring.lower() in name.lower()


class GraphBuilder:
    """Рекурсивный DFS-обход зависимостей с фильтрацией пакетов."""

    def __init__(self, get_dependencies, filter_substring=""):
        """Задать функцию получения зависимостей и подстроку фильтра."""
        self.get_dependencies = get_dependencies
        self.filter_substring = filter_substring
        self.graph = None
        self.path = []

    def build(self, root):
        """Построить граф транзитивных зависимостей пакета root."""
        if is_excluded(root, self.filter_substring):
            raise GraphError(
                f"пакет {root} исключён фильтром "
                f"{self.filter_substring!r}"
            )
        self.graph = DependencyGraph(root)
        self.path = []
        self.visit(root)
        return self.graph

    def visit(self, name):
        """Посетить пакет и рекурсивно обойти его зависимости."""
        self.path.append(name)
        deps = [
            dep for dep in self.get_dependencies(name)
            if not is_excluded(dep, self.filter_substring)
        ]
        self.graph.edges[name] = deps
        for dep in deps:
            if dep in self.path:
                start = self.path.index(dep)
                self.graph.cycles.append(self.path[start:] + [dep])
            elif dep not in self.graph.edges:
                self.visit(dep)
        self.path.pop()


def build_graph(root, get_dependencies, filter_substring=""):
    """Построить граф зависимостей пакета root."""
    return GraphBuilder(get_dependencies, filter_substring).build(root)
