"""
MCP plugin for Google Keep integration.
Provides tools for interacting with Google Keep notes through MCP.
"""

import json
from mcp.server.fastmcp import FastMCP
from .keep_api import get_client, serialize_note, can_modify_note

mcp = FastMCP("keep")

@mcp.tool()
def find(query="") -> str:
    """
    Find notes based on a search query.
    
    Args:
        query (str, optional): A string to match against the title and text
        
    Returns:
        str: JSON string containing the matching notes with their id, title, text, pinned status, color and labels
    """
    try:
        keep = get_client()
        notes = keep.find(query=query, archived=False, trashed=False)
        
        notes_data = [serialize_note(note) for note in notes]
        return json.dumps(notes_data)
    except Exception as e:
        import traceback
        error_msg = f"Error in find: {str(e)}\n{traceback.format_exc()}"
        return json.dumps({"error": error_msg})

@mcp.tool()
def create_note(title: str = None, text: str = None) -> str:
    """
    Create a new note with title and text.
    
    Args:
        title (str, optional): The title of the note
        text (str, optional): The content of the note
        
    Returns:
        str: JSON string containing the created note's data
    """
    try:
        keep = get_client()
        note = keep.createNote(title=title, text=text)
        
        # Get or create the keep-mcp label
        label = keep.findLabel('keep-mcp')
        if not label:
            label = keep.createLabel('keep-mcp')
        
        # Add the label to the note
        note.labels.add(label)
        keep.sync()  # Ensure the note is created and labeled on the server
        
        return json.dumps(serialize_note(note))
    except Exception as e:
        import traceback
        error_msg = f"Error in create_note: {str(e)}\n{traceback.format_exc()}"
        return json.dumps({"error": error_msg})

@mcp.tool()
def update_note(note_id: str, title: str = None, text: str = None) -> str:
    """
    Update a note's properties.
    
    Args:
        note_id (str): The ID of the note to update
        title (str, optional): New title for the note
        text (str, optional): New text content for the note
        
    Returns:
        str: JSON string containing the updated note's data
        
    Raises:
        ValueError: If the note doesn't exist or cannot be modified
    """
    keep = get_client()
    note = keep.get(note_id)
    
    if not note:
        raise ValueError(f"Note with ID {note_id} not found")
    
    if not can_modify_note(note):
        raise ValueError(f"Note with ID {note_id} cannot be modified (missing keep-mcp label and UNSAFE_MODE is not enabled)")
    
    if title is not None:
        note.title = title
    if text is not None:
        note.text = text
    
    keep.sync()  # Ensure changes are saved to the server
    return json.dumps(serialize_note(note))

@mcp.tool()
def delete_note(note_id: str) -> str:
    """
    Delete a note (mark for deletion).
    
    Args:
        note_id (str): The ID of the note to delete
        
    Returns:
        str: Success message
        
    Raises:
        ValueError: If the note doesn't exist or cannot be modified
    """
    keep = get_client()
    note = keep.get(note_id)
    
    if not note:
        raise ValueError(f"Note with ID {note_id} not found")
    
    if not can_modify_note(note):
        raise ValueError(f"Note with ID {note_id} cannot be modified (missing keep-mcp label and UNSAFE_MODE is not enabled)")
    
    note.delete()
    keep.sync()  # Ensure deletion is saved to the server
    return json.dumps({"message": f"Note {note_id} marked for deletion"})

@mcp.tool()
def create_list(title: str = None, items: list = None) -> str:
    """
    Create a new list with title and items.
    
    Args:
        title (str, optional): The title of the list
        items (list, optional): A list of items, each item should be a dict with 'text', optionally 'checked', and optionally 'super_list_item_id' keys
        
    Returns:
        str: JSON string containing the created list's data
    """
    try:
        keep = get_client()
        
        # Create an empty list first
        note = keep.createList(title=title, items=[])
        
        # Get or create the keep-mcp label
        label = keep.findLabel('keep-mcp')
        if not label:
            label = keep.createLabel('keep-mcp')
        
        # Add the label to the list
        note.labels.add(label)
        
        # If items provided, add them with hierarchy support
        if items:
            # First pass: create all items at top level and build a mapping
            item_mapping = {}  # Maps original item index to created ListItem
            
            import random
            sort = random.randint(1000000000, 9999999999)
            
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    text = item.get('text', '')
                    checked = item.get('checked', False)
                else:
                    # If item is just a string
                    text = str(item)
                    checked = False
                
                # Create the item
                list_item = note.add(text, checked, sort)
                sort -= note.SORT_DELTA
                item_mapping[i] = list_item
            
            # Second pass: set up hierarchy based on super_list_item_id
            # Build a mapping from original IDs to item indices first
            id_to_index = {}
            for i, item in enumerate(items):
                if isinstance(item, dict) and item.get('id'):
                    id_to_index[item['id']] = i
            
            for i, item in enumerate(items):
                if isinstance(item, dict) and item.get('super_list_item_id'):
                    super_id = item.get('super_list_item_id')
                    
                    # Find the parent item by its original ID
                    parent_index = id_to_index.get(super_id)
                    if parent_index is not None:
                        parent_item = item_mapping.get(parent_index)
                        child_item = item_mapping.get(i)
                        
                        # If we found both parent and child, indent the child under parent
                        if parent_item and child_item:
                            parent_item.indent(child_item)
        
        keep.sync()  # Ensure the list is created and labeled on the server
        
        return json.dumps(serialize_note(note))
    except Exception as e:
        import traceback
        error_msg = f"Error in create_list: {str(e)}\n{traceback.format_exc()}"
        return json.dumps({"error": error_msg})

