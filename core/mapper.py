"""Consistent PII value mapper — real → fake, deterministic and reversible.

The same real value always maps to the same fake value within a run.
Mappings can be persisted to / loaded from JSON for cross-run consistency
and for audit/debug purposes.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, Optional
from faker import Faker

from detectors.base import (
    NAME, EMAIL, PHONE, COMPANY, ADDRESS,
    SSN, CREDIT_CARD, DOB, IP_ADDRESS,
)


class PIIMapper:
    """Maintains a deterministic mapping from real PII values to fake replacements.

    Each unique (normalised) real value gets a Faker-generated replacement,
    seeded by the hash of the real value so the output is reproducible.

    Attributes:
        _map: ``{normalised_real: {fake, pii_type, count, original_forms}}``
    """

    def __init__(self, mapping_path: Optional[str] = None):
        self._map: Dict[str, dict] = {}
        self._mapping_path = mapping_path
        if mapping_path and Path(mapping_path).exists():
            self._load(mapping_path)

    # ── public API ────────────────────────────────────────────────────────

    def get_or_create(self, real_value: str, pii_type: str) -> str:
        """Return the fake replacement for *real_value*, creating one if needed."""
        key = self._normalise(real_value, pii_type)
        if key in self._map:
            self._map[key]["count"] += 1
            if real_value not in self._map[key]["original_forms"]:
                self._map[key]["original_forms"].append(real_value)
            return self._map[key]["fake"]

        fake_value = self._generate_fake(real_value, pii_type)
        self._map[key] = {
            "fake": fake_value,
            "pii_type": pii_type,
            "count": 1,
            "original_forms": [real_value],
        }
        return fake_value

    def save(self, path: Optional[str] = None) -> None:
        """Persist the full mapping to JSON for audit / debugging."""
        dest = path or self._mapping_path
        if dest is None:
            return
        with open(dest, "w", encoding="utf-8") as fh:
            json.dump(self._map, fh, indent=2, ensure_ascii=False)

    def save_audit_log(self, path: str) -> None:
        """Save a production-safe audit log (no original values, only fakes + types)."""
        audit = {}
        for key, entry in self._map.items():
            audit[key] = {
                "fake": entry["fake"],
                "pii_type": entry["pii_type"],
                "count": entry["count"],
            }
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(audit, fh, indent=2, ensure_ascii=False)

    def get_stats(self) -> Dict[str, int]:
        """Return count of unique mappings per PII type."""
        stats: Dict[str, int] = {}
        for entry in self._map.values():
            t = entry["pii_type"]
            stats[t] = stats.get(t, 0) + 1
        return stats

    def get_total_replacements(self) -> int:
        """Return total number of replacements applied (including repeats)."""
        return sum(e["count"] for e in self._map.values())

    # ── internals ─────────────────────────────────────────────────────────

    @staticmethod
    def _normalise(value: str, pii_type: str) -> str:
        """Case-insensitive normalisation for names and emails."""
        if pii_type in (NAME, EMAIL, COMPANY):
            return value.strip().lower()
        return value.strip()

    @staticmethod
    def _seed_from(value: str) -> int:
        """Deterministic seed derived from the value text."""
        h = hashlib.sha256(value.encode("utf-8")).hexdigest()
        return int(h[:8], 16)

    def _generate_fake(self, real_value: str, pii_type: str) -> str:
        """Create a type-appropriate fake value, seeded deterministically."""
        seed = self._seed_from(self._normalise(real_value, pii_type))
        fake = Faker()
        Faker.seed(seed)

        generators = {
            NAME:        lambda: fake.name(),
            EMAIL:       lambda: fake.ascii_free_email(),
            PHONE:       lambda: fake.phone_number(),
            COMPANY:     lambda: fake.company(),
            ADDRESS:     lambda: fake.address().replace("\n", ", "),
            SSN:         lambda: fake.ssn(),
            CREDIT_CARD: lambda: fake.credit_card_number(),
            DOB:         lambda: fake.date_of_birth(minimum_age=18, maximum_age=80).strftime("%m/%d/%Y"),
            IP_ADDRESS:  lambda: fake.ipv4(),
        }

        generator = generators.get(pii_type, lambda: fake.bothify("???-####"))
        return generator()

    def _load(self, path: str) -> None:
        """Load a previously saved mapping file."""
        with open(path, "r", encoding="utf-8") as fh:
            self._map = json.load(fh)
