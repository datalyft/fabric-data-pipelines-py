"""fabric_data_pipelines — Microsoft Fabric data pipelines as code.

Example::

    from fabric_data_pipelines import Pipeline, Wait, Notebook

    wait = Wait(name="pause", wait_time_in_seconds=5)
    nb = Notebook(name="run", notebook_id="...", workspace_id="...")
    wait.then(nb)

    pipeline = Pipeline(name="daily_load", activities=[wait, nb])
    print(pipeline.to_json())
"""

from fabric_data_pipelines import expressions as expr
from fabric_data_pipelines.activities import (
    Activity,
    ActivityDependency,
    ActivityPolicy,
    AppendVariable,
    AzureSqlMITable,
    AzureSqlTable,
    ColumnMapping,
    ColumnRef,
    Copy,
    CopySink,
    CopySource,
    Dataflow,
    Dataset,
    DatasetSettings,
    DataWarehouseSink,
    DataWarehouseSource,
    DataWarehouseTable,
    DependencyCondition,
    ExecutePipeline,
    ExternalReferences,
    Fail,
    ForEach,
    IfCondition,
    LakehouseTable,
    LakehouseTableSink,
    LakehouseTableSource,
    LinkedService,
    LinkedServiceProperties,
    Lookup,
    Notebook,
    PipelineReference,
    RawActivity,
    Script,
    ScriptBlock,
    SecureInputOutputPolicy,
    SetVariable,
    SqlMISink,
    SqlMISource,
    StagingSettings,
    StoredProcedure,
    Switch,
    SwitchCase,
    TabularTranslator,
    TypeConversionSettings,
    Until,
    Wait,
    Web,
)
from fabric_data_pipelines.errors import (
    CrossScopeDependencyError,
    CyclicDependencyError,
    DuplicateActivityNameError,
    PipelineValidationError,
    ScheduleValidationError,
    UnknownDependencyError,
)
from fabric_data_pipelines.export import save_workspace
from fabric_data_pipelines.pipeline import LibraryVariable, Parameter, Pipeline, Variable
from fabric_data_pipelines.schedule import (
    Cron,
    Daily,
    DayOfWeek,
    Monthly,
    MonthlyOccurrence,
    Schedule,
    ScheduleParameter,
    Weekday,
    Weekly,
    weekly_at,
)
from fabric_data_pipelines.serialization import Expression, FabricModel, dump_json

__all__ = [
    "Activity",
    "ActivityDependency",
    "ActivityPolicy",
    "AppendVariable",
    "AzureSqlMITable",
    "AzureSqlTable",
    "ColumnMapping",
    "ColumnRef",
    "Copy",
    "CopySink",
    "CopySource",
    "Cron",
    "CrossScopeDependencyError",
    "CyclicDependencyError",
    "Daily",
    "DataWarehouseSink",
    "DataWarehouseSource",
    "DataWarehouseTable",
    "Dataflow",
    "Dataset",
    "DatasetSettings",
    "DayOfWeek",
    "DependencyCondition",
    "DuplicateActivityNameError",
    "ExecutePipeline",
    "Expression",
    "ExternalReferences",
    "FabricModel",
    "Fail",
    "ForEach",
    "IfCondition",
    "LakehouseTable",
    "LakehouseTableSink",
    "LakehouseTableSource",
    "LibraryVariable",
    "LinkedService",
    "LinkedServiceProperties",
    "Lookup",
    "Monthly",
    "MonthlyOccurrence",
    "Notebook",
    "Parameter",
    "Pipeline",
    "PipelineReference",
    "PipelineValidationError",
    "RawActivity",
    "Schedule",
    "ScheduleParameter",
    "ScheduleValidationError",
    "Script",
    "ScriptBlock",
    "SecureInputOutputPolicy",
    "SetVariable",
    "SqlMISink",
    "SqlMISource",
    "StagingSettings",
    "StoredProcedure",
    "Switch",
    "SwitchCase",
    "TabularTranslator",
    "TypeConversionSettings",
    "UnknownDependencyError",
    "Until",
    "Variable",
    "Wait",
    "Web",
    "Weekday",
    "Weekly",
    "dump_json",
    "expr",
    "save_workspace",
    "weekly_at",
]

from importlib.metadata import PackageNotFoundError, version

try:
    __version__ = version("fabric-data-pipelines")
except PackageNotFoundError:  # pragma: no cover - editable/source tree without install
    __version__ = "0.0.0"
