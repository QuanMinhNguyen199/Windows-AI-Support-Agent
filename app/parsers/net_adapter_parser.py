import json

from app.models.diagnostics import NetworkAdapter


def parse_net_adapters(output: str) -> list[NetworkAdapter]:
    if not output.strip():
        return []
    try:
        payload = json.loads(output)
    except (json.JSONDecodeError, TypeError):
        return []
    records = payload if isinstance(payload, list) else [payload]
    adapters: list[NetworkAdapter] = []
    for record in records:
        if not isinstance(record, dict) or not record.get("Name"):
            continue
        adapters.append(
            NetworkAdapter(
                name=str(record["Name"]),
                description=(
                    str(record["InterfaceDescription"])
                    if record.get("InterfaceDescription") is not None
                    else None
                ),
                status=str(record["Status"]) if record.get("Status") is not None else None,
                link_speed=(
                    str(record["LinkSpeed"]) if record.get("LinkSpeed") is not None else None
                ),
            )
        )
    return adapters
