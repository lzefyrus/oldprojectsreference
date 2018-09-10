# encode: utf-8

import json

from rest_framework import serializers

from domain import utils
from domain.exceptions import InvalidRequestError


class Base64Validator(object):
    """
    Validates if a picture is base64.
    """

    def __call__(self, value):
        if not utils.is_base64(value):
            raise serializers.ValidationError("This is not a valid base64")
        return value


class IntValidator(object):
    """
    Validates if a value is int parseble.
    """

    def __call__(self, value):
        try:
            return int(value)
        except ValueError:
            raise serializers.ValidationError("this field must be integer")


def validate_geolocation_query_string(func_to_decorate):
    """
    Decorator that validates geolocation parameters from the query string.
    :param func_to_decorate:
    :return:
    """
    def new_func(*original_args, **original_kwargs):
        """
        Decorated function.
        :param original_args:
        :param original_kwargs:
        :return:
        """
        self = original_args[0]
        query_string = self.request.query_params
        errors = []

        if not query_string:
            return func_to_decorate(*original_args, **original_kwargs)

        # address validation
        if 'address' in query_string:
            if not query_string['address']:
                errors.append('invalid address it cannot be empty')
            else:
                self.address = query_string['address']
        # lat/lng validation
        else:
            try:
                self.lng = float(query_string['lng'])
            except KeyError:
                errors.append("lng parameter is required")
            except ValueError:
                errors.append('invalid lng it must be a float')

            try:
                self.lat = float(query_string['lat'])
            except KeyError:
                errors.append("lat parameter is required")
            except ValueError:
                errors.append('invalid lat it must be a float')

        try:
            self.radius = int(query_string['radius'])
        except KeyError:
            errors.append("radius parameter is required")
        except ValueError:
            errors.append('invalid radius it must be an integer')

        self.brand = query_string.get('brand')
        if self.brand:
            try:
                self.brand = int(self.brand)
            except ValueError:
                try:
                    self.brand = json.loads(self.brand)
                except:
                    errors.append('invalid brand it must be an integer or list')

        if errors:
            raise InvalidRequestError(errors)

        return func_to_decorate(*original_args, **original_kwargs)
    return new_func
