"""DeviceDatabase: storing, updating and persisting discovered devices (no network access)."""

import json
import shutil
from pathlib import Path

from src.modules.discovery.device_database import DeviceDatabase

EXAMPLE = Path(__file__).resolve().parent.parent / "data" / "devices" / "example"


def make_db(tmp_path):
    return DeviceDatabase(str(tmp_path / "devices" / "device_database.json"))


def test_starts_empty_when_no_file(tmp_path):
    db = make_db(tmp_path)
    assert db.get_all_devices() == {}


def test_device_without_ip_is_rejected(tmp_path):
    db = make_db(tmp_path)
    assert db.add_or_update_device({"hostname": "no-ip"}) is False
    assert db.get_all_devices() == {}


def test_new_device_then_update_counts_discoveries(tmp_path):
    db = make_db(tmp_path)
    assert db.add_or_update_device({"ip": "192.0.2.10", "status": "active", "device_type": "printer"})
    assert db.add_or_update_device({"ip": "192.0.2.10", "status": "active", "open_ports": [631]})
    device = db.get_device("192.0.2.10")
    assert device["discovery_count"] == 2
    assert device["device_type"] == "printer"  # earlier fields are kept on update
    assert device["status_history"][-1]["open_ports"] == [631]


def test_status_history_keeps_last_ten(tmp_path):
    db = make_db(tmp_path)
    for port in range(15):
        db.add_or_update_device({"ip": "192.0.2.11", "status": "active", "open_ports": [port]})
    history = db.get_device("192.0.2.11")["status_history"]
    assert len(history) == 10
    assert history[0]["open_ports"] == [5]


def test_persists_across_instances(tmp_path):
    make_db(tmp_path).add_or_update_device({"ip": "192.0.2.12", "status": "active"})
    assert make_db(tmp_path).get_device("192.0.2.12")["status"] == "active"


def test_mark_offline_and_summary(tmp_path):
    db = make_db(tmp_path)
    db.add_or_update_device({"ip": "192.0.2.13", "status": "active", "device_type": "nas"})
    db.add_or_update_device({"ip": "192.0.2.14", "status": "active", "device_type": "nas"})
    assert db.mark_device_offline("192.0.2.14")
    assert db.mark_device_offline("192.0.2.99") is False
    summary = db.get_network_summary()
    assert summary["total_devices"] == 2
    assert summary["active_devices"] == 1
    assert summary["offline_devices"] == 1
    assert summary["device_types"] == {"nas": 2}


def test_example_data_loads(tmp_path):
    target = tmp_path / "devices"
    shutil.copytree(EXAMPLE, target)
    db = DeviceDatabase(str(target / "device_database.json"))
    assert len(db.get_all_devices()) == len(json.loads((EXAMPLE / "device_database.json").read_text()))
    assert db.network_fingerprints


def test_devices_with_missing_fields_do_not_crash_lookups(tmp_path):
    # Scanners store None for unknown hostnames and manufacturers.
    db = make_db(tmp_path)
    db.add_or_update_device({"ip": "192.0.2.20", "status": "active", "manufacturer": None, "hostname": None})
    db.add_or_update_device({"ip": "192.0.2.21", "status": "active", "manufacturer": "Synology"})
    assert [d["ip"] for d in db.get_devices_by_manufacturer("synology")] == ["192.0.2.21"]
