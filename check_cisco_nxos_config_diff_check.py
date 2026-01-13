"""
Check to compare device configuration against a reference template.

Algorithm:
- Retrieve the current running configuration from the device.
- Dynamically load the 'confdiff' module from the user's netaudit project directory.
- Use the 'generate_audit' function from 'confdiff' to compare the current configuration against a predefined template (e.g., 'nexus_ref').
- Capture the audit results, including status, observations, and comments.ion of the module.
- Steps taken to perform the configuration comparison.
"""

import re
import os
import tempfile
import uuid
import textdistance
from jinja2 import Environment, FileSystemLoader

TEMPLATE_MAP = {} # Should be defined in the user's netaudit project directory
DELIM = "\uF000"
HTML_TEMPLATE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Config Differ</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        * {
            box-sizing: border-box;
        }

        html, body {
            height: 100%;
            margin: 0;
            padding: 0;
            overflow: hidden; 
        }

        body {
            font-family: 'Inter', sans-serif;
            font-size: 12px;
            background: #ffffff;
            color: #222;
            display: flex;
            flex-direction: column;
        }

        i {
            margin-right: 8px;
        }

        .toolbar {
            position: sticky;
            top: 0;
            z-index: 100;
            height: 48px;
            min-height: 42px;
            padding: 6px 8px;
            background: #ffffff;
            border-bottom: 1px solid #d0d7e2;
            display: flex;
            align-items: center;
        }

        .toolbar button {
            padding: 8px;
            font-size: 12px;
            margin-right: 6px;
            cursor: pointer;
            border: 1px solid #c7ccd6;
            background: #f3f6fb;
            border-radius: 3px;
        }

        .toolbar button:hover {
            background: #e8eef9;
        }

        .toolbar .sep {
            width: 1px;
            height: 18px;
            background: #ccc;
            margin: 0 6px;
        }

        .toolbar label {
            margin-right: 12px;
            cursor: pointer;
        }

        .toolbar input[type="checkbox"] {
            vertical-align: middle;
            margin-right: 4px;
        }

        /* Filter toggle buttons */

        .filter-btn {
            border-color: #c7ccd6;
            background: #f3f6fb;
            color: #222;
        }

        .filter-btn.active {
            background: #1e5bb8;
            color: #ffffff;
            border-color: #1e5bb8;
        }

        .filter-btn.active:hover {
            background: #154a9c;
            border-color: #154a9c;
        }

        .main-layout {
            flex: 1;
            display: flex;
            min-height: 0;
        }

        .diff-pane {
            flex: 1;
            overflow-y: auto;
            padding-right: 6px;
            margin: 0 8px;
            background: #ffffff;
        }

        .card {
            --indent: calc(var(--depth) * 14px);
            margin: 10px 4px 10px var(--indent);
            border: 1px solid #d0d7e2;
            border-radius: 4px;
            background: #ffffff;
            position: relative;
        }

        /* vertical hierarchy line */

        .card::before {
            content: "";
            position: absolute;
            left: -8px;
            top: 0;
            bottom: 0;
            width: 1px;
            background: #d0d7e2;
        }

        .card[data-depth="0"]::before {
            display: none;
        }

        .card-header {
            background: #f3f6fb;
            color: #1e5bb8;
            font-weight: 600;
            padding: 6px 10px;
            border-bottom: 1px solid #d0d7e2;
            cursor: pointer;
            user-select: none;
            display: flex;
            align-items: center;
        }

        .toggle-icon {
            transition: transform 0.2s ease;
            margin-right: 6px;
        }

        .card.collapsed .toggle-icon {
            transform: rotate(-90deg);
        }

        .card-body {
            padding: 4px 0;
        }

        .card.collapsed .card-body {
            display: none;
        }

        .card.is-removed {
            border-color: #d93025;
        }

        .card.is-removed .card-header {
            background: #ffebeb;
            border-bottom-color: #d93025;
            color: #d93025;
        }

        .card.is-added {
            border-color: #188038;
        }

        .card.is-added .card-header {
            background: #e6ffed;
            border-bottom-color: #188038;
            color: #188038;
        }

        .item {
            padding: 6px 8px;
            margin: 0 4px;
            border-left: 3px solid transparent;
            border-radius: 3px;
        }

        /* Added */

        .item.is-added {
            background: #e6ffed;
            border-left-color: #188038;
        }

        .item.is-added i {
            color: #188038;
        }

        /* Removed */

        .item.is-removed {
            background: #ffecec;
            border-left-color: #d93025;
        }

        .item.is-removed i {
            color: #d93025;
        }

        /* Changed */

        .item.is-changed {
            background: #fff6e5;
            border-left-color: #f4a100;
        }

        .item.is-changed i {
            color: #f4a100;
        }

        /* Unchanged */

        .item.is-same {
            background: #ffffff;
            border-left-color: #e0e0e0;
        }

        .item.is-same i {
            color: #888;
            opacity: 0.6;
        }

        .diff-char {
            color: #d93025;
            background: #ffcccc;
            padding: 0 1px;
            border-radius: 2px;
        }

        .arrow {
            margin: 0 8px;
        }

        .raw-pane {
            width: 40%;
            background: #f9fafc;
            border-left: 1px solid #d0d7e2;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .raw-pane.hidden {
            display: none;
        }

        .raw-header {
            display: flex;
            align-items: center;
            background: #eef2f8;
            border-bottom: 1px solid #d0d7e2;
        }

        .raw-header button {
            font-size: 12px;
        }

        .raw-tab {
            padding: 6px 12px;
            border: none;
            background: transparent;
            cursor: pointer;
            font-weight: 600;
        }

        .raw-tab.active {
            background: #ffffff;
            border-bottom: 2px solid #1e5bb8;
            color: #1e5bb8;
        }

        .raw-close {
            margin-left: auto;
            padding: 6px 10px;
            border: none;
            background: transparent;
            cursor: pointer;
        }

        .raw-content {
            flex: 1;
            padding: 8px;
            font-family: 'Inter', monospace;
            line-height: 1.8;
            overflow-y: auto;
            background: #ffffff;
            display: none;
        }

        .raw-content.active {
            display: block;
        }
    </style>
