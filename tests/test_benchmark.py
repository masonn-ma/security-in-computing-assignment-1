from datetime import datetime

from crypto_bench.runners.benchmark import _create_run_directory


def test_run_directory_uses_date_and_next_version(tmp_path):
    (tmp_path / "17-11-2026_v1").mkdir()
    (tmp_path / "17-11-2026_v3").mkdir()
    (tmp_path / "16-11-2026_v9").mkdir()

    run_id, root = _create_run_directory(
        tmp_path, datetime(2026, 11, 17, 12, 0)
    )

    assert run_id == "17-11-2026_v4"
    assert root == tmp_path / "17-11-2026_v4"
    assert root.is_dir()
