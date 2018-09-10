# encode: utf-8

import googlemaps
from django.conf import settings


class Maps(object):
    """
    This class holds maps functions.    
    """

    def __init__(self):
        """
        Initializes map client.
        """
        self.client = googlemaps.Client(key=settings.GOOGLE_MAPS_KEY)
