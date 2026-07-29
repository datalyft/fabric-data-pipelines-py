"""Daily notebook transform — the smallest useful Fabric pipeline.

Scenario: pause briefly, then run a Fabric notebook that transforms
yesterday's landing data into silver tables.
"""

from fabric_data_pipelines import Notebook, Pipeline, Wait

wait = Wait(name="Wait_For_Upstream", wait_time_in_seconds=30)
transform = Notebook(
    name="Transform_Silver_Sales",
    notebook_id="00000000-0000-0000-0000-000000000002",
    workspace_id="00000000-0000-0000-0000-000000000001",
)
wait.then(transform)

pipeline = Pipeline(
    name="Daily_Silver_Sales_Transform",
    description="Wait for upstream settlement, then run the silver sales notebook.",
    activities=[wait, transform],
)

if __name__ == "__main__":
    print(pipeline.to_json())
