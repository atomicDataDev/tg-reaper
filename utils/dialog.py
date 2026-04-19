"""
Dialog deletion
"""

from telethon import TelegramClient
from telethon.tl.functions.messages import DeleteHistoryRequest
from ui import print_trash, print_warning


async def delete_dialog_for_sender(
    client: TelegramClient, target, name: str
) -> bool:
    """Deletes dialog only for sender"""
    try:
        entity = await client.get_entity(target)
        peer = await client.get_input_entity(entity)
        await client(DeleteHistoryRequest(peer=peer, max_id=0, revoke=False))
        print_trash(f"{name} — диалог удалён (только у себя).")
        return True
    except Exception as e:
        print_warning(f"{name} — не удалось удалить диалог: {type(e).__name__}: {e}")
        return False