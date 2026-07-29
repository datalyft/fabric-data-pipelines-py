"""Unit tests for Web activity serialization."""

from fabric_data_pipelines import ExternalReferences, Pipeline, Web


def test_web_activity_shape() -> None:
    web = Web(
        name="Call_Orders_API",
        method="GET",
        relative_url="/orders?status=open",
        headers={"Accept": "application/json"},
        http_request_timeout="00:01:40",
        external_references=ExternalReferences(connection="00000000-0000-0000-0000-000000000005"),
    )
    data = web.to_dict()
    assert data["type"] == "WebActivity"
    assert data["typeProperties"]["method"] == "GET"
    assert data["typeProperties"]["relativeUrl"] == "/orders?status=open"
    assert data["typeProperties"]["headers"] == {"Accept": "application/json"}
    assert data["typeProperties"]["httpRequestTimeout"] == "00:01:40"
    assert data["externalReferences"]["connection"] == "00000000-0000-0000-0000-000000000005"
    assert data["policy"]["timeout"] == "0.12:00:00"

    pipeline = Pipeline(name="web_demo", activities=[web])
    assert pipeline.to_dict()["properties"]["activities"][0]["name"] == "Call_Orders_API"


def test_web_post_with_body() -> None:
    web = Web(
        name="Notify",
        method="POST",
        relative_url="/hooks/notify",
        body={"event": "load_complete"},
        external_references=ExternalReferences(connection="00000000-0000-0000-0000-000000000005"),
    )
    data = web.to_dict()
    assert data["typeProperties"]["method"] == "POST"
    assert data["typeProperties"]["body"] == {"event": "load_complete"}
    assert "disableCertValidation" not in data["typeProperties"]
