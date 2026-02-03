# Arc Sidebar Export

Export pinned tabs from Arc browser organized by space. Works on **macOS** and **Windows**.

## Features

- Exports **pinned tabs only** from Arc's sidebar
- Organizes by **Spaces** with folder hierarchy preserved
- Outputs to **JSON** and/or **Chrome-compatible HTML**
- **Cross-platform**: supports macOS and Windows
- No external dependencies

## Usage

```bash
# Export both JSON and HTML (default)
python3 arc-export.py

# Export JSON only
python3 arc-export.py --json

# Export HTML only (for Chrome import)
python3 arc-export.py --html

# Custom output filename
python3 arc-export.py -o my_bookmarks

# Compact JSON (no indentation)
python3 arc-export.py --json --compact
```

## Options

| Flag | Short | Description |
|------|-------|-------------|
| `--json` | `-j` | Export as JSON |
| `--html` | `-H` | Export as HTML (Chrome format) |
| `--output` | `-o` | Output filename (without extension) |
| `--compact` | | Compact JSON output |

## Output

Files are saved to the `outputs/` directory:

```
arc-sidebar-export/
├── arc-export.py      # Main script
├── utils/
│   ├── __init__.py    # Package exports
│   ├── parser.py      # ArcSidebarParser class
│   └── exporter.py    # Exporter class
├── outputs/
│   ├── arc_pinned.json
│   └── arc_pinned.html
└── README.md
```

### JSON Format

```json
{
  "export_date": "2026-02-03T12:30:00",
  "spaces": [
    {
      "id": "...",
      "title": "UI",
      "pinned": [
        {
          "title": "Blogs",
          "type": "folder",
          "children": [
            {
              "title": "Josh W Comeau",
              "type": "tab",
              "url": "https://www.joshwcomeau.com/"
            }
          ]
        }
      ]
    }
  ]
}
```

### HTML Format

Chrome-compatible Netscape Bookmark format. Import directly into Chrome, Edge, Firefox, or Safari.

## Import into Chrome

1. Open `chrome://bookmarks`
2. Click **⋮** (three dots) → **Import bookmarks**
3. Select the `.html` file from `outputs/`

Your Arc spaces will appear as bookmark folders.

## Requirements

- Python 3.6+
- Arc browser installed on macOS or Windows

## Files

| File | Description |
|------|-------------|
| `arc-export.py` | Main CLI script |
| `utils/parser.py` | ArcSidebarParser class and platform detection |
| `utils/exporter.py` | Exporter class (JSON and HTML output) |

## How It Works

Reads Arc's `StorableSidebar.json` and extracts:
- Spaces (workspaces)
- Pinned containers
- Tabs and folders with parent-child relationships

Builds a hierarchical tree and exports to the chosen format.

### Data Location

| Platform | Path |
|----------|------|
| macOS | `~/Library/Application Support/Arc/StorableSidebar.json` |
| Windows | `%LOCALAPPDATA%\Packages\TheBrowserCompany.Arc_*\LocalCache\Local\Arc\StorableSidebar.json` |
