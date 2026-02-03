"""
Arc Sidebar Exporter
Export utilities for Arc sidebar data to various formats.
"""

import html
import json
from typing import Dict, List


class Exporter:
    """Export utilities for Arc sidebar data"""

    @staticmethod
    def to_json(data: Dict, output_path: str, pretty: bool = True) -> bool:
        """Export data to JSON file"""
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error writing JSON: {e}")
            return False

    @staticmethod
    def to_html(data: Dict, output_path: str) -> bool:
        """Export data to Chrome-compatible bookmarks HTML"""

        def format_item(item: Dict, indent: int = 1) -> List[str]:
            result = []
            prefix = '    ' * indent

            if item.get('type') == 'folder':
                title = html.escape(item.get('title', 'Untitled'))
                result.append(f'{prefix}<DT><H3>{title}</H3>')
                result.append(f'{prefix}<DL><p>')
                for child in item.get('children', []):
                    result.extend(format_item(child, indent + 1))
                result.append(f'{prefix}</DL><p>')
            else:
                title = html.escape(item.get('title', 'Untitled'))
                url = html.escape(item.get('url', ''))
                if url:
                    result.append(f'{prefix}<DT><A HREF="{url}">{title}</A>')

            return result

        lines = [
            '<!DOCTYPE NETSCAPE-Bookmark-file-1>',
            '<!-- Exported from Arc Browser -->',
            '<META HTTP-EQUIV="Content-Type" CONTENT="text/html; charset=UTF-8">',
            '<TITLE>Bookmarks</TITLE>',
            '<H1>Bookmarks</H1>',
            '<DL><p>'
        ]

        for space in data.get('spaces', []):
            space_title = html.escape(space.get('title', 'Untitled Space'))
            pinned_items = space.get('pinned', [])

            if not pinned_items:
                continue

            lines.append(f'    <DT><H3>{space_title}</H3>')
            lines.append('    <DL><p>')

            for item in pinned_items:
                lines.extend(format_item(item, 2))

            lines.append('    </DL><p>')

        lines.append('</DL><p>')

        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(lines))
            return True
        except IOError as e:
            print(f"Error writing HTML: {e}")
            return False
