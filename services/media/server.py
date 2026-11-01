from typing import Any
import grpc
from google.protobuf import empty_pb2

import media_pb2
import media_pb2_grpc
import service
from common.server import field, invoke, serve, string_id


def to_media(record: Any) -> media_pb2.Media:
    return media_pb2.Media(
        id=string_id(field(record, "id")),
        event_id=string_id(field(record, "event_id")),
        image_url=field(record, "image_url", ""),
    )


class MediaService(media_pb2_grpc.MediaServiceServicer):
    def CreateMedia(self, request: media_pb2.CreateMediaRequest, context: grpc.ServicerContext) -> media_pb2.IdResponse:
        result = invoke(
            context, service.create_media,
            event_id=request.event_id,
            image_url=request.image_url,
            custom_id=request.custom_id or None,
        )
        return media_pb2.IdResponse(id=string_id(result))

    def ShowMedia(self, request: media_pb2.ShowMediaRequest, context: grpc.ServicerContext) -> media_pb2.ShowMediaResponse:
        records = invoke(context, service.find_media, request.id or None)
        return media_pb2.ShowMediaResponse(media=[to_media(x) for x in (records or [])])

    def UpdateMedia(self, request: media_pb2.UpdateMediaRequest, context: grpc.ServicerContext) -> empty_pb2.Empty:
        invoke(
            context, service.update_media,
            media_id=request.id,
            event_id=request.event_id if request.HasField("event_id") else None,
            image_url=request.image_url if request.HasField("image_url") else None,
        )
        return empty_pb2.Empty()

    def DeleteMedia(self, request: media_pb2.DeleteMediaRequest, context: grpc.ServicerContext) -> empty_pb2.Empty:
        invoke(context, service.delete_media, request.id)
        return empty_pb2.Empty()


if __name__ == "__main__":
    serve("media", (media_pb2_grpc.add_MediaServiceServicer_to_server, MediaService()))