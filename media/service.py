from types import SimpleNamespace
from typing import Any, Optional

import concerts_pb2 # type: ignore
import concerts_pb2_grpc # type: ignore

from common import db, peers
from common.tools import is_url
from common.records import FestHubError, delete_record, find_records, insert, parse_id, update

# Define the stub for the Concerts microservice to validate event IDs
concerts_svc = peers.stub(concerts_pb2_grpc.ConcertServiceStub, "CONCERTS")


def require_concert(event_id: str) -> None:
    """Uses gRPC to ensure the referenced concert exists before linking media to it."""
    res = peers.call(concerts_svc.ShowConcerts, concerts_pb2.ShowConcertsRequest(id=event_id))
    if not getattr(res, "concerts", None):
        raise FestHubError(f"no concert with id {event_id}")


def check_media(media_record: SimpleNamespace) -> None:
    if hasattr(media_record, "image_url") and not is_url(media_record.image_url):
        raise FestHubError("image_url must be a valid HTTP/HTTPS URL")


def create_media(event_id: str, image_url: str, custom_id: Optional[str] = None) -> str:
    require_concert(event_id)

    with db.transaction():
        media_record = SimpleNamespace(
            event_id=event_id,
            image_url=image_url
        )
        check_media(media_record)
        
        # We assume the table is named "media". Adjust if your schema.sql uses a different name.
        media_id = insert("media", parse_id(custom_id), media_record, "a media asset with that ID already exists")
        return str(media_id)


def find_media(media_id: Optional[str] = None) -> list[Any]:
    # Order by "id" since media doesn't have a "name" column
    return find_records("media", media_id, "media asset", order_by="id")


def update_media(media_id: str, event_id: Optional[str] = None, image_url: Optional[str] = None) -> None:
    if event_id is not None:
        require_concert(event_id)

    with db.transaction():
        changes: dict[str, Any] = {}
        if event_id is not None:
            changes["event_id"] = event_id
        if image_url is not None:
            changes["image_url"] = image_url
            
        if changes:
            check_media(SimpleNamespace(**changes))
            update("media", media_id, "media asset", SimpleNamespace(**changes))


def delete_media(media_id: str) -> None:
    delete_record("media", media_id, "media asset")