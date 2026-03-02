from __future__ import annotations

from uuid import UUID

from fastapi.testclient import TestClient

from osiris.main import app


def _parse_metric_value(
    metrics_text: str,
    *,
    name: str,
    labels: dict[str, str],
) -> float:
    expected = tuple(sorted(labels.items()))
    for raw_line in metrics_text.splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or not line.startswith(name):
            continue

        metric_and_value = line.split(" ", 1)
        if len(metric_and_value) != 2:
            continue

        metric_part, value_part = metric_and_value
        if "{" not in metric_part or not metric_part.endswith("}"):
            continue

        _, raw_labels = metric_part.split("{", 1)
        raw_labels = raw_labels[:-1]  # strip trailing "}"
        parsed_labels: list[tuple[str, str]] = []
        for pair in raw_labels.split(","):
            if "=" not in pair:
                continue
            key, value = pair.split("=", 1)
            parsed_labels.append((key, value.strip('"')))

        if tuple(sorted(parsed_labels)) != expected:
            continue
        return float(value_part)
    return 0.0


def test_metrics_endpoint_exposes_http_metrics_and_counter_increments():
    with TestClient(app) as client:
        baseline_metrics = client.get("/metrics")
        assert baseline_metrics.status_code == 200
        assert "osiris_http_in_flight_requests" in baseline_metrics.text
        assert "osiris_fe_worker_runs_total" in baseline_metrics.text

        before = _parse_metric_value(
            baseline_metrics.text,
            name="osiris_http_requests_total",
            labels={"method": "GET", "path": "/openapi.json", "status_code": "200"},
        )

        openapi = client.get("/openapi.json")
        assert openapi.status_code == 200

        after_metrics = client.get("/metrics")
        assert after_metrics.status_code == 200
        assert "osiris_http_requests_total" in after_metrics.text
        after = _parse_metric_value(
            after_metrics.text,
            name="osiris_http_requests_total",
            labels={"method": "GET", "path": "/openapi.json", "status_code": "200"},
        )
        assert after >= before + 1


def test_request_id_header_is_propagated_when_provided():
    custom_request_id = "req-observability-001"
    with TestClient(app) as client:
        response = client.get("/openapi.json", headers={"X-Request-ID": custom_request_id})
    assert response.status_code == 200
    assert response.headers.get("X-Request-ID") == custom_request_id


def test_request_id_header_is_generated_when_missing():
    with TestClient(app) as client:
        response = client.get("/openapi.json")
    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id is not None
    UUID(request_id)
