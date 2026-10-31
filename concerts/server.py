from types import SimpleNamespace
from typing import Any
import grpc
from google.protobuf import empty_pb2

import concerts_pb2 # type: ignore
import concerts_pb2_grpc # type: ignore
import service
from common.server import field, invoke, serve, string_id

def to_concert(record: Any) -> concerts_pb2.Concert:
    return concerts_pb2.Concert(
        id=string_id(field(record, "id")),
        name=field(record, "name", ""),
        description=field(record, "description", ""),
        available_tickets=field(record, "available_tickets", 0),
        ticket_price_cents=field(record, "ticket_price", 0),
        artist_ids=[string_id(x) for x in (field(record, "artist_ids", []) or [])],
        category_ids=[string_id(x) for x in (field(record, "category_ids", []) or [])],
        media_ids=[string_id(x) for x in (field(record, "media_ids", []) or [])],
    )

class ConcertService(concerts_pb2_grpc.ConcertServiceServicer):
    def CreateConcert(
        self, request: concerts_pb2.CreateConcertRequest, context: grpc.ServicerContext
    ) -> concerts_pb2.IdResponse:
        result = invoke(
            context, service.create_concert,
            name=request.name,
            description=request.description,
            available_tickets=request.available_tickets,
            ticket_price=request.ticket_price,
            custom_id=request.custom_id or None,
            artist_ids=list(request.artist_ids),
            category_ids=list(request.category_ids),
            media_ids=list(request.media_ids),
        )
        return concerts_pb2.IdResponse(id=string_id(result))

    def ShowConcerts(
        self, request: concerts_pb2.ShowConcertsRequest, context: grpc.ServicerContext
    ) -> concerts_pb2.ShowConcertsResponse:
        records = invoke(context, service.show_concerts, request.id or None)
        return concerts_pb2.ShowConcertsResponse(concerts=[to_concert(x) for x in (records or [])])

    def UpdateConcert(
        self, request: concerts_pb2.UpdateConcertRequest, context: grpc.ServicerContext
    ) -> empty_pb2.Empty:
        invoke(
            context, service.update_concert,
            concert_id=request.id,
            name=request.name if request.HasField("name") else None,
            description=request.description if request.HasField("description") else None,
            available_tickets=request.available_tickets if request.HasField("available_tickets") else None,
            ticket_price=request.ticket_price if request.HasField("ticket_price") else None,
            add_artist_ids=list(request.add_artist_ids),
            remove_artist_ids=list(request.remove_artist_ids),
            add_category_ids=list(request.add_category_ids),
            remove_category_ids=list(request.remove_category_ids),
            add_media_ids=list(request.add_media_ids),
            remove_media_ids=list(request.remove_media_ids),
        )
        return empty_pb2.Empty()

    def DeleteConcert(
        self, request: concerts_pb2.DeleteConcertRequest, context: grpc.ServicerContext
    ) -> concerts_pb2.DeleteConcertResponse:
        result: SimpleNamespace = invoke(context, service.delete_concert, request.id) # type: ignore
        return concerts_pb2.DeleteConcertResponse(
            deleted_media_ids=[string_id(x) for x in result.deleted_media_ids],
            deleted_category_ids=[string_id(x) for x in result.deleted_category_ids],
        )

class BookingService(concerts_pb2_grpc.BookingServiceServicer):
    def BookArtist(
        self, request: concerts_pb2.BookingRequest, context: grpc.ServicerContext
    ) -> empty_pb2.Empty:
        invoke(context, service.book_artist, request.event_id, request.artist_id)
        return empty_pb2.Empty()

    def UnbookArtist(
        self, request: concerts_pb2.BookingRequest, context: grpc.ServicerContext
    ) -> empty_pb2.Empty:
        invoke(context, service.unbook_artist, request.event_id, request.artist_id)
        return empty_pb2.Empty()

    def ListBookings(
        self, request: concerts_pb2.ListBookingsRequest, context: grpc.ServicerContext
    ) -> concerts_pb2.ListBookingsResponse:
        records = invoke(context, service.list_bookings, list(request.artist_ids))
        bookings = [
            concerts_pb2.Booking(
                event_id=string_id(field(r, "event_id")),
                artist_id=string_id(field(r, "artist_id"))
            ) for r in (records or [])
        ]
        return concerts_pb2.ListBookingsResponse(bookings=bookings)

    def ForgetArtist(
        self, request: concerts_pb2.ForgetArtistRequest, context: grpc.ServicerContext
    ) -> empty_pb2.Empty:
        invoke(context, service.forget_artist, request.artist_id)
        return empty_pb2.Empty()

if __name__ == "__main__":
    serve(
        "concerts", 
        (concerts_pb2_grpc.add_ConcertServiceServicer_to_server, ConcertService()),
        (concerts_pb2_grpc.add_BookingServiceServicer_to_server, BookingService())
    )