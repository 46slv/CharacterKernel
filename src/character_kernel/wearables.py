from __future__ import annotations

from dataclasses import dataclass, replace
from typing import Iterable, Sequence

from .attachments import AttachmentError, SurfaceAttachment, SurfaceIdentity


@dataclass(frozen=True)
class WearableVariant:
    """Editable source identity for one interchangeable wearable variant."""

    variant_id: str
    source_id: str
    source_hash: str

    def __post_init__(self) -> None:
        if not self.variant_id or not self.source_id or not self.source_hash:
            raise ValueError("wearable variant identity fields must be non-empty")


@dataclass(frozen=True)
class WearableSelection:
    """Small immutable selection state; fitted geometry remains derived."""

    variants: tuple[WearableVariant, ...]
    active_variant: str
    fit_revision: int = 0

    def __post_init__(self) -> None:
        if not self.variants:
            raise ValueError("at least one wearable variant is required")
        ids = tuple(variant.variant_id for variant in self.variants)
        if len(set(ids)) != len(ids):
            raise ValueError("wearable variant ids must be unique")
        if self.active_variant not in ids:
            raise ValueError(f"unknown active wearable variant: {self.active_variant!r}")
        if self.fit_revision < 0:
            raise ValueError("fit_revision cannot be negative")

    def select(self, variant_id: str) -> "WearableSelection":
        if variant_id not in {variant.variant_id for variant in self.variants}:
            raise ValueError(f"unknown wearable variant: {variant_id!r}")
        return replace(self, active_variant=variant_id, fit_revision=self.fit_revision + 1)


@dataclass(frozen=True)
class AttachmentBatchReport:
    status: str
    total: int
    valid: int
    invalid_ids: tuple[str, ...] = ()

    @property
    def all_valid(self) -> bool:
        return self.total > 0 and self.valid == self.total and self.status == "VALID"


def validate_attachment_batch(
    attachments: Iterable[SurfaceAttachment],
    *,
    identity: SurfaceIdentity,
    vertices: Sequence[Sequence[float]],
    triangles: Sequence[Sequence[int]] | None = None,
    vertex_normals: Sequence[Sequence[float]] | None = None,
) -> AttachmentBatchReport:
    """Evaluate every persisted correspondence and fail closed as one batch."""

    records = tuple(attachments)
    invalid: list[str] = []
    valid = 0
    for attachment in records:
        try:
            attachment.evaluate(
                identity=identity,
                vertices=vertices,
                triangles=triangles,
                vertex_normals=vertex_normals,
            )
        except AttachmentError:
            invalid.append(attachment.attachment_id)
        else:
            valid += 1
    return AttachmentBatchReport(
        status="VALID" if not invalid and records else "REBIND_REQUIRED",
        total=len(records),
        valid=valid,
        invalid_ids=tuple(invalid),
    )