@mcp.tool()
def add_list_item(list_id: str, text: str, checked: bool = False) -> str:
    """
    Add an item to an existing list.
    
    Args:
        list_id (str): The ID of the list to add item to
        text (str): The text of the item to add
        checked (bool, optional): Whether the item is checked
        
    Returns:
        str: JSON string containing the updated list's data
        
    Raises:
        ValueError: If the list doesn't exist, is not a list, or cannot be modified
    """
    import gkeepapi.node as node_module
    
    keep = get_client()
    note = keep.get(list_id)
    
    if not note:
        raise ValueError(f"List with ID {list_id} not found")
    
    if not isinstance(note, node_module.List):
        raise ValueError(f"Node with ID {list_id} is not a list")
    
    if not can_modify_note(note):
        raise ValueError(f"List with ID {list_id} cannot be modified (missing keep-mcp label and UNSAFE_MODE is not enabled)")
    
    note.add(text, checked)
    keep.sync()  # Ensure changes are saved to the server
    return json.dumps(serialize_note(note))

@mcp.tool()
def update_list_item(list_id: str, item_id: str, text: str = None, checked: bool = None) -> str:
    """
    Update an item in a list.
    
    Args:
        list_id (str): The ID of the list containing the item
        item_id (str): The ID of the item to update
        text (str, optional): New text for the item
        checked (bool, optional): New checked status for the item
        
    Returns:
        str: JSON string containing the updated list's data
        
    Raises:
        ValueError: If the list doesn't exist, is not a list, cannot be modified, or item not found
    """
    import gkeepapi.node as node_module
    
    keep = get_client()
    note = keep.get(list_id)
    
    if not note:
        raise ValueError(f"List with ID {list_id} not found")
    
    if not isinstance(note, node_module.List):
        raise ValueError(f"Node with ID {list_id} is not a list")
    
    if not can_modify_note(note):
        raise ValueError(f"List with ID {list_id} cannot be modified (missing keep-mcp label and UNSAFE_MODE is not enabled)")
    
    # Find the item
    item = None
    for list_item in note.items:
        if list_item.id == item_id:
            item = list_item
            break
    
    if not item:
        raise ValueError(f"Item with ID {item_id} not found in list {list_id}")
    
    if text is not None:
        item.text = text
    if checked is not None:
        item.checked = checked
    
    keep.sync()  # Ensure changes are saved to the server
    return json.dumps(serialize_note(note))

@mcp.tool()
def delete_list_item(list_id: str, item_id: str) -> str:
    """
    Delete an item from a list.
    
    Args:
        list_id (str): The ID of the list containing the item
        item_id (str): The ID of the item to delete
        
    Returns:
        str: JSON string containing the updated list's data
        
    Raises:
        ValueError: If the list doesn't exist, is not a list, cannot be modified, or item not found
    """
    import gkeepapi.node as node_module
    
    keep = get_client()
    note = keep.get(list_id)
    
    if not note:
        raise ValueError(f"List with ID {list_id} not found")
    
    if not isinstance(note, node_module.List):
        raise ValueError(f"Node with ID {list_id} is not a list")
    
    if not can_modify_note(note):
        raise ValueError(f"List with ID {list_id} cannot be modified (missing keep-mcp label and UNSAFE_MODE is not enabled)")
    
    # Find the item
    item = None
    for list_item in note.items:
        if list_item.id == item_id:
            item = list_item
            break
    
    if not item:
        raise ValueError(f"Item with ID {item_id} not found in list {list_id}")
    
    item.delete()
    keep.sync()  # Ensure changes are saved to the server
    return json.dumps(serialize_note(note))

def main():
    try:
        mcp.run(transport='stdio')
    except Exception as e:
        import traceback
        import sys
        print(f"Error in MCP server: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
    