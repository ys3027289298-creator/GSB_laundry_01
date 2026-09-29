import unittest

import core


class TestCore(unittest.TestCase):
    def test_01_no_duplicate_cloth(self):
        state = core.new_game()
        core.create_order(state, 1)
        self.assertTrue(core.load_cloth(state, 1, "C1"))
        self.assertFalse(core.load_cloth(state, 1, "C1"))

    def test_02_no_assign_when_full(self):
        state = core.new_game()
        core.create_order(state, 1)
        core.create_order(state, 2)
        core.assign_machine(state, 1, "M1")
        core.assign_machine(state, 2, "M2")
        self.assertFalse(core.can_assign(state))

    def test_03_fee_exact(self):
        state = core.new_game()
        core.create_order(state, 1)
        self.assertEqual(core.fee(state, 1, 3), 2)

    def test_04_cancel_dry_returns_clothes(self):
        state = core.new_game()
        core.create_order(state, 1)
        core.load_cloth(state, 1, "C1")
        core.cancel_dry(state, 1)
        self.assertEqual(state["orders"][1]["clothes"], [])

    def test_05_discount_once(self):
        state = core.new_game()
        core.create_order(state, 1, member=True)
        self.assertEqual(core.discount(state, 1, 100), 90)

    def test_06_pickup_failure_keeps_order(self):
        state = core.new_game()
        core.create_order(state, 1)
        result = core.pickup(state, 1, False)
        self.assertFalse(result)
        self.assertIn(1, state["orders"])

    def test_07_expire_releases_machine(self):
        state = core.new_game()
        core.reserve(state, 1, "M1", 1)
        core.expire(state, 5)
        self.assertIsNone(state["machines"]["M1"])

    def test_08_load_preserves_order_id(self):
        state = core.new_game()
        state["order_id"] = 7
        loaded = core.load_state(core.save_state(state))
        self.assertEqual(loaded["order_id"], 7)


if __name__ == "__main__":
    unittest.main()
