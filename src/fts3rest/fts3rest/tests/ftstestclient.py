from flask.testing import FlaskClient
import functools
from flask import Response
import json


class TestResponse(Response):
    @property
    def json(self):
        return json.loads(self.data)


def _adapt_test(func):
    @functools.wraps
    def wrapper(*args, **kwargs):
        path = kwargs.pop("url", "/")
        expected_status = kwargs.pop("status", 200)
        data = kwargs.pop("params", None)
        res = func(*args, **kwargs, path=path, data=data)
        assert res.status_code == expected_status
        return res

    return wrapper


class FTSTestClient(FlaskClient):
    """
    This Flask Test Client adapts the request methods so they can be used
    with old functional tests created for Pylon's WebTest
    """

    get = _adapt_test(FlaskClient.get)
    post = _adapt_test(FlaskClient.post)
    put = _adapt_test(FlaskClient.put)
    delete = _adapt_test(FlaskClient.delete)

    def __init__(self, *args, **kwargs):
        kwargs["response_wrapper"] = TestResponse
        super().__init__(*args, **kwargs)

    def post_json(self, url, params, **kwargs):
        params = json.dumps(params)
        kwargs["content_type"] = "application/json"
        return self.post(url=url, params=params, **kwargs)

    def get_json(self, url, *args, **kwargs):
        kwargs["headers"] = [("Accept", "application/json")]
        return self.get(url=url, *args, **kwargs)
