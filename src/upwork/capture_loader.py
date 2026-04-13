import ast
from pathlib import Path


def load_capture_dicts(file_path: Path) -> dict[str, dict]:
    source = file_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    out: dict[str, dict] = {}
    wanted_names = {"cookies", "headers", "params", "json_data"}

    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in wanted_names:
                try:
                    out[target.id] = ast.literal_eval(node.value)
                except Exception:
                    pass

    return out
