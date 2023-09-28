from functools import wraps

import flask_jwt_extended
from flask import make_response, jsonify


def jwt_required(optional=False, fresh=False, refresh=False, locations=None):
    """
    A decorator to protect a Flask endpoint with JSON Web Tokens.

    Any route decorated with this will require a valid JWT to be present in the
    request (unless optional=True, in which case no JWT is also valid) before the
    endpoint can be called.

    :param optional:
        If ``True``, allow the decorated endpoint to be if no JWT is present in the
        request. Defaults to ``False``.

    :param fresh:
        If ``True``, require a JWT marked with ``fresh`` to be able to access this
        endpoint. Defaults to ``False``.

    :param refresh:
        If ``True``, requires a refresh JWT to access this endpoint. If ``False``,
        requires an access JWT to access this endpoint. Defaults to ``False``.

    :param locations:
        A location or list of locations to look for the JWT in this request, for
        example ``'headers'`` or ``['headers', 'cookies']``. Defaluts to ``None``
        which indicates that JWTs will be looked for in the locations defined by the
        ``JWT_TOKEN_LOCATION`` configuration option.
    """

    def wrapper(fn):
        @wraps(fn)
        def decorator(*args, **kwargs):
            try:
                flask_jwt_extended.verify_jwt_in_request(optional, fresh, refresh, locations)
            except Exception as e:
                print(f"Error: {e}")
                return make_response(jsonify(msg=f"Invalid or expired JWT token", status=401), 401)

            return fn(*args, **kwargs)

        return decorator

    return wrapper