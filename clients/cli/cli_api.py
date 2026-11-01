import os
from types import SimpleNamespace

import grpc

import artists_pb2
import artists_pb2_grpc
import categories_pb2
import categories_pb2_grpc
import concerts_pb2
import concerts_pb2_grpc
import media_pb2
import media_pb2_grpc


class FestHubError(Exception):
    def __init__(self, message, code=None):
        super().__init__(message)
        self.code = code


GATEWAY_TARGET = (
    f"{os.getenv('GATEWAY_HOST', 'localhost')}:"
    f"{os.getenv('GATEWAY_PORT', '9080')}"
)
RPC_TIMEOUT_SECONDS = float(os.getenv("GRPC_TIMEOUT_SECONDS", "3"))
channel = grpc.insecure_channel(GATEWAY_TARGET)
concerts = concerts_pb2_grpc.ConcertServiceStub(channel)
artists = artists_pb2_grpc.ArtistServiceStub(channel)
categories = categories_pb2_grpc.CategoryServiceStub(channel)
media = media_pb2_grpc.MediaServiceStub(channel)


def call(method, request):
    try:
        return method(request, timeout=RPC_TIMEOUT_SECONDS)
    except grpc.RpcError as error:
        raise FestHubError(error.details() or error.code().name.lower(), code=error.code()) from error


def create_concert(name, description, available_tickets, ticket_price, custom_id=None,
                   artist_ids=(), category_ids=(), media_ids=()):
    response = call(concerts.CreateConcert, concerts_pb2.CreateConcertRequest(
        name=name,
        description=description,
        available_tickets=available_tickets,
        ticket_price=ticket_price,
        custom_id=custom_id or "",
        artist_ids=list(artist_ids),
        category_ids=list(category_ids),
        media_ids=list(media_ids),
    ))
    return response.id


def find_concerts(event_id=None):
    response = call(concerts.ShowConcerts, concerts_pb2.ShowConcertsRequest(id=event_id or ""))
    return list(response.concerts)


def update_concert(event_id, name=None, description=None, available_tickets=None, ticket_price=None,
                   add_artist_ids=(), remove_artist_ids=(), add_category_ids=(), remove_category_ids=(),
                   add_media_ids=(), remove_media_ids=()):
    request = concerts_pb2.UpdateConcertRequest(
        id=event_id,
        add_artist_ids=list(add_artist_ids),
        remove_artist_ids=list(remove_artist_ids),
        add_category_ids=list(add_category_ids),
        remove_category_ids=list(remove_category_ids),
        add_media_ids=list(add_media_ids),
        remove_media_ids=list(remove_media_ids),
    )
    if name is not None:
        request.name = name
    if description is not None:
        request.description = description
    if available_tickets is not None:
        request.available_tickets = available_tickets
    if ticket_price is not None:
        request.ticket_price = ticket_price
    call(concerts.UpdateConcert, request)


def delete_concert(event_id):
    response = call(concerts.DeleteConcert, concerts_pb2.DeleteConcertRequest(id=event_id))
    return list(response.deleted_media_ids), list(response.deleted_category_ids)


def create_artist(name, booking_contact, custom_id=None, event_ids=()):
    response = call(artists.CreateArtist, artists_pb2.CreateArtistRequest(
        name=name,
        booking_contact=booking_contact,
        custom_id=custom_id or "",
        event_ids=list(event_ids),
    ))
    return response.id


def find_artists(artist_id=None):
    response = call(artists.ShowArtists, artists_pb2.ShowArtistsRequest(id=artist_id or ""))
    return [
        SimpleNamespace(
            id=artist.id,
            name=artist.name,
            booking_contact=artist.booking_contact,
            event_ids=list(artist.event_ids),
        )
        for artist in response.artists
    ]


def update_artist(artist_id, name=None, booking_contact=None, add_event_ids=(), remove_event_ids=()):
    request = artists_pb2.UpdateArtistRequest(
        id=artist_id,
        add_event_ids=list(add_event_ids),
        remove_event_ids=list(remove_event_ids),
    )
    if name is not None:
        request.name = name
    if booking_contact is not None:
        request.booking_contact = booking_contact
    call(artists.UpdateArtist, request)


def delete_artist(artist_id):
    call(artists.DeleteArtist, artists_pb2.DeleteArtistRequest(id=artist_id))


def create_category(name, description, custom_id=None, event_ids=()):
    response = call(categories.CreateCategory, categories_pb2.CreateCategoryRequest(
        name=name,
        description=description,
        custom_id=custom_id or "",
        event_ids=list(event_ids),
    ))
    return response.id


def find_categories(category_id=None):
    response = call(categories.ShowCategories, categories_pb2.ShowCategoriesRequest(id=category_id or ""))
    return [
        SimpleNamespace(
            id=category.id,
            name=category.name,
            description=category.description,
            event_ids=list(category.event_ids),
        )
        for category in response.categories
    ]


def update_category(category_id, name=None, description=None, add_event_ids=(), remove_event_ids=()):
    request = categories_pb2.UpdateCategoryRequest(
        id=category_id,
        add_event_ids=list(add_event_ids),
        remove_event_ids=list(remove_event_ids),
    )
    if name is not None:
        request.name = name
    if description is not None:
        request.description = description
    call(categories.UpdateCategory, request)


def delete_category(category_id):
    call(categories.DeleteCategory, categories_pb2.DeleteCategoryRequest(id=category_id))


def create_media(event_id, image_url, custom_id=None):
    response = call(media.CreateMedia, media_pb2.CreateMediaRequest(
        event_id=event_id,
        image_url=image_url,
        custom_id=custom_id or "",
    ))
    return response.id


def find_media(media_id=None):
    response = call(media.ShowMedia, media_pb2.ShowMediaRequest(id=media_id or ""))
    return [
        SimpleNamespace(id=item.id, event_id=item.event_id, image_url=item.image_url)
        for item in response.media
    ]


def update_media(media_id, event_id=None, image_url=None):
    request = media_pb2.UpdateMediaRequest(id=media_id)
    if event_id is not None:
        request.event_id = event_id
    if image_url is not None:
        request.image_url = image_url
    call(media.UpdateMedia, request)


def delete_media(media_id):
    call(media.DeleteMedia, media_pb2.DeleteMediaRequest(id=media_id))
