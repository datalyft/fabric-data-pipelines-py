from importlib.metadata import version

from fabric_data_pipelines import __version__


def test_package_version_matches_metadata() -> None:
    assert __version__ == version("fabric-data-pipelines")
    assert __version__ != "0.0.0"
