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
    keep = get_client()
    notes = keep.find(query=query, archived=False, trashed=False)
    
    notes_data = [serialize_note(note) for note in notes]
    return json.dumps(notes_data)

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
        # Check if this is a list note and handle it differently
        if hasattr(note, 'items') and hasattr(note, 'add'):  # It's a List
            # For lists, replace all items with new text content
            note.text = text  # Use the fixed setter from gkeepapi
        else:
            # For regular notes, set text normally
            note.text = text
    
    keep.sync()  # Ensure changes are saved to the server
    return json.dumps(serialize_note(note))

@mcp.tool()
def clear_checked_items(note_id: str) -> str:
    """
    Remove all checked items from a list note.
    
    Args:
        note_id (str): The ID of the list note to clear checked items from
        
    Returns:
        str: JSON string containing the updated note's data
        
    Raises:
        ValueError: If the note doesn't exist, cannot be modified, or is not a list
    """
    keep = get_client()
    note = keep.get(note_id)
    
    if not note:
        raise ValueError(f"Note with ID {note_id} not found")
    
    if not can_modify_note(note):
        raise ValueError(f"Note with ID {note_id} cannot be modified (missing keep-mcp label and UNSAFE_MODE is not enabled)")
    
    # Check if this is a list note
    if not (hasattr(note, 'items') and hasattr(note, 'checked')):
        raise ValueError(f"Note with ID {note_id} is not a list note")
    
    # Remove all checked items
    checked_items = list(note.checked)  # Create a copy of the list
    for item in checked_items:
        note.remove(item)
    
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

def main():
    mcp.run(transport='stdio')


if __name__ == "__main__":
    main()
    