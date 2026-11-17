from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from readiness_reservations.simulator import Config, POLICIES, generate_tasks, simulate


class SimulatorTests(unittest.TestCase):
    def test_trace_is_deterministic(self):
        cfg = Config(tasks=10)
        self.assertEqual(generate_tasks(cfg, 7), generate_tasks(cfg, 7))


    def test_all_policies_enforce_exact_version(self):
        cfg = Config(tasks=200, eviction_rate_per_s=20, competing_load=0.9)
        for policy in POLICIES:
            result = simulate(policy, cfg, 3)
            self.assertEqual(result.invalid_version_executions, 0)
            self.assertEqual(result.correct_version_executions, result.completed)


    def test_joint_reservation_prevents_valid_ttl_races(self):
        cfg = Config(tasks=300, dispatch_delay_ms=30, reservation_ttl_ms=50,
                     eviction_rate_per_s=20, replacement_rate_per_s=10,
                     competing_load=0.95)
        joint = simulate("joint_reservation", cfg, 9)
        on_demand = simulate("on_demand", cfg, 9)
        self.assertEqual(joint.readiness_refusals, 0)
        self.assertLess(joint.readiness_refusals, on_demand.readiness_refusals)


    def test_expired_reservation_does_not_claim_protection(self):
        cfg = Config(tasks=300, dispatch_delay_ms=40, reservation_ttl_ms=20,
                     eviction_rate_per_s=20, competing_load=0.95)
        joint = simulate("joint_reservation", cfg, 9)
        self.assertGreater(joint.readiness_refusals, 0)


if __name__ == "__main__":
    unittest.main()
