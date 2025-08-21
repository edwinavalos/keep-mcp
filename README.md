# keep-mcp

MCP server for Google Keep

## 🔧 Fork Modifications

**This is a personal fork with enhancements for hierarchical Google Keep list management.** 

### Changes from upstream:
- **List Hierarchy Preservation**: Added `super_list_item_id` support to maintain proper indentation when copying/creating lists
- **Enhanced List Creation**: Updated `create_list` function to support hierarchical item relationships
- **Comprehensive Error Handling**: Added try-catch blocks to all MCP functions to prevent server crashes
- **Improved Serialization**: Extended `serialize_note` to capture full list structure including parent-child relationships

These changes enable proper manipulation of Google Keep lists with nested items (e.g., grocery lists with categorized sections).

**Note**: This fork is intended for personal use and integration testing. While the changes may be useful to others, there are no current plans to contribute them back upstream. If there's significant community interest, I might consider it.

![keep-mcp](https://github.com/user-attachments/assets/f50c4ae6-4d35-4bb6-a494-51c67385f1b6)

## How to use

1. Add the MCP server to your MCP servers:

```json
  "mcpServers": {
    "keep-mcp-pipx": {
      "command": "pipx",
      "args": [
        "run",
        "keep-mcp"
      ],
      "env": {
        "GOOGLE_EMAIL": "Your Google Email",
        "GOOGLE_MASTER_TOKEN": "Your Google Master Token - see README.md"
      }
    }
  }
```

2. Add your credentials:
* `GOOGLE_EMAIL`: Your Google account email address
* `GOOGLE_MASTER_TOKEN`: Your Google account master token

Check https://gkeepapi.readthedocs.io/en/latest/#obtaining-a-master-token and https://github.com/simon-weber/gpsoauth?tab=readme-ov-file#alternative-flow for more information.

## Features

* `find`: Search for notes based on a query string
* `create_note`: Create a new note with title and text (automatically adds keep-mcp label)
* `create_list`: Create a new list with hierarchical item support (supports nested items)
* `update_note`: Update a note's title and text
* `delete_note`: Mark a note for deletion
* `add_list_item`: Add items to existing lists
* `update_list_item`: Update existing list items
* `delete_list_item`: Delete items from lists

By default, all destructive and modification operations are restricted to notes that have were created by the MCP server (i.e. have the keep-mcp label). Set `UNSAFE_MODE` to `true` to bypass this restriction.

```
"env": {
  ...
  "UNSAFE_MODE": "true"
}
```

## Publishing

To publish a new version to PyPI:

1. Update the version in `pyproject.toml`
2. Build the package:
   ```bash
   pipx run build
   ```
3. Upload to PyPI:
   ```bash
   pipx run twine upload --repository pypi dist/*
   ```

## Troubleshooting

* If you get "DeviceManagementRequiredOrSyncDisabled" check https://admin.google.com/ac/devices/settings/general and turn "Turn off mobile management (Unmanaged)"
