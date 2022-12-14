"""
Contains all the search routes.
"""
import datetime
from typing import List

from app import utils
from app import models
from app import serializer
from app.lib import searchlib
from flask import Blueprint
from flask import request

search_bp = Blueprint("search", __name__, url_prefix="/")


SEARCH_COUNT = 10
"""The max amount of items to return per request"""


class SearchResults:
    """
    Holds all the search results.
    """

    query: str = ""
    tracks: list[models.Track] = []
    albums: list[models.Album] = []
    playlists: list[models.Playlist] = []
    artists: list[models.Artist] = []


class DoSearch:
    """Class containing the methods that perform searching."""

    def __init__(self, query: str) -> None:
        """
        :param :str:`query`: the search query.
        """
        self.query = query
        SearchResults.query = query

    def search_tracks(self):
        """Calls :class:`SearchTracks` which returns the tracks that fuzzily match
        the search terms. Then adds them to the `SearchResults` store.
        """
        self.tracks = utils.Get.get_all_tracks()
        tracks = searchlib.SearchTracks(self.tracks, self.query)()

        if len(tracks) == 0:
            return []

        tracks = utils.RemoveDuplicates(tracks)()
        SearchResults.tracks = tracks

        return tracks

    def search_artists(self):
        """Calls :class:`SearchArtists` which returns the artists that fuzzily match
        the search term. Then adds them to the `SearchResults` store.
        """
        self.artists = utils.Get.get_all_artists()
        artists = searchlib.SearchArtists(self.artists, self.query)()
        SearchResults.artists = artists

        return artists

    def search_albums(self):
        """Calls :class:`SearchAlbums` which returns the albums that fuzzily match
        the search term. Then adds them to the `SearchResults` store.
        """
        albums = utils.Get.get_all_albums()
        albums = searchlib.SearchAlbums(albums, self.query)()
        SearchResults.albums = albums

        return albums

    def search_playlists(self):
        """Calls :class:`SearchPlaylists` which returns the playlists that fuzzily match
        the search term. Then adds them to the `SearchResults` store.
        """
        playlists = utils.Get.get_all_playlists()
        playlists = [serializer.Playlist(playlist) for playlist in playlists]

        playlists = searchlib.SearchPlaylists(playlists, self.query)()
        SearchResults.playlists = playlists

        return playlists

    def search_all(self):
        """Calls all the search methods."""
        self.search_tracks()
        self.search_albums()
        self.search_artists()
        self.search_playlists()


@search_bp.route("/search/tracks", methods=["GET"])
def search_tracks():
    """
    Searches for tracks that match the search query.
    """

    query = request.args.get("q")
    if not query:
        return {"error": "No query provided"}, 400

    tracks = DoSearch(query).search_tracks()

    return {
        "tracks": tracks[:SEARCH_COUNT],
        "more": len(tracks) > SEARCH_COUNT,
    }, 200


@search_bp.route("/search/albums", methods=["GET"])
def search_albums():
    """
    Searches for albums.
    """

    query = request.args.get("q")
    if not query:
        return {"error": "No query provided"}, 400

    tracks = DoSearch(query).search_albums()

    return {
        "albums": tracks[:SEARCH_COUNT],
        "more": len(tracks) > SEARCH_COUNT,
    }, 200


@search_bp.route("/search/artists", methods=["GET"])
def search_artists():
    """
    Searches for artists.
    """

    query = request.args.get("q")
    if not query:
        return {"error": "No query provided"}, 400

    artists = DoSearch(query).search_artists()

    return {
        "artists": artists[:SEARCH_COUNT],
        "more": len(artists) > SEARCH_COUNT,
    }, 200


@search_bp.route("/search/playlists", methods=["GET"])
def search_playlists():
    """
    Searches for playlists.
    """

    query = request.args.get("q")
    if not query:
        return {"error": "No query provided"}, 400

    playlists = DoSearch(query).search_playlists()

    return {
        "playlists": playlists[:SEARCH_COUNT],
        "more": len(playlists) > SEARCH_COUNT,
    }, 200


@search_bp.route("/search/top", methods=["GET"])
def get_top_results():
    """
    Returns the top results for the search query.
    """

    query = request.args.get("q")
    if not query:
        return {"error": "No query provided"}, 400

    DoSearch(query).search_all()

    max = 2
    return {
        "tracks": SearchResults.tracks[:max],
        "albums": SearchResults.albums[:max],
        "artists": SearchResults.artists[:max],
        "playlists": SearchResults.playlists[:max],
    }


@search_bp.route("/search/loadmore")
def search_load_more():
    """
    Returns more songs, albums or artists from a search query.
    """
    type = request.args.get("type")
    index = int(request.args.get("index"))

    if type == "tracks":
        t = SearchResults.tracks
        return {
            "tracks": t[index : index + SEARCH_COUNT],
            "more": len(t) > index + SEARCH_COUNT,
        }

    elif type == "albums":
        a = SearchResults.albums
        return {
            "albums": a[index : index + SEARCH_COUNT],
            "more": len(a) > index + SEARCH_COUNT,
        }

    elif type == "artists":
        a = SearchResults.artists
        return {
            "artists": a[index : index + SEARCH_COUNT],
            "more": len(a) > index + SEARCH_COUNT,
        }
