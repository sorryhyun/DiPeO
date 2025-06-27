"""Domain service for Notion integration with high-level operations."""

import json
from datetime import datetime
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from dipeo_core import SupportsFile, SupportsNotion


class NotionIntegrationDomainService:
    """High-level domain service for Notion operations combined with file operations."""

    def __init__(self, notion_service: "SupportsNotion", file_service: "SupportsFile"):
        """Initialize with required infrastructure services."""
        self._notion = notion_service
        self._file = file_service

    async def sync_page_to_file(
        self, page_id: str, file_path: str, api_key: str, format: str = "markdown"
    ) -> dict[str, Any]:
        """Sync a Notion page to a local file."""
        try:
            # Get page content from Notion
            page_data = await self._notion.get_page(page_id, api_key)

            # Get page properties
            properties = await self._notion.get_page_properties(page_id, api_key)

            # Get page blocks (content)
            blocks = await self._notion.get_blocks(page_id, api_key)

            # Convert to desired format
            if format == "markdown":
                content = self._convert_to_markdown(page_data, properties, blocks)
            elif format == "json":
                content = json.dumps(
                    {"page": page_data, "properties": properties, "blocks": blocks},
                    indent=2,
                )
            else:
                content = str(blocks)  # Raw format

            # Save to file
            await self._file.write_file(file_path, content)

            return {
                "success": True,
                "page_id": page_id,
                "file_path": file_path,
                "format": format,
                "size": len(content),
                "synced_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "page_id": page_id,
                "file_path": file_path,
            }

    async def sync_file_to_page(
        self, file_path: str, page_id: str, api_key: str, append: bool = False
    ) -> dict[str, Any]:
        """Sync a local file to a Notion page."""
        try:
            # Read file content
            content = await self._file.read_file(file_path)

            # Convert content to Notion blocks
            blocks = self._convert_to_notion_blocks(content)

            if append:
                # Append to existing page
                for block in blocks:
                    await self._notion.append_block(page_id, block, api_key)
            else:
                # Replace page content
                # First, get and delete existing blocks
                existing_blocks = await self._notion.get_blocks(page_id, api_key)
                for block in existing_blocks:
                    if "id" in block:
                        await self._notion.delete_block(block["id"], api_key)

                # Then append new blocks
                for block in blocks:
                    await self._notion.append_block(page_id, block, api_key)

            return {
                "success": True,
                "file_path": file_path,
                "page_id": page_id,
                "blocks_added": len(blocks),
                "synced_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "file_path": file_path,
                "page_id": page_id,
            }

    async def search_and_export(
        self, query: str, api_key: str, export_dir: str, limit: int = 10
    ) -> dict[str, Any]:
        """Search Notion and export results to files."""
        try:
            # Search in Notion
            results = await self._notion.search(query, api_key)

            exported_files = []

            # Limit results
            for i, result in enumerate(results[:limit]):
                if result.get("object") == "page":
                    page_id = result["id"]
                    title = self._extract_title(result)

                    # Create safe filename
                    safe_title = "".join(c for c in title if c.isalnum() or c in " -_")[
                        :50
                    ]
                    file_name = f"{safe_title}_{page_id[:8]}.md"
                    file_path = f"{export_dir}/{file_name}"

                    # Export page
                    export_result = await self.sync_page_to_file(
                        page_id=page_id,
                        file_path=file_path,
                        api_key=api_key,
                        format="markdown",
                    )

                    if export_result["success"]:
                        exported_files.append(
                            {"page_id": page_id, "title": title, "file_path": file_path}
                        )

            return {
                "success": True,
                "query": query,
                "total_results": len(results),
                "exported_count": len(exported_files),
                "exported_files": exported_files,
            }

        except Exception as e:
            return {"success": False, "error": str(e), "query": query}

    async def create_page_from_template(
        self,
        parent_id: str,
        title: str,
        template_file: str,
        api_key: str,
        properties: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Create a new Notion page from a file template."""
        try:
            # Read template content
            template_content = await self._file.read_file(template_file)

            # Create page
            page_data = {
                "parent": {"page_id": parent_id}
                if "-" in parent_id
                else {"database_id": parent_id},
                "properties": properties
                or {"title": {"title": [{"text": {"content": title}}]}},
            }

            created_page = await self._notion.create_page(page_data, api_key)
            page_id = created_page["id"]

            # Add content from template
            blocks = self._convert_to_notion_blocks(template_content)
            for block in blocks:
                await self._notion.append_block(page_id, block, api_key)

            return {
                "success": True,
                "page_id": page_id,
                "title": title,
                "parent_id": parent_id,
                "blocks_added": len(blocks),
                "created_at": datetime.utcnow().isoformat(),
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "title": title,
                "parent_id": parent_id,
            }

    def _convert_to_markdown(
        self,
        page_data: dict[str, Any],
        properties: dict[str, Any],
        blocks: list[dict[str, Any]],
    ) -> str:
        """Convert Notion page data to markdown format."""
        markdown_parts = []

        # Add title
        title = self._extract_title(page_data)
        if title:
            markdown_parts.append(f"# {title}\n")

        # Add properties as metadata
        if properties:
            markdown_parts.append("## Properties\n")
            for key, value in properties.items():
                if isinstance(value, dict) and "type" in value:
                    prop_value = self._extract_property_value(value)
                    if prop_value:
                        markdown_parts.append(f"- **{key}**: {prop_value}")
            markdown_parts.append("")

        # Convert blocks to markdown
        markdown_parts.append("## Content\n")
        for block in blocks:
            md_block = self._convert_block_to_markdown(block)
            if md_block:
                markdown_parts.append(md_block)

        return "\n".join(markdown_parts)

    def _convert_block_to_markdown(self, block: dict[str, Any]) -> str:
        """Convert a single Notion block to markdown."""
        block_type = block.get("type", "")

        if block_type == "paragraph":
            text = self._extract_text(block.get("paragraph", {}))
            return text + "\n" if text else ""

        if block_type == "heading_1":
            text = self._extract_text(block.get("heading_1", {}))
            return f"# {text}\n" if text else ""

        if block_type == "heading_2":
            text = self._extract_text(block.get("heading_2", {}))
            return f"## {text}\n" if text else ""

        if block_type == "heading_3":
            text = self._extract_text(block.get("heading_3", {}))
            return f"### {text}\n" if text else ""

        if block_type == "bulleted_list_item":
            text = self._extract_text(block.get("bulleted_list_item", {}))
            return f"- {text}" if text else ""

        if block_type == "numbered_list_item":
            text = self._extract_text(block.get("numbered_list_item", {}))
            return f"1. {text}" if text else ""

        if block_type == "code":
            code_block = block.get("code", {})
            text = self._extract_text(code_block)
            language = code_block.get("language", "")
            return f"```{language}\n{text}\n```\n" if text else ""

        if block_type == "quote":
            text = self._extract_text(block.get("quote", {}))
            return f"> {text}\n" if text else ""

        return ""

    def _convert_to_notion_blocks(self, content: str) -> list[dict[str, Any]]:
        """Convert text content to Notion blocks."""
        blocks = []
        lines = content.split("\n")

        for line in lines:
            if line.strip():
                # Simple paragraph block for now
                # Could be enhanced to detect markdown and create appropriate blocks
                blocks.append(
                    {
                        "object": "block",
                        "type": "paragraph",
                        "paragraph": {
                            "rich_text": [{"type": "text", "text": {"content": line}}]
                        },
                    }
                )

        return blocks

    def _extract_title(self, page_data: dict[str, Any]) -> str:
        """Extract title from page data."""
        properties = page_data.get("properties", {})

        # Try common title property names
        for prop_name in ["Title", "title", "Name", "name"]:
            if prop_name in properties:
                return self._extract_property_value(properties[prop_name])

        # Fallback to first title-type property
        for prop in properties.values():
            if prop.get("type") == "title":
                return self._extract_property_value(prop)

        return "Untitled"

    def _extract_property_value(self, prop: dict[str, Any]) -> str:
        """Extract value from a Notion property."""
        prop_type = prop.get("type", "")

        if prop_type == "title":
            title_arr = prop.get("title", [])
            return "".join(t.get("plain_text", "") for t in title_arr)

        if prop_type == "rich_text":
            text_arr = prop.get("rich_text", [])
            return "".join(t.get("plain_text", "") for t in text_arr)

        if prop_type == "number":
            return str(prop.get("number", ""))

        if prop_type == "select":
            select = prop.get("select", {})
            return select.get("name", "")

        if prop_type == "multi_select":
            options = prop.get("multi_select", [])
            return ", ".join(opt.get("name", "") for opt in options)

        if prop_type == "date":
            date = prop.get("date", {})
            return date.get("start", "")

        if prop_type == "checkbox":
            return "Yes" if prop.get("checkbox") else "No"

        return ""

    def _extract_text(self, text_block: dict[str, Any]) -> str:
        """Extract plain text from a text block."""
        rich_text = text_block.get("rich_text", [])
        return "".join(t.get("plain_text", "") for t in rich_text)
