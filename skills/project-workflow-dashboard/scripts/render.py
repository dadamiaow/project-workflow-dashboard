"""Render one portable dashboard and optionally preserve a milestone snapshot."""

import argparse
from html import escape
import json
import math
from pathlib import Path
import re
from string import Template
from tempfile import NamedTemporaryFile


TEMPLATE = Path(__file__).resolve().parents[1] / "assets/dashboard.html"


def object_value(value, field):
    if not isinstance(value, dict):
        raise ValueError(f"{field} must be an object")
    return value


def text_field(item, key, where, *, required=True):
    value = item.get(key, None if required else "")
    if not isinstance(value, str) or (required and not value.strip()):
        raise ValueError(f"{where}.{key} must be text")
    return escape(value)


def list_field(item, key, where, *, required=False):
    value = item.get(key, None if required else [])
    if not isinstance(value, list) or (required and not value):
        raise ValueError(f"{where}.{key} must be {'a nonempty' if required else 'a'} list")
    return value


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def render_table(item, where):
    item = object_value(item, where)
    title = text_field(item, "title", where)
    columns = list_field(item, "columns", where, required=True)
    if any(not isinstance(col, str) or not col.strip() for col in columns):
        raise ValueError(f"{where}.columns must be nonempty text labels")
    header = "".join(f'<th scope="col">{escape(col)}</th>' for col in columns)
    html_rows = []
    for i, row in enumerate(list_field(item, "rows", where)):
        if not isinstance(row, list) or len(row) != len(columns):
            raise ValueError(f"{where}.rows[{i}] must have {len(columns)} cells")
        if any(cell is not None and not isinstance(cell, str) and not finite_number(cell) for cell in row):
            raise ValueError(f"{where}.rows[{i}] must contain text, finite numbers, or null")
        cells = "".join(f"<td>{'—' if cell is None else escape(str(cell))}</td>" for cell in row)
        html_rows.append(f"<tr>{cells}</tr>")
    return (f'<h3>{title}</h3><div class="table-wrap"><table>'
            f'<thead><tr>{header}</tr></thead><tbody>{"".join(html_rows)}</tbody></table></div>')


def render_chart(item, where):
    item = object_value(item, where)
    title = text_field(item, "title", where)
    unit = text_field(item, "unit", where, required=False)
    ceiling = item.get("max")
    if not finite_number(ceiling) or ceiling <= 0:
        raise ValueError(f"{where}.max must be a positive finite number")
    bars = []
    for i, point in enumerate(list_field(item, "values", where, required=True)):
        if (not isinstance(point, list) or len(point) != 2 or not isinstance(point[0], str)
                or not point[0].strip() or not finite_number(point[1]) or not 0 <= point[1] <= ceiling):
            raise ValueError(f"{where}.values[{i}] must be a label and a number between 0 and {ceiling}")
        label, value = point
        bars.append(f'<div class="bar"><span>{escape(label)}</span>'
                    f'<div class="track" aria-hidden="true"><div style="width:{value/ceiling:.4%}"></div></div>'
                    f'<span>{value:g}{unit}</span></div>')
    return (f"<figure><figcaption>{title} <small>0–{ceiling:g}{unit}</small></figcaption>"
            f'{"".join(bars)}</figure>')


def render_stage(item, where):
    item = object_value(item, where)
    title = text_field(item, "title", where)
    status = text_field(item, "status", where)
    detail = text_field(item, "detail", where, required=False)
    return f"<li><strong>{title}</strong> <span class=\"status\">{status}</span><p>{detail}</p></li>"


def disclosure(title, body):
    return f'<details><summary>{title}</summary><div class="detail-body">{body}</div></details>'


def render_detail(item, where):
    item = object_value(item, where)
    title = text_field(item, "title", where)
    text = text_field(item, "text", where, required=False)
    tables = render_list(item, "tables", where, render_table)
    children = render_list(item, "children", where, render_detail)
    body = (f"<p>{text}</p>" if text else "") + tables
    if children:
        body += f'<div class="subsections">{children}</div>'
    return disclosure(title, body)


def render_list(item, key, where, renderer, *, required=False):
    return "".join(renderer(entry, f"{where}.{key}[{i}]")
                   for i, entry in enumerate(list_field(item, key, where, required=required)))


def render_sources(item, where):
    sources = list_field(item, "sources", where)
    if any(not isinstance(source, str) or not source.strip() for source in sources):
        raise ValueError(f"{where}.sources must contain nonempty text")
    return "".join(f"<li>{escape(source)}</li>" for source in sources)


def render_current_step(data, label, next_label):
    if "current_step" not in data:
        return ""
    step = object_value(data["current_step"], "current_step")
    title = text_field(step, "title", "current_step")
    status = text_field(step, "status", "current_step")
    detail = text_field(step, "detail", "current_step", required=False)
    next_action = text_field(step, "next_action", "current_step", required=False)
    description = f"<p>{detail}</p>" if detail else ""
    action = f"<p><strong>{next_label}</strong> {next_action}</p>" if next_action else ""
    return (f'<aside class="current-step" aria-labelledby="current-step-title">'
            f'<h3 id="current-step-title">{label}</h3>'
            f'<p><strong>{title}</strong> <span class="status">{status}</span></p>'
            f'{description}{action}</aside>')


