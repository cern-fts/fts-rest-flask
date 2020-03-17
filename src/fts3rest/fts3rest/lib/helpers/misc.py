import json
from urllib.parse import unquote_plus
from werkzeug.exceptions import BadRequest


def get_input_as_dict(request, from_query=False):
    """
    Return a valid dictionary from the request input
    """
    if from_query:
        input_dict = request.values
    elif request.content_type == "application/json, application/x-www-form-urlencoded":
        input_dict = json.loads(unquote_plus(request.body))
    elif request.content_type.startswith("application/json") or request.method == "PUT":
        try:
            input_dict = json.loads(request.body)
        except Exception:
            raise BadRequest("Badly formatted JSON request")
    elif request.content_type.startswith("application/x-www-form-urlencoded"):
        input_dict = dict(request.values)
    else:
        raise BadRequest(
            "Expecting application/json or application/x-www-form-urlencoded"
        )

    if not hasattr(input_dict, "__getitem__") or not hasattr(input_dict, "get"):
        raise BadRequest("Expecting a dictionary")
    return input_dict
