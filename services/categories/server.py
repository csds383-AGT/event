from google.protobuf import empty_pb2

import categories_pb2
import categories_pb2_grpc
import service
from common.server import field, invoke, serve, string_id


def to_category(record):
    return categories_pb2.Category(
        id=string_id(field(record, "id")),
        name=field(record, "name", ""),
        description=field(record, "description", ""),
        event_ids=[string_id(x) for x in (field(record, "event_ids", []) or [])],
    )


class CategoryService(categories_pb2_grpc.CategoryServiceServicer):
    def CreateCategory(self, request, context):
        result = invoke(
            context, service.create_category,
            name=request.name,
            description=request.description,
            custom_id=request.custom_id or None,
            event_ids=list(request.event_ids),
        )
        return categories_pb2.IdResponse(id=string_id(result))

    def ShowCategories(self, request, context):
        records = invoke(context, service.find_categories, request.id or None)
        return categories_pb2.ShowCategoriesResponse(categories=[to_category(x) for x in records])

    def UpdateCategory(self, request, context):
        invoke(
            context, service.update_category,
            category_id=request.id,
            name=request.name if request.HasField("name") else None,
            description=request.description if request.HasField("description") else None,
            add_event_ids=list(request.add_event_ids),
            remove_event_ids=list(request.remove_event_ids),
        )
        return empty_pb2.Empty()

    def DeleteCategory(self, request, context):
        invoke(context, service.delete_category, request.id)
        return empty_pb2.Empty()


if __name__ == "__main__":
    serve("categories", (categories_pb2_grpc.add_CategoryServiceServicer_to_server, CategoryService()))
