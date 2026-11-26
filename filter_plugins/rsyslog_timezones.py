"""Compile IANA civil-time transitions into a native rsyslog string lookup table."""

import json
import subprocess
import zoneinfo
from collections import defaultdict
from collections.abc import Callable, Iterable, Iterator
from datetime import datetime, timedelta
from pathlib import Path


def _offset(value: str) -> int:
    """Decode zdump's signed HH[MM[SS]] offset."""
    digits = value[1:].ljust(6, "0")
    seconds = int(digits[:2]) * 3600 + int(digits[2:4]) * 60 + int(digits[4:])
    return -seconds if value.startswith("-") else seconds


def _transitions(
    zone: zoneinfo.ZoneInfo,
) -> tuple[int, dict[int, list[tuple[datetime, int | str]]]]:
    """Mark gaps as invalid and retain the earlier instant of a repeated hour."""
    paths = (Path(base, str(zone)) for base in zoneinfo.TZPATH)
    zonefile = next((path for path in paths if path.is_file()), None)
    if zonefile is None:
        raise ValueError(f"No system zoneinfo file for {zone} on the Ansible controller")
    # Future Gregorian rules repeat every 400 years. Include the whole 2400 cycle.
    output = subprocess.run(
        ["zdump", "-i", "-c", "1,2801", str(zonefile)],
        env={"LC_ALL": "C"}, capture_output=True, text=True, check=True,
    )
    lines = (line.split("\t") for line in output.stdout.splitlines() if "\t" in line)
    header = next(lines, [])
    if header[:2] != ["-", "-"]:
        raise ValueError(f"zdump did not return an initial offset for {zone}")
    initial = previous = _offset(header[2])
    years: dict[int, list[tuple[datetime, int | str]]] = defaultdict(list)
    for fields in lines:
        current = _offset(fields[2])
        if current != previous:
            after = datetime.fromisoformat("T".join(fields[:2]))
            before = after + timedelta(seconds=previous - current)
            if before < after:
                years[before.year].append((before, "gap"))
            boundary = max(before, after)
            years[boundary.year].append((boundary, current))
        previous = current
    return initial, years


def _zone_rows(zone: str) -> Iterator[dict[str, str]]:
    # zdump interprets unknown names as POSIX rules. Require a real IANA key first.
    initial, years = _transitions(zoneinfo.ZoneInfo(zone))
    # A missing year uses the initial offset (including zones without transitions).
    yield {"index": zone, "value": json.dumps([{"at": 0, "offset": initial}])}
    active: int | str = initial
    for year in range(min(years, default=2800), 2800):
        spans = [{"at": 0, "offset": active}]
        for when, active in years[year]:
            spans.append({"at": int(when.strftime("%m%d%H%M%S")), "offset": active})
        if len(spans) > 1 or active != initial:
            yield {"index": f"{zone}/{year}", "value": json.dumps(spans, separators=(",", ":"))}


class FilterModule:
    """Expose the timezone compiler to Ansible templates."""

    @staticmethod
    def timezone_table(zones: Iterable[str]) -> dict[str, object]:
        """Build a deterministic table from the controller's zoneinfo files."""
        rows = [row for zone in sorted(zones) for row in _zone_rows(zone)]
        return {"version": 1, "table": rows}

    @classmethod
    def filters(cls) -> dict[str, Callable[[Iterable[str]], dict[str, object]]]:
        """Register the role's Jinja filter."""
        return {"rsyslog_timezone_table": cls.timezone_table}
