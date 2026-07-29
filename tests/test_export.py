from pathlib import Path

import pytest

from fabric_data_pipelines import Pipeline, Wait, save_workspace


def test_save_workspace_prunes_unlisted_items(tmp_path: Path) -> None:
    p1 = Pipeline(name="keep", activities=[Wait(name="w", wait_time_in_seconds=1)])
    p2 = Pipeline(name="drop", activities=[Wait(name="w2", wait_time_in_seconds=1)])

    p1.save_item(tmp_path)
    p2.save_item(tmp_path)

    produced = save_workspace([p1], tmp_path, prune=True)
    assert len(produced) == 1
    assert (tmp_path / "keep.DataPipeline").exists()
    assert not (tmp_path / "drop.DataPipeline").exists()


def test_save_workspace_rejects_duplicate_names(tmp_path: Path) -> None:
    p1 = Pipeline(name="dup", activities=[Wait(name="w", wait_time_in_seconds=1)])
    p2 = Pipeline(name="dup", activities=[Wait(name="w2", wait_time_in_seconds=1)])

    with pytest.raises(ValueError):
        save_workspace([p1, p2], tmp_path, prune=False)
