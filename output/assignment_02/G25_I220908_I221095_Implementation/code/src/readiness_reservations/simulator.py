"""Deterministic discrete-event model for dispatch-to-start readiness races.

The model deliberately isolates the mechanism under study.  A scheduler observes
an edge worker, waits for a control-plane/transport delay, and then dispatches.
During that gap an exact artifact can be evicted or replaced and a compute slot
can be claimed by another tenant.  Reservations protect either or both resources.
All policies enforce exact-version execution; a mismatch is a refusal, never a
silent execution of stale code.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
import math
import random
from statistics import mean
from typing import Iterable


POLICIES = (
    "advertisement",
    "on_demand",
    "artifact_only",
    "slot_only",
    "joint_reservation",
)


@dataclass(frozen=True)
class Config:
    tasks: int = 1000
    arrival_rate_per_s: float = 18.0
    dispatch_delay_ms: float = 30.0
    eviction_rate_per_s: float = 8.0
    replacement_rate_per_s: float = 4.0
    competing_load: float = 0.65
    advertisement_interval_ms: float = 50.0
    reservation_ttl_ms: float = 50.0
    artifact_size_mb: float = 128.0
    edge_runtime_ms: float = 24.0
    cloud_runtime_ms: float = 42.0
    cloud_rtt_ms: float = 62.0
    retry_penalty_ms: float = 12.0
    cancellation_probability: float = 0.02


@dataclass(frozen=True)
class Task:
    arrival_ms: float
    deadline_ms: float
    version: int
    edge_rtt_ms: float
    u_evict: float
    u_replace: float
    u_compete: float
    u_cancel: float
    competitor_ms: float


@dataclass
class Worker:
    version: int = 0
    next_free_ms: float = 0.0
    advertised_version: int = 0
    advertised_free_ms: float = 0.0
    advertised_at_ms: float = 0.0


@dataclass
class Metrics:
    policy: str
    seed: int
    submitted: int = 0
    completed: int = 0
    deadlines_met: int = 0
    readiness_refusals: int = 0
    artifact_refusals: int = 0
    slot_refusals: int = 0
    cloud_fallbacks: int = 0
    correct_version_executions: int = 0
    invalid_version_executions: int = 0
    cancellations: int = 0
    control_messages: int = 0
    reserved_slot_ms: float = 0.0
    unused_reserved_slot_ms: float = 0.0
    pinned_mb_ms: float = 0.0
    latencies_ms: list[float] | None = None

    def __post_init__(self) -> None:
        self.latencies_ms = []

    def row(self, cfg: Config) -> dict[str, float | int | str]:
        values = asdict(self)
        latencies = sorted(self.latencies_ms or [])
        values.pop("latencies_ms")
        values.update(
            deadline_satisfaction=self.deadlines_met / self.submitted,
            refusal_rate=self.readiness_refusals / self.submitted,
            fallback_rate=self.cloud_fallbacks / self.submitted,
            mean_latency_ms=mean(latencies) if latencies else float("nan"),
            p95_latency_ms=_percentile(latencies, 0.95),
            pinned_mb_seconds=self.pinned_mb_ms / 1000.0,
            reserved_slot_seconds=self.reserved_slot_ms / 1000.0,
            unused_reserved_slot_seconds=self.unused_reserved_slot_ms / 1000.0,
            dispatch_delay_ms=cfg.dispatch_delay_ms,
            eviction_rate_per_s=cfg.eviction_rate_per_s,
            competing_load=cfg.competing_load,
            reservation_ttl_ms=cfg.reservation_ttl_ms,
        )
        return values


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return float("nan")
    return values[min(len(values) - 1, math.ceil(q * len(values)) - 1)]


def generate_tasks(cfg: Config, seed: int) -> list[Task]:
    rng = random.Random(seed)
    now = 0.0
    version = 0
    result: list[Task] = []
    for _ in range(cfg.tasks):
        now += rng.expovariate(cfg.arrival_rate_per_s) * 1000.0
        if rng.random() < 0.08:
            version += 1
        result.append(
            Task(
                arrival_ms=now,
                deadline_ms=now + rng.uniform(92.0, 142.0),
                version=version,
                edge_rtt_ms=rng.uniform(9.0, 21.0),
                u_evict=rng.random(),
                u_replace=rng.random(),
                u_compete=rng.random(),
                u_cancel=rng.random(),
                competitor_ms=rng.uniform(18.0, 55.0),
            )
        )
    return result


def simulate(policy: str, cfg: Config, seed: int) -> Metrics:
    if policy not in POLICIES:
        raise ValueError(f"unknown policy: {policy}")
    tasks = generate_tasks(cfg, seed)
    worker = Worker()
    m = Metrics(policy=policy, seed=seed)

    for task in tasks:
        m.submitted += 1
        # Periodic advertisements capture a potentially stale snapshot.
        if task.arrival_ms - worker.advertised_at_ms >= cfg.advertisement_interval_ms:
            worker.advertised_version = worker.version
            worker.advertised_free_ms = worker.next_free_ms
            worker.advertised_at_ms = task.arrival_ms
            m.control_messages += 1

        if policy == "advertisement":
            seen_version = worker.advertised_version
            seen_free = worker.advertised_free_ms
        else:
            seen_version = worker.version
            seen_free = worker.next_free_ms
            m.control_messages += 2  # readiness request and response

        ready = seen_version == task.version and seen_free <= task.arrival_ms
        projected_edge_finish = (
            task.arrival_ms
            + cfg.dispatch_delay_ms
            + task.edge_rtt_ms
            + cfg.edge_runtime_ms
        )
        choose_edge = ready and projected_edge_finish <= task.deadline_ms

        if not choose_edge:
            latency = cfg.cloud_rtt_ms + cfg.cloud_runtime_ms
            _complete(m, task, latency, cloud=True)
            # Background prefetch/update makes new versions available sometimes.
            if task.u_replace < 0.35:
                worker.version = task.version
            continue

        protect_artifact = policy in ("artifact_only", "joint_reservation")
        protect_slot = policy in ("slot_only", "joint_reservation")
        if protect_artifact or protect_slot:
            m.control_messages += 2  # reserve and grant

        dispatch_at = task.arrival_ms + cfg.dispatch_delay_ms
        reservation_valid = cfg.dispatch_delay_ms <= cfg.reservation_ttl_ms
        artifact_protected = protect_artifact and reservation_valid
        slot_protected = protect_slot and reservation_valid

        if protect_artifact:
            held = min(cfg.dispatch_delay_ms, cfg.reservation_ttl_ms)
            m.pinned_mb_ms += cfg.artifact_size_mb * held
        if protect_slot:
            held = min(cfg.dispatch_delay_ms, cfg.reservation_ttl_ms)
            m.reserved_slot_ms += held

        if task.u_cancel < cfg.cancellation_probability:
            m.cancellations += 1
            if protect_slot:
                m.unused_reserved_slot_ms += min(
                    cfg.dispatch_delay_ms, cfg.reservation_ttl_ms
                )
            continue

        gap_s = cfg.dispatch_delay_ms / 1000.0
        eviction_p = 1.0 - math.exp(-cfg.eviction_rate_per_s * gap_s)
        replacement_p = 1.0 - math.exp(-cfg.replacement_rate_per_s * gap_s)
        competition_p = min(0.98, cfg.competing_load * gap_s * 20.0)

        if not artifact_protected:
            if task.u_evict < eviction_p:
                worker.version = -1
            elif task.u_replace < replacement_p:
                worker.version = task.version + 1
        if not slot_protected and task.u_compete < competition_p:
            worker.next_free_ms = max(worker.next_free_ms, dispatch_at + task.competitor_ms)

        artifact_ok = worker.version == task.version
        slot_ok = worker.next_free_ms <= dispatch_at
        if not artifact_ok or not slot_ok:
            m.readiness_refusals += 1
            if not artifact_ok:
                m.artifact_refusals += 1
            if not slot_ok:
                m.slot_refusals += 1
            m.cloud_fallbacks += 1
            latency = (
                cfg.dispatch_delay_ms
                + cfg.retry_penalty_ms
                + cfg.cloud_rtt_ms
                + cfg.cloud_runtime_ms
            )
            _complete(m, task, latency, cloud=False)
            worker.version = task.version  # async repair/prefetch after failure
            continue

        start = max(dispatch_at, worker.next_free_ms)
        finish = start + task.edge_rtt_ms + cfg.edge_runtime_ms
        worker.next_free_ms = finish
        _complete(m, task, finish - task.arrival_ms, cloud=False)

    return m


def _complete(m: Metrics, task: Task, latency_ms: float, cloud: bool) -> None:
    m.completed += 1
    m.correct_version_executions += 1
    m.latencies_ms.append(latency_ms)
    if cloud:
        m.cloud_fallbacks += 1
    if task.arrival_ms + latency_ms <= task.deadline_ms:
        m.deadlines_met += 1


def run_many(configs: Iterable[Config], seeds: Iterable[int]) -> list[dict]:
    rows: list[dict] = []
    for cfg in configs:
        for seed in seeds:
            for policy in POLICIES:
                rows.append(simulate(policy, cfg, seed).row(cfg))
    return rows