def render_learning(data, labels, field_labels):
    def render_entry(entry, where):
        entry = object_value(entry, where)
        title = text_field(entry, "title", where)
        rows = []
        for field, label in field_labels.items():
            value = text_field(entry, field, where, required=False)
            if value:
                rows.append(f"<dt>{label}</dt><dd>{value}</dd>")
        sources = render_sources(entry, where)
        if sources:
            rows.append(f'<dt>{labels["sources"]}</dt><dd><ul>{sources}</ul></dd>')
        body = f'<dl class="brief">{"".join(rows)}</dl>' if rows else ""
        return disclosure(title, body)

    entries = render_list(data, "learning", "dashboard", render_entry)
    if not entries:
        return ""
    return f'<h3 class="learning-heading">{labels["learning"]}</h3><div class="details">{entries}</div>'


def render_tabs(panels, label):
    if len(panels) == 1:
        return ""
    buttons = "".join(
        f'<button type="button" id="tab-{key}" role="tab" aria-controls="{key}">{title}</button>'
        for key, title, _ in panels
    )
    return f'<div id="dashboard-tabs" class="tabs" role="tablist" aria-label="{label}" hidden>{buttons}</div>'


def render(data):
    data = object_value(data, "dashboard")
    title, date, summary = (text_field(data, key, "dashboard") for key in ("title", "as_of", "summary"))
    lang = data.get("lang", "en")
    if not isinstance(lang, str) or not re.fullmatch(r"[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*", lang):
        raise ValueError("dashboard.lang must be an HTML language tag, such as zh-CN")
    chinese = lang.split("-")[0].lower() == "zh"
    labels = {
        "progress": "项目进度" if chinese else "Progress",
        "results": "关键结果" if chinese else "Key results",
        "details": "明细与来源" if chinese else "Details and sources",
        "current_step": "当前步骤" if chinese else "Current step",
        "learning": "试验与学习" if chinese else "Experiments and learning",
        "sources": "来源" if chinese else "Sources",
    }
    overrides = object_value(data.get("labels", {}), "labels")
    for key in labels.keys() & overrides.keys():
        labels[key] = text_field(overrides, key, "labels")

    field_labels = {
        "question": "问题" if chinese else "Question",
        "comparison": "比较" if chinese else "Comparison",
        "result": "结论" if chinese else "Finding",
        "next_step": "后续" if chinese else "Follow-up",
    }
    current_step = render_current_step(data, labels["current_step"], "下一步" if chinese else "Next action")
    learning = render_learning(data, labels, field_labels)
    stages = render_list(data, "stages", "dashboard", render_stage, required=True)
    charts = render_list(data, "charts", "dashboard", render_chart)
    tables = render_list(data, "tables", "dashboard", render_table)
    details = render_list(data, "details", "dashboard", render_detail)
    sources = render_sources(data, "dashboard")

    panels = [("progress", labels["progress"], f"{current_step}{learning}<ol>{stages}</ol>")]
    if charts or tables:
        charts = f'<div class="charts">{charts}</div>' if charts else ""
        panels.append(("results", labels["results"], f"{charts}{tables}"))
    if details or sources:
        sources = disclosure(labels["sources"], f"<ul>{sources}</ul>") if sources else ""
        panels.append(("details", labels["details"], f'<div class="details">{details}{sources}</div>'))

    tabs = render_tabs(panels, "切换看板" if chinese else "Dashboard views")
    sections = "".join(
        f'<section id="{key}"{" data-tab-panel" if tabs else ""}><h2>{heading}</h2>{body}</section>'
        for key, heading, body in panels
    )
    return Template(TEMPLATE.read_text(encoding="utf-8")).substitute(
        title=title, as_of=date, summary=summary, lang=lang, tabs=tabs, sections=sections,
    ).encode("utf-8")


def publish(content, output, snapshot):
    if snapshot:
        if snapshot.exists() and snapshot.read_bytes() != content:
            raise ValueError(f"Snapshot already exists with different content: {snapshot}")
        duplicate = next((path for path in sorted(snapshot.parent.glob("*.html"))
                          if path.is_file() and path.read_bytes() == content), None)
        if duplicate:
            print(f"Snapshot already saved: {duplicate}")
        else:
            snapshot.parent.mkdir(parents=True, exist_ok=True)
            with snapshot.open("xb") as file:
                try:
                    file.write(content)
                except OSError:
                    file.close()
                    snapshot.unlink()
                    raise
            print(f"Snapshot saved: {snapshot}")
    output.parent.mkdir(parents=True, exist_ok=True)
    pending = None
    try:
        with NamedTemporaryFile(dir=output.parent, suffix=".tmp", delete=False) as file:
            pending = Path(file.name)
            file.write(content)
        pending.replace(output)
    finally:
        if pending:
            pending.unlink(missing_ok=True)
    print(f"Dashboard updated: {output}")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("data", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--snapshot", type=Path)
    args = parser.parse_args()
    paths = [args.data, args.output] + ([args.snapshot] if args.snapshot else [])
    if len({path.resolve() for path in paths}) != len(paths):
        parser.error("Input, current output, and snapshot must be different files")
    if any(path.suffix.lower() != ".html" for path in paths[1:]):
        parser.error("Output and snapshot filenames must end in .html")
    try:
        publish(render(json.loads(args.data.read_bytes())), args.output, args.snapshot)
    except (OSError, ValueError, OverflowError) as error:
        parser.exit(1, f"{error}\n")


if __name__ == "__main__":
    main()
