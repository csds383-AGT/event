from contextlib import suppress
from types import SimpleNamespace

import concerts_pb2
import concerts_pb2_grpc
from common import db, peers
from common.records import FestHubError, check_lengths, find_records, insert, parse_id, require, update

concerts = peers.stub(concerts_pb2_grpc.ConcertServiceStub, "CONCERTS")


def check_category(category):
    check_lengths(category.name, category.description)


def canonical(event_id):
    uuid = db.to_uuid(event_id)
    return event_id if uuid is None else str(uuid)


def require_concert(event_id):
    if not event_id:
        raise FestHubError(f"no concert with id {event_id}")
    peers.call(concerts.ShowConcerts, concerts_pb2.ShowConcertsRequest(id=event_id))
    return canonical(event_id)


def event_links():
    response = peers.call(concerts.ShowConcerts, concerts_pb2.ShowConcertsRequest())
    links = {}
    for concert in response.concerts:
        for category_id in concert.category_ids:
            links.setdefault(category_id, []).append(concert.id)
    return links


def link_request(event_id, category_id, change):
    return concerts_pb2.UpdateConcertRequest(id=event_id, **{f"{change}_category_ids": [category_id]})


def change_links(category_id, add_event_ids=(), remove_event_ids=()):
    linked = set(event_links().get(category_id, []))
    add_event_ids = [require_concert(event_id) for event_id in add_event_ids]
    remove_event_ids = [canonical(event_id) for event_id in remove_event_ids]
    for event_id in add_event_ids:
        if event_id in linked:
            raise FestHubError("that event is already in this category")
    for event_id in remove_event_ids:
        if event_id not in linked:
            raise FestHubError(f"event {event_id} is not in category {category_id}")
    done = []
    try:
        for change, undo, event_ids in [("add", "remove", add_event_ids), ("remove", "add", remove_event_ids)]:
            for event_id in event_ids:
                peers.call(concerts.UpdateConcert, link_request(event_id, category_id, change))
                done.append((undo, event_id))
    except FestHubError:
        for undo, event_id in reversed(done):
            with suppress(FestHubError):
                peers.call(concerts.UpdateConcert, link_request(event_id, category_id, undo))
        raise


def create_category(name, description, custom_id=None, event_ids=()):
    category = SimpleNamespace(name=name, description=description)
    check_category(category)
    with db.transaction():
        category_id = insert("categories", parse_id(custom_id), category, "a category with that ID already exists")
    try:
        change_links(category_id, add_event_ids=event_ids)
    except FestHubError:
        db.delete("categories", category_id)
        raise
    return category_id


def find_categories(category_id=None):
    categories = find_records("categories", category_id, "category")
    if not categories:
        return []
    links = event_links()
    return [SimpleNamespace(**category._asdict(), event_ids=sorted(links.get(category.id, [])))
            for category in categories]


def update_category(category_id, name=None, description=None, add_event_ids=(), remove_event_ids=()):
    with db.transaction():
        category = update("categories", category_id, "category", SimpleNamespace(name=name, description=description))
        check_category(category)
        change_links(category.id, add_event_ids, remove_event_ids)


def delete_category(category_id):
    with db.transaction():
        category = require("categories", category_id, "category")
        change_links(category.id, remove_event_ids=event_links().get(category.id, []))
        db.delete("categories", category.id)
