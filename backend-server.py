import sys
from pathlib import Path

from google.protobuf import empty_pb2

PROJECT_DIR = Path(__file__).resolve().parent
LOGIC_DIR = PROJECT_DIR / "logic"
if LOGIC_DIR.is_dir():
    sys.path.insert(0, str(LOGIC_DIR))

import services
import concerts_pb2
import concerts_pb2_grpc
import categories_pb2
import categories_pb2_grpc
import media_pb2
import media_pb2_grpc
from common.server import field, invoke, serve, string_id


def to_concert(record):
    return concerts_pb2.Concert(
        id=string_id(field(record, "id")),
        name=field(record, "name", ""),
        description=field(record, "description", ""),
        available_tickets=field(record, "available_tickets", 0),
        # The services/repository layer stores prices as integer cents.
        ticket_price_cents=field(record, "ticket_price", field(record, "ticket_price_cents", 0)),
        artist_ids=[string_id(x) for x in (field(record, "artist_ids", []) or [])],
        category_ids=[string_id(x) for x in (field(record, "category_ids", []) or [])],
        media_ids=[string_id(x) for x in (field(record, "media_ids", []) or [])],
    )


def to_category(record):
    return categories_pb2.Category(
        id=string_id(field(record, "id")),
        name=field(record, "name", ""),
        description=field(record, "description", ""),
        event_ids=[string_id(x) for x in (field(record, "event_ids", []) or [])],
    )


def to_media(record):
    return media_pb2.Media(
        id=string_id(field(record, "id")),
        event_id=string_id(field(record, "event_id")),
        image_url=field(record, "image_url", ""),
    )

class CategoryService(categories_pb2_grpc.CategoryServiceServicer):
    def CreateCategory(self, request, context):
        result = invoke(
            context, services.create_category,
            name=request.name,
            description=request.description,
            custom_id=request.custom_id or None,
            event_ids=list(request.event_ids),
        )
        return categories_pb2.IdResponse(id=string_id(result))

    def ShowCategories(self, request, context):
        records = invoke(context, services.find_categories, request.id or None)
        return categories_pb2.ShowCategoriesResponse(categories=[to_category(x) for x in records]) # type: ignore

    def UpdateCategory(self, request, context):
        invoke(
            context, services.update_category,
            category_id=request.id,
            name=request.name if request.HasField("name") else None,
            description=request.description if request.HasField("description") else None,
            add_event_ids=list(request.add_event_ids),
            remove_event_ids=list(request.remove_event_ids),
        )
        return empty_pb2.Empty()

    def DeleteCategory(self, request, context):
        invoke(context, services.delete_category, request.id)
        return empty_pb2.Empty()

if __name__ == "__main__":
    serve(
        "logic",
        (categories_pb2_grpc.add_CategoryServiceServicer_to_server, CategoryService()),
    )
