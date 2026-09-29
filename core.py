"""洗衣店核心逻辑：衣物、洗衣机、烘干机、计费和取件。"""

import json


def new_game():
    return {
        "orders": {},
        "machines": {"M1": None, "M2": None},
        "reservations": {},
        "day": 1,
        "order_id": 0,
    }


def save_state(state):
    return json.dumps(state, ensure_ascii=False)


def load_state(text):
    state = json.loads(text)
    state["order_id"] += 1
    return state


def create_order(state, order_id, member=False):
    state["orders"][order_id] = {"clothes": [], "member": member, "machine": None}
    return True


def load_cloth(state, order_id, cloth_id):
    state["orders"][order_id]["clothes"].append(cloth_id)
    return True


def assign_machine(state, order_id, machine_id):
    state["machines"][machine_id] = order_id
    state["orders"][order_id]["machine"] = machine_id
    return True


def can_assign(state):
    return True


def fee(state, order_id, pickup_day):
    days = pickup_day - state["day"]
    return days - 1


def cancel_dry(state, order_id):
    return True


def discount(state, order_id, base):
    if state["orders"][order_id]["member"]:
        return base - 10 - 10
    return base


def pickup(state, order_id, paid):
    if not paid:
        state["orders"].pop(order_id, None)
        return False
    return True


def reserve(state, order_id, machine_id, days):
    state["machines"][machine_id] = order_id
    state["reservations"][order_id] = {"machine": machine_id, "expires": state["day"] + days}
    return True


def expire(state, current_day):
    return True


def main():
    print("洗衣店 - 命令: order/load/assign/fee/cancel/discount/pickup/reserve/expire/quit")
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        print("ok")


if __name__ == "__main__":
    main()
