"""
Governance pack profile resolution.

Profiles control *inclusion only* of existing artefacts in a governance pack.
They do not generate new artefacts, change semantics, or introduce interpretation.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class PackItem:
    """
    Represents a file that may appear in a governance pack.

    - name: filename as it appears in the pack root
    - required: if True, absence is an error for the selected profile
    """

    name: str
    required: bool = False


class UnknownPackProfileError(ValueError):
    """Raised when an unknown pack profile is requested."""


def resolve_pack_profile(profile: str) -> List[PackItem]:
    """
    Resolve a pack profile name into a deterministic list of PackItem entries.

    Profiles are compositional only: they describe which files are included
    *if they exist*, and which files are required for the profile to be valid.

    Parameters
    ----------
    profile : str
        One of: "minimal", "qa", "audit"

    Returns
    -------
    List[PackItem]
        Ordered list of pack items to consider for inclusion.
    """

    profile = (profile or "audit").lower()

    profiles: Dict[str, List[PackItem]] = {
        "minimal": [
            PackItem("pack_manifest.json", required=True),
            PackItem("summary.txt", required=True),
            PackItem("README.txt", required=True),
        ],
        "qa": [
            # Required (same as minimal)
            PackItem("pack_manifest.json", required=True),
            PackItem("summary.txt", required=True),
            PackItem("README.txt", required=True),

            # Optional (included only if present)
            PackItem("manifest.json"),
            PackItem("explain.txt"),
            PackItem("explain.json"),
            PackItem("report.txt"),
            PackItem("report.json"),
            PackItem("validate.txt"),
            PackItem("validate.json"),
        ],
        "audit": [
            # Required
            PackItem("pack_manifest.json", required=True),
            PackItem("summary.txt", required=True),
            PackItem("README.txt", required=True),

            # Optional — full v1.17 behaviour preserved
            PackItem("manifest.json"),
            PackItem("explain.txt"),
            PackItem("explain.json"),
            PackItem("report.txt"),
            PackItem("report.json"),
            PackItem("validate.txt"),
            PackItem("validate.json"),
        ],
    }

    if profile not in profiles:
        raise UnknownPackProfileError(
            f"Unknown pack profile '{profile}'. "
            f"Valid profiles are: {', '.join(sorted(profiles.keys()))}."
        )

    return profiles[profile]