</head>
<body>
<div class="toolbar">
    <button class="filter-btn" data-filter="is-added">
        <i class="fas fa-plus"></i>Added
    </button>
    <button class="filter-btn active" data-filter="is-removed">
        <i class="fas fa-minus"></i>Removed
    </button>
    <button class="filter-btn active" data-filter="is-changed">
        <i class="fas fa-not-equal"></i>Changed
    </button>
    <button class="filter-btn" data-filter="is-unchanged">
        <i class="fas fa-equals"></i>Same
    </button>

    <span class="sep"></span>

    <button id="expand-all">
        <i class="fas fa-expand"></i>Expand All
    </button>
    <button id="collapse-all">
        <i class="fas fa-compress"></i>Collapse All
    </button>
    <button id="show-raw">
        <i class="fas fa-book"></i>Raw
    </button>
</div>

<div class="main-layout">
    <div class="diff-pane">
        {{ content | safe }}
    </div>

    <div id="raw-pane" class="raw-pane hidden">
        <div class="raw-header">
            <button class="raw-tab active" data-target="raw-base">Base</button>
            <button class="raw-tab" data-target="raw-target">Target</button>
            <button id="close-raw" class="raw-close">
                <i class="fas fa-times"></i>
            </button>
        </div>

        <pre id="raw-base" class="raw-content active">{{ base_config | e }}</pre>
        <pre id="raw-target" class="raw-content">{{ target_config | e }}</pre>

    </div>
