"""
Arc Sidebar Parser
Parses Arc browser sidebar data from StorableSidebar.json.
"""

import glob
import json
import os
import platform
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional


def get_default_arc_path() -> str:
    """Get the default Arc browser data path based on the current platform"""
    system = platform.system()

    if system == "Darwin":  # macOS
        return os.path.expanduser("~/Library/Application Support/Arc")

    elif system == "Windows":
        # Arc on Windows is installed via Microsoft Store
        # Path: %LOCALAPPDATA%\Packages\TheBrowserCompany.Arc_*\LocalCache\Local\Arc
        local_app_data = os.environ.get("LOCALAPPDATA", "")
        if not local_app_data:
            local_app_data = os.path.expanduser("~\\AppData\\Local")

        packages_path = os.path.join(local_app_data, "Packages")
        # Find the Arc package folder (the suffix may vary)
        arc_pattern = os.path.join(packages_path, "TheBrowserCompany.Arc_*")
        arc_packages = glob.glob(arc_pattern)

        if arc_packages:
            # Use the first match (there should typically be only one)
            return os.path.join(arc_packages[0], "LocalCache", "Local", "Arc")

        # Fallback to the known common suffix
        return os.path.join(
            packages_path,
            "TheBrowserCompany.Arc_ttt1ap7aakyb4",
            "LocalCache",
            "Local",
            "Arc"
        )

    else:
        raise OSError(f"Unsupported platform: {system}. Only macOS and Windows are supported.")


class ArcSidebarParser:
    """Parser for Arc browser sidebar data (StorableSidebar.json)"""

    def __init__(self, arc_path: str = None):
        if arc_path is None:
            arc_path = get_default_arc_path()

        self.sidebar_path = os.path.join(arc_path, "StorableSidebar.json")
        self.data = None
        self.items_map: Dict[str, Dict] = {}
        self.spaces_map: Dict[str, Dict] = {}

    def load_sidebar(self) -> bool:
        """Load sidebar data from StorableSidebar.json"""
        try:
            with open(self.sidebar_path, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
            return True
        except FileNotFoundError:
            print(f"Error: Sidebar file not found at {self.sidebar_path}")
            return False
        except json.JSONDecodeError as e:
            print(f"Error: Failed to parse sidebar file: {e}")
            return False

    @staticmethod
    def convert_timestamp(timestamp: float) -> str:
        """Convert Arc/macOS timestamp to ISO format"""
        try:
            if timestamp <= 0:
                return ""
            mac_epoch = datetime(2001, 1, 1, tzinfo=timezone.utc)
            dt = datetime.fromtimestamp(mac_epoch.timestamp() + timestamp)
            return dt.isoformat()
        except (ValueError, OSError, TypeError):
            return ""

    def _build_items_map(self):
        """Build a map of item ID -> item data"""
        self.items_map = {}
        sync_state = self.data.get("sidebarSyncState", {})
        items = sync_state.get("items", [])

        i = 0
        while i < len(items):
            item = items[i]
            if isinstance(item, str):
                item_id = item
                if i + 1 < len(items) and isinstance(items[i + 1], dict):
                    item_data = items[i + 1].get("value", items[i + 1])
                    self.items_map[item_id] = item_data
                    i += 2
                else:
                    i += 1
            elif isinstance(item, dict):
                item_data = item.get("value", item)
                if "id" in item_data:
                    self.items_map[item_data["id"]] = item_data
                i += 1
            else:
                i += 1

    def _build_spaces_map(self):
        """Build a map of space ID -> space data"""
        self.spaces_map = {}
        sync_state = self.data.get("sidebarSyncState", {})
        space_models = sync_state.get("spaceModels", [])

        i = 0
        while i < len(space_models):
            item = space_models[i]
            if isinstance(item, str):
                space_id = item
                if i + 1 < len(space_models) and isinstance(space_models[i + 1], dict):
                    space_data = space_models[i + 1].get("value", space_models[i + 1])
                    self.spaces_map[space_id] = space_data
                    i += 2
                else:
                    i += 1
            elif isinstance(item, dict):
                space_data = item.get("value", item)
                if "id" in space_data:
                    self.spaces_map[space_data["id"]] = space_data
                i += 1
            else:
                i += 1

    def _parse_item(self, item_id: str) -> Optional[Dict[str, Any]]:
        """Parse a single item and its children recursively"""
        if item_id not in self.items_map:
            return None

        item = self.items_map[item_id]
        tab_data = item.get("data", {}).get("tab", {})

        result = {
            "id": item.get("id"),
            "title": item.get("title") or tab_data.get("savedTitle", "Untitled"),
            "type": "folder" if not tab_data else "tab",
        }

        if tab_data:
            url = tab_data.get("savedURL", "")
            result["url"] = url.replace("\\/", "/")
            result["type"] = "tab"

        created_at = item.get("createdAt")
        if created_at:
            result["created_at"] = self.convert_timestamp(created_at)

        last_active = tab_data.get("timeLastActiveAt") if tab_data else None
        if last_active:
            result["last_active_at"] = self.convert_timestamp(last_active)

        children_ids = item.get("childrenIds", [])
        if children_ids:
            result["type"] = "folder"
            children = []
            for child_id in children_ids:
                child = self._parse_item(child_id)
                if child:
                    children.append(child)
            if children:
                result["children"] = children

        return result

    def _find_root_items_for_container(self, container_id: str) -> List[str]:
        """Find all items that have this container as their parent"""
        return [
            item_id for item_id, item in self.items_map.items()
            if item.get("parentID") == container_id
        ]

    def _parse_space(self, space_id: str) -> Optional[Dict[str, Any]]:
        """Parse a space and its pinned contents"""
        if space_id not in self.spaces_map:
            return None

        space = self.spaces_map[space_id]
        result = {
            "id": space_id,
            "title": space.get("title", "Untitled Space"),
            "pinned": []
        }

        new_container_ids = space.get("newContainerIDs", [])
        in_pinned_section = False

        for item in new_container_ids:
            if isinstance(item, dict):
                if "pinned" in item:
                    in_pinned_section = True
                elif "unpinned" in item:
                    in_pinned_section = False
            elif isinstance(item, str) and in_pinned_section:
                container_id = item
                root_items = self._find_root_items_for_container(container_id)
                for item_id in root_items:
                    parsed = self._parse_item(item_id)
                    if parsed:
                        result["pinned"].append(parsed)

        return result

    def parse_all(self) -> Dict[str, Any]:
        """Parse all spaces and their pinned contents"""
        if not self.data:
            if not self.load_sidebar():
                return {}

        self._build_items_map()
        self._build_spaces_map()

        result = {
            "export_date": datetime.now().isoformat(),
            "source": "StorableSidebar.json",
            "spaces": []
        }

        for space_id in self.spaces_map:
            space_data = self._parse_space(space_id)
            if space_data:
                result["spaces"].append(space_data)

        return result

    def get_statistics(self) -> Dict[str, int]:
        """Get statistics about the sidebar"""
        if not self.data:
            if not self.load_sidebar():
                return {}

        self._build_items_map()
        self._build_spaces_map()

        tabs = 0
        folders = 0

        for item in self.items_map.values():
            tab_data = item.get("data", {}).get("tab", {})
            if tab_data and tab_data.get("savedURL"):
                tabs += 1
            elif item.get("childrenIds"):
                folders += 1

        return {
            "spaces": len(self.spaces_map),
            "tabs": tabs,
            "folders": folders
        }
