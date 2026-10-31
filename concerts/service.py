from typing import Any, Iterable, Optional
from types import SimpleNamespace
from common import db
from common.records import FestHubError, check_lengths, find_records, insert, parse_id, require, update
from common.base_service import to_cents

def check_concert(concert: SimpleNamespace) -> None:
    if hasattr(concert, "name"):
        check_lengths(concert.name, getattr(concert, "description", ""))
    if getattr(concert, "available_tickets", 0) < 0:
        raise FestHubError("available tickets cannot be negative")

def sync_links(table: str, column: str, event_id: str, adds: Iterable[str], removes: Iterable[str]) -> None:
    for target_id in (adds or []):
        db.link(table, event_id, target_id)
    for target_id in (removes or []):
        db.unlink(table, column, event_id, target_id)

def create_concert(
    name: str, 
    description: str, 
    available_tickets: int, 
    ticket_price: str, 
    custom_id: Optional[str] = None, 
    artist_ids: Iterable[str] = (), 
    category_ids: Iterable[str] = (), 
    media_ids: Iterable[str] = ()
) -> str:
    with db.transaction():
        concert = SimpleNamespace(
            name=name,
            description=description,
            available_tickets=available_tickets,
            ticket_price=to_cents(ticket_price)
        )
        check_concert(concert)
        
        event_id = insert("concert_events", parse_id(custom_id), concert, "a concert with that ID already exists")
        str_event_id = str(event_id)

        sync_links("bookings", "artist_id", str_event_id, artist_ids, [])
        sync_links("event_categories", "category_id", str_event_id, category_ids, [])
        sync_links("event_media", "media_id", str_event_id, media_ids, [])
        return str_event_id

def show_concerts(concert_id: Optional[str] = None) -> list[SimpleNamespace]:
    concerts: list[Any] = find_records("concert_events", concert_id, "concert", order_by="name")
    if not concerts:
        return []
    
    event_ids: list[str] = [str(c.id) for c in concerts]

    def get_links(table: str, col: str) -> dict[str, list[str]]:
        rows = db.fetchall(f"SELECT event_id, {col} FROM {table} WHERE event_id = ANY(%s::uuid[])", [event_ids])
        mapping: dict[str, list[str]] = {}
        for r in rows:
            mapping.setdefault(str(getattr(r, "event_id")), []).append(str(getattr(r, col)))
        return mapping

    artist_map = get_links("bookings", "artist_id")
    category_map = get_links("event_categories", "category_id")
    media_map = get_links("event_media", "media_id")

    return [
        SimpleNamespace(
            **c._asdict(),
            artist_ids=artist_map.get(str(c.id), []),
            category_ids=category_map.get(str(c.id), []),
            media_ids=media_map.get(str(c.id), [])
        ) for c in concerts
    ]

def update_concert(
    concert_id: str, 
    name: Optional[str] = None, 
    description: Optional[str] = None, 
    available_tickets: Optional[int] = None, 
    ticket_price: Optional[str] = None,
    add_artist_ids: Iterable[str] = (), 
    remove_artist_ids: Iterable[str] = (),
    add_category_ids: Iterable[str] = (), 
    remove_category_ids: Iterable[str] = (),
    add_media_ids: Iterable[str] = (), 
    remove_media_ids: Iterable[str] = ()
) -> None:
    with db.transaction():
        changes: dict[str, Any] = {}
        if name is not None: changes["name"] = name
        if description is not None: changes["description"] = description
        if available_tickets is not None: changes["available_tickets"] = available_tickets
        if ticket_price is not None: changes["ticket_price"] = to_cents(ticket_price)
        
        if changes:
            check_concert(SimpleNamespace(**changes))
            update("concert_events", concert_id, "concert", SimpleNamespace(**changes))
        
        sync_links("bookings", "artist_id", concert_id, add_artist_ids, remove_artist_ids)
        sync_links("event_categories", "category_id", concert_id, add_category_ids, remove_category_ids)
        sync_links("event_media", "media_id", concert_id, add_media_ids, remove_media_ids)

def delete_concert(concert_id: str) -> SimpleNamespace:
    with db.transaction():
        require("concert_events", concert_id, "concert")
        
        cats = [str(getattr(r, "category_id")) for r in db.fetchall("SELECT category_id FROM event_categories WHERE event_id = %s", [db.to_uuid(concert_id)])]
        medias = [str(getattr(r, "media_id")) for r in db.fetchall("SELECT media_id FROM event_media WHERE event_id = %s", [db.to_uuid(concert_id)])]
        
        db.delete("concert_events", concert_id)
        
        orphaned_cats: list[str] = []
        if cats:
            still_used_cats = {str(getattr(r, "category_id")) for r in db.fetchall("SELECT DISTINCT category_id FROM event_categories WHERE category_id = ANY(%s::uuid[])", [cats])}
            orphaned_cats = [c for c in cats if c not in still_used_cats]
            
        orphaned_medias: list[str] = []
        if medias:
            still_used_medias = {str(getattr(r, "media_id")) for r in db.fetchall("SELECT DISTINCT media_id FROM event_media WHERE media_id = ANY(%s::uuid[])", [medias])}
            orphaned_medias = [m for m in medias if m not in still_used_medias]

        return SimpleNamespace(deleted_category_ids=orphaned_cats, deleted_media_ids=orphaned_medias)

def book_artist(event_id: str, artist_id: str) -> None:
    with db.transaction():
        if not db.link("bookings", event_id, artist_id):
            raise FestHubError("artist is already booked for this event")

def unbook_artist(event_id: str, artist_id: str) -> None:
    with db.transaction():
        db.unlink("bookings", "artist_id", event_id, artist_id)

def list_bookings(artist_ids: Iterable[str] = ()) -> list[Any]:
    if not artist_ids:
        return []
    uuids = [db.to_uuid(aid) for aid in artist_ids if db.to_uuid(aid) is not None]
    if not uuids:
        return []
    return db.fetchall("SELECT event_id, artist_id FROM bookings WHERE artist_id = ANY(%s::uuid[])", [uuids])

def forget_artist(artist_id: str) -> None:
    with db.transaction():
        db.rowcount("DELETE FROM bookings WHERE artist_id = %s", [db.to_uuid(artist_id)])