</div>
<script>
    /* ---------- Section Toggle ---------- */
    document.querySelectorAll('.card-header').forEach(header => {
        header.addEventListener('click', () => {
            header.closest('.card').classList.toggle('collapsed');
        });
    });

    /* ---------- Expand / Collapse ---------- */
    document.getElementById('expand-all').onclick = () => {
        document.querySelectorAll('.card').forEach(c => c.classList.remove('collapsed'));
    };

    document.getElementById('collapse-all').onclick = () => {
        document.querySelectorAll('.card').forEach(c => c.classList.add('collapsed'));
    };

    /* ---------- Filter Toggle Buttons ---------- */
    function applyFilters() {
        const enabled = new Set(
            Array.from(document.querySelectorAll('.filter-btn.active'))
                .map(btn => btn.dataset.filter)
        );

        document.querySelectorAll('.item').forEach(item => {
            const visible = [...item.classList].some(cls => enabled.has(cls));
            item.style.display = visible ? '' : 'none';
        });

        updateCardVisibility();
    }

    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            btn.classList.toggle('active');
            applyFilters();
        });
    });

    /* ---------- Hide empty cards ---------- */
    function updateCardVisibility() {
        document.querySelectorAll('.card').forEach(card => {
            const visibleItems = card.querySelectorAll('.item:not([style*="display: none"])');
            card.style.display = visibleItems.length ? '' : 'none';
        });
    }

    /* Initial state */
    applyFilters();

    /* ---------- Raw Pane Toggle ---------- */
    const rawPane = document.getElementById('raw-pane');
    const showRawBtn = document.getElementById('show-raw');
    const closeRawBtn = document.getElementById('close-raw');

    showRawBtn.onclick = () => {
        rawPane.classList.toggle('hidden');
    };

    closeRawBtn.onclick = () => {
        rawPane.classList.add('hidden');
    };

    /* ---------- Raw Tabs ---------- */
    document.querySelectorAll('.raw-tab').forEach(tab => {
        tab.addEventListener('click', () => {
            document.querySelectorAll('.raw-tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.raw-content').forEach(c => c.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(tab.dataset.target).classList.add('active');
        });
    });
</script>
</body>
</html>"""


class ConfigDiffer:
    """ Class to compare two configuration strings and identify differences.

    Attributes:
        target_cfg (str): The target configuration string.
        base_cfg (str): The base configuration string.
        target_parsed (dict): Parsed representation of the target configuration.
        base_parsed (dict): Parsed representation of the base configuration.
        results (dict): Comparison results between target and base configurations.
    """

    def __init__(self, target_cfg, base_cfg):
        """ Initialize the ConfigDiffer with target and base configuration strings. """
        self.target_cfg = target_cfg
        self.base_cfg = base_cfg
        self.target_parsed = {}
        self.base_parsed = {}
        self.results = {}

    def compare(self):
        """ Compare the target and base configurations and store the results. """

        def left_prefix_similarity(a, b):
            a_tokens = a.split()
            b_tokens = b.split()

            max_len = max(len(a_tokens), len(b_tokens))
            if max_len == 0:
                return 0.0

            match_len = 0
            for at, bt in zip(a_tokens, b_tokens):
                if at == bt:
                    match_len += 1
                else:
                    break

            return match_len / max_len

        def token_jaccard(a, b):
            a_set = set(a.split())
            b_set = set(b.split())
            if not a_set and not b_set:
                return 1.0
            return len(a_set & b_set) / len(a_set | b_set)

        def cisco_similarity(a, b):
            a_tokens = a.split()
            b_tokens = b.split()

            # Fast reject: different command families
            if not a_tokens or not b_tokens or a_tokens[0] != b_tokens[0]:
                return 0.0

            # Fast reject: huge token length mismatch
            if abs(len(a_tokens) - len(b_tokens)) > 4:
                return 0.0

            prefix_score = left_prefix_similarity(a, b)
            token_score = token_jaccard(a, b)

            # Strong left bias
            return (0.7 * prefix_score) + (0.3 * token_score)

        # ----------------- main logic -----------------

        self.target_parsed = self.parse(self.target_cfg)
        self.base_parsed = self.parse(self.base_cfg)
        self.used_target_lines = set()
        self.results = {}

        for line_num, base_item in self.base_parsed.items():
            base_string = base_item["string"]
            base_path = base_item["path"]
            base_is_parent = base_item["is_parent"]

            candidates = [
                item for item in self.target_parsed.values()
                if item["path"] == base_path and id(item) not in self.used_target_lines
            ]

            best_match = None
            best_score = -1.0

            for candidate in candidates:
                target_string = candidate["string"]

                # Parent commands must match exactly
                if base_is_parent:
                    if base_string == target_string:
                        best_match = candidate
                        best_score = 1.0
                        break
                    continue

                score = cisco_similarity(base_string, target_string)

                if score > best_score:
                    best_match = candidate
                    best_score = score

            # Threshold for non-parent commands
            is_matched = best_match is not None and best_score >= 0.6

            if is_matched:
                self.used_target_lines.add(id(best_match))

                a = base_string
                b = best_match["string"]
                min_len = min(len(a), len(b))

                diff_positions = [
                                     i for i in range(min_len) if a[i] != b[i]
                                 ] + list(range(min_len, max(len(a), len(b))))

                matched_string = b
            else:
                matched_string = ""
                diff_positions = list(range(len(base_string)))

            self.results[line_num] = {
                "string": base_string,
                "best_match": matched_string,
                "is_parent": base_is_parent,
                "similarity_score": best_score,
                "is_matched": is_matched,
                "diff_positions": diff_positions,
                "path": base_path,
            }

        # ----------------- added target-only lines -----------------

        next_line = max(self.results.keys(), default=0) + 1

        for target_item in self.target_parsed.values():
            if id(target_item) in self.used_target_lines:
                continue

            self.results[next_line] = {
                "string": target_item["string"],
                "best_match": "",
                "is_parent": target_item["is_parent"],
                "similarity_score": -2.0,
                "is_matched": False,
                "diff_positions": list(range(len(target_item["string"]))),
                "path": target_item["path"],
                "is_added": True,
            }
            next_line += 1

    def parse(self, cfg):
        """ Parse the configuration string into a structured format. """
        lines = cfg.splitlines()
        result = {}
        path_stack = []

        def indent(line):
            return len(line) - len(line.lstrip(" "))

        for i, line in enumerate(lines):
            stripped_line = line.strip()
            if not stripped_line:
                continue

            indent_level = indent(line)

            while path_stack and path_stack[-1][0] >= indent_level:
                path_stack.pop()

            current_path = DELIM.join(p[1] for p in path_stack)

            is_parent = False
            for j in range(i + 1, len(lines)):
                if lines[j].strip():
                    if indent(lines[j]) > indent_level:
                        is_parent = True
                    break

            result[len(result) + 1] = {
                "string": stripped_line,
                "path": current_path,
                "is_parent": is_parent
            }
            path_stack.append((indent_level, stripped_line))

        return result


class DiffRenderer:
    """ Class to render the diff results as an HTML string.
    Attributes:
        differ (ConfigDiffer): The ConfigDiffer instance containing comparison results.
        path_scores (dict): Mapping of paths to their similarity scores.
        tree (dict): Hierarchical tree structure of the diff results.
        html (str): The rendered HTML string.
    """

    def __init__(self, differ):
        """ Initialize the DiffRenderer with a ConfigDiffer instance. """
        self.differ = differ
        self.path_scores = {}
        self.tree = {}
        self.html = ""

    def render(self):
        """Render the diff results as an HTML string."""
        self._build_tree()

        html = []

        global_items = self.tree.pop("root_items", [])
        if global_items:
            html.append(self._render_section("global", {"root_items": global_items}, depth=0))

        for section, subtree in self.tree.items():
            html.append(self._render_section(section, subtree, depth=0))

        env = Environment(loader=FileSystemLoader('.'))
        template = env.from_string(HTML_TEMPLATE)

        self.html = template.render(
            content="\n".join(html),
            target_config=self.differ.target_cfg,
            base_config=self.differ.base_cfg,
        )
        return self.html

    def save(self, output_file):
        """Save the rendered HTML diff to a file."""
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(self.html)

    def _build_tree(self):
        """ Build a hierarchical tree structure from the diff results. """
        for item in self.differ.results.values():
            path = [item['path'], item['string']] if item['path'] else [item['string']]
            self.path_scores[f'{DELIM}'.join(path)] = item.get("similarity_score", 0)

            node = self.tree
            if item["path"]:
                for part in item["path"].split(DELIM):
                    node = node.setdefault(part, {})

            if not (item["is_parent"] and not item["is_matched"]):
                node.setdefault("root_items", []).append(item)

    def _render_section(self, title, subtree, depth=0):
        """Render a section of the diff tree."""
        section = []

        for key, value in subtree.items():
            if key == "root_items":
                section.extend(self._render_item(item) for item in value)
            else:
                section.append(self._render_section(key, value, depth + 1))

        if not section:
            return ""

        state = self._get_section_state(subtree)
        card_cls = f"card is-{state}" if state else "card"

        return f'''
            <div class="{card_cls}" data-depth="{depth}" style="--depth: {depth};">
                <div class="card-header">
                    <i class="fas fa-chevron-down toggle-icon"></i>{title}
                </div>
                <div class="card-body">
                    {''.join(section)}
                </div>
            </div>
        '''

    def _render_item(self, item):
        """ Render a single diff item. """
        if item.get("is_added"): return self._render_simple_item(item, "is-added", "plus")
        if not item["is_matched"]: return self._render_simple_item(item, "is-removed", "minus")
        if item["similarity_score"] < 1.0: return self._render_changed_item(item)
        if item["is_parent"]: return ""

        return self._render_simple_item(item, "is-unchanged", "equals")

    def _render_simple_item(self, item, cls, icon):
        return (
            f'<div class="item {cls}" data-type="{cls}">'
            f'<i class="fas fa-{icon}"></i>'
            f'{item["string"]}'
            f'</div>'
        )

    def _render_changed_item(self, item):
        """Render a changed item."""
        left = self._highlight_diff(item["string"], item["diff_positions"])
        right = self._highlight_diff(item["best_match"], item["diff_positions"])

        return (
            f'<div class="item is-changed" data-type="is-changed">'
            f'<i class="fas fa-not-equal"></i>'
            f'{left}<span class="arrow"><i class="fas fa-arrow-right"></i></span>{right}'
            f'</div>'
        )

    def _get_section_state(self, subtree):
        """ Determine the state of a section based on its items. """
        items = subtree.get("root_items")
        if not items:
            return None

        score = self.path_scores.get(items[0].get("path"))
        return {-1: "removed", -2: "added"}.get(score)

    def _highlight_diff(self, text, diff_positions):
        """ Highlight differing characters in a string. """
        if not diff_positions:
            return text

        out = []
        for i, ch in enumerate(text):
            out.append(f'<span class="diff-char">{ch}</span>') if i in diff_positions else out.append(ch)
        return "".join(out)


class ConfigAuditDiffCheck:
    NAME = "Configuration Difference Check"
    VERSION = "1.0.0"
    AUTHOR = "Netaudit AI Assistant"
    TAGS = ["Configuration", "Diff", "Compliance"]
    DESCRIPTION = (
        "This check compares the device's current configuration against a "
        "reference template to identify any discrepancies or unauthorized changes."
    )
    COMPLEXITY = 4

    def __init__(self, device, context=None):
        self.device = device
        self.context = context or {}
        self.REQUESTS = {
            "device": self.device,
            "command": "show running-config",
            "handler": "handle_initial"
        }
        self.RESULTS = {
            "status": 0,
            "observation": "",
            "comments": []
        }

    def load_template(self):
        # For this example, we use a hardcoded template name.
        # In practice, this could be parameterized or determined based on device attributes.
        template_name = "nexus_ref"
        template_path = TEMPLATE_MAP.get(template_name)

        if not TEMPLATE_MAP.get(template_name):
            raise ValueError(f"Template '{template_name}' not found in TEMPLATE_MAP.")

        with open(template_path, "r") as f:
            return f.read(), template_path

    def handle_initial(self, device, cmd, output):
        try:
            base_cfg, template_path = self.load_template()

            tmp_dir = tempfile.gettempdir()
            filename = f"config_diff_{uuid.uuid4().hex}.html"
            html_path = os.path.join(tmp_dir, filename)

            differ = ConfigDiffer(output, base_cfg)
            differ.compare()
            renderer = DiffRenderer(differ)
            renderer.render()
            renderer.save(html_path)

            stats = {
                "unchanged": len(re.findall(r'class="item\s+is-unchanged"', renderer.html)),
                "changed": len(re.findall(r'class="item\s+is-changed"', renderer.html)),
                "added": len(re.findall(r'class="item\s+is-added"', renderer.html)),
                "removed": len(re.findall(r'class="item\s+is-removed"', renderer.html)),
            }
            baseline_total = (stats["unchanged"] + stats["changed"] + stats["removed"])
            match_percent = (round((stats["unchanged"] / baseline_total) * 100) if baseline_total else 100)
            if stats["changed"] == 0 and stats["removed"] == 0:
                audit_results = ("COMPLIANT", 1)
            elif match_percent >= 80:
                audit_results = ("PARTIALLY COMPLIANT", 4)
            else:
                audit_results = ("NON-COMPLIANT", 3)

            self.RESULTS["status"] = audit_results[1]
            self.RESULTS["observation"] = (
                f"{audit_results[0]} - Match {match_percent}% "
                f"({stats['unchanged']} unchanged, {stats['changed']} changed, "
                f"{stats['removed']} removed, {stats['added']} added)"
            )
            self.RESULTS["comments"] = [
                f'Comparing against template: {template_path}',
                (
                    f'<div style="display: flex; gap: 8px; padding: 8px 0;">'
                    f'<a href="/render_html?path={html_path}" target="_blank" rel="noopener noreferrer">'
                    f'<button type="button"><i class="fas fa-external-link-alt"></i>'
                    f'View Comparision</button>'
                    f'</div>'
                )
            ]
        except Exception as e:
            self.RESULTS["status"] = 5
            self.RESULTS["observation"] = f"Error during configuration diff check: {str(e)}"
            self.RESULTS["comments"].append(
                "An error occurred while performing the configuration diff check. "
                "Please review the error message and ensure that the Flask context "
                "is correctly provided."
            )
        finally:
            self.REQUESTS.clear()


CHECK_CLASS = ConfigAuditDiffCheck
