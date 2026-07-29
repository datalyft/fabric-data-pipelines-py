"""Web GET — call a REST path via a Fabric connection.

Scenario: hit a relative URL on a configured HTTP connection and keep the
default activity policy Fabric writes for Web activities.
"""

from fabric_data_pipelines import ExternalReferences, Pipeline, Web

web = Web(
    name="Call_Orders_API",
    method="GET",
    relative_url="/orders?status=open",
    headers={"Accept": "application/json"},
    http_request_timeout="00:01:40",
    external_references=ExternalReferences(connection="00000000-0000-0000-0000-000000000005"),
)

pipeline = Pipeline(
    name="Web_Orders_Lookup",
    description="GET /orders from a Fabric Web connection.",
    activities=[web],
)

if __name__ == "__main__":
    print(pipeline.to_json())
