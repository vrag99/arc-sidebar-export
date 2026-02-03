#!/usr/bin/env python3
"""
Arc Sidebar Export Tool
Exports pinned tabs from Arc browser organized by space.

Usage:
    python arc-export.py              # Export both JSON and HTML
    python arc-export.py --json       # Export JSON only
    python arc-export.py --html       # Export HTML only (Chrome-compatible)
    python arc-export.py -o FILE      # Custom output filename (without extension)
"""

import argparse
import os
import sys

from utils import ArcSidebarParser, Exporter


def main():
    parser = argparse.ArgumentParser(
        description="Export Arc browser pinned tabs organized by space.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python arc-export.py              Export both JSON and HTML
  python arc-export.py --json       Export JSON only
  python arc-export.py --html       Export HTML only (for Chrome import)
  python arc-export.py -o bookmarks Custom output filename
        """
    )

    parser.add_argument(
        '--json', '-j',
        action='store_true',
        help='Export as JSON'
    )
    parser.add_argument(
        '--html', '-H',
        action='store_true',
        help='Export as HTML (Chrome bookmarks format)'
    )
    parser.add_argument(
        '--output', '-o',
        type=str,
        default='arc_pinned',
        help='Output filename without extension (default: arc_pinned)'
    )
    parser.add_argument(
        '--compact',
        action='store_true',
        help='Compact JSON output (no indentation)'
    )

    args = parser.parse_args()

    # If neither format specified, export both
    if not args.json and not args.html:
        args.json = True
        args.html = True

    # Setup paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_dir = os.path.join(script_dir, "outputs")
    os.makedirs(output_dir, exist_ok=True)

    print("Arc Sidebar Export")
    print("=" * 50)

    # Initialize parser
    arc_parser = ArcSidebarParser()

    if not os.path.exists(arc_parser.sidebar_path):
        print(f"Error: Arc sidebar not found at {arc_parser.sidebar_path}")
        sys.exit(1)

    print(f"Source: {arc_parser.sidebar_path}\n")

    # Load and parse
    if not arc_parser.load_sidebar():
        sys.exit(1)

    stats = arc_parser.get_statistics()
    print(f"Found {stats['spaces']} spaces, {stats['tabs']} tabs, {stats['folders']} folders\n")

    data = arc_parser.parse_all()

    if not data or not data.get('spaces'):
        print("Error: No data to export")
        sys.exit(1)

    # Count pinned items
    pinned_count = sum(
        len(space.get('pinned', []))
        for space in data['spaces']
    )
    print(f"Exporting {pinned_count} pinned items from {len(data['spaces'])} spaces\n")

    # Export
    exported = []

    if args.json:
        json_path = os.path.join(output_dir, f"{args.output}.json")
        if Exporter.to_json(data, json_path, pretty=not args.compact):
            exported.append(f"JSON: {json_path}")

    if args.html:
        html_path = os.path.join(output_dir, f"{args.output}.html")
        if Exporter.to_html(data, html_path):
            exported.append(f"HTML: {html_path}")

    if exported:
        print("Exported:")
        for path in exported:
            print(f"  {path}")

        if args.html:
            print("\nTo import into Chrome:")
            print("  1. Open chrome://bookmarks")
            print("  2. Click ⋮ → Import bookmarks")
            print("  3. Select the HTML file")
    else:
        print("No files exported")
        sys.exit(1)


if __name__ == "__main__":
    main()
