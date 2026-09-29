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
    # 读档不得改动订单计数器，避免重新分配出已存在的订单编号
    if not isinstance(state, dict):
        raise ValueError("存档格式错误")
    state.setdefault("orders", {})
    state.setdefault("machines", {"M1": None, "M2": None})
    state.setdefault("reservations", {})
    state.setdefault("day", 1)
    state.setdefault("order_id", 0)
    return state


def create_order(state, order_id, member=False):
    if order_id in state.get("orders", {}):
        return False
    state["orders"][order_id] = {"clothes": [], "member": member, "machine": None}
    return True


def load_cloth(state, order_id, cloth_id):
    order = state.get("orders", {}).get(order_id)
    if order is None or not cloth_id:
        return False
    if cloth_id in order["clothes"]:
        return False
    order["clothes"].append(cloth_id)
    return True


def assign_machine(state, order_id, machine_id):
    if not can_assign(state):
        return False
    if order_id not in state.get("orders", {}):
        return False
    if machine_id not in state.get("machines", {}):
        return False
    if state["machines"][machine_id] is not None:
        return False
    if state["orders"][order_id].get("machine") is not None:
        return False
    state["machines"][machine_id] = order_id
    state["orders"][order_id]["machine"] = machine_id
    return True


def can_assign(state):
    return any(machine is None for machine in state.get("machines", {}).values())


def fee(state, order_id, pickup_day):
    if order_id not in state.get("orders", {}):
        return None
    if not isinstance(pickup_day, int) or pickup_day < state["day"]:
        return None
    # 送洗当天也算一天，跨日天数直接相减
    return pickup_day - state["day"]


def cancel_dry(state, order_id):
    order = state.get("orders", {}).get(order_id)
    if order is None:
        return False
    order["clothes"] = []
    order["dry"] = False
    return True


def discount(state, order_id, base):
    order = state.get("orders", {}).get(order_id)
    if order is None or base < 0:
        return None
    if order.get("member"):
        return max(0, base - 10)
    return base


def pickup(state, order_id, paid):
    order = state.get("orders", {}).get(order_id)
    if order is None or order.get("settled"):
        return False
    if not paid:
        # 未付款取件失败，订单必须保留
        return False
    order["settled"] = True
    machine_id = order.get("machine")
    if machine_id is not None and state.get("machines", {}).get(machine_id) == order_id:
        state["machines"][machine_id] = None
        order["machine"] = None
    state["reservations"].pop(order_id, None)
    return True


def reserve(state, order_id, machine_id, days):
    if order_id not in state.get("orders", {}):
        return False
    if machine_id not in state.get("machines", {}) or days is None or days <= 0:
        return False
    if state["machines"][machine_id] is not None:
        return False
    state["machines"][machine_id] = order_id
    state["reservations"][order_id] = {"machine": machine_id, "expires": state["day"] + days}
    return True


def expire(state, current_day):
    if not isinstance(current_day, int) or current_day < state.get("day", 1):
        return False
    state["day"] = current_day
    expired = [
        order_id
        for order_id, info in state.get("reservations", {}).items()
        if current_day >= info["expires"]
    ]
    for order_id in expired:
        info = state["reservations"].pop(order_id)
        machine_id = info["machine"]
        if state.get("machines", {}).get(machine_id) == order_id:
            order = state["orders"].get(order_id)
            if order is not None and order.get("machine") == machine_id:
                order["machine"] = None
            state["machines"][machine_id] = None
    return True


def main():
    print("洗衣店 - 命令: order/load/assign/fee/cancel/discount/pickup/reserve/expire/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not raw or raw == "quit":
            break
        parts = raw.split()
        command = parts[0]
        args = parts[1:]

        def int_arg(index):
            try:
                return int(args[index]), None
            except (IndexError, ValueError):
                return None, "参数错误"

        if command == "order":
            member = len(args) >= 1 and args[0] in ("member", "会员", "1", "true", "yes")
            state["order_id"] += 1
            if create_order(state, state["order_id"], member):
                print("ok order", state["order_id"])
            else:
                state["order_id"] -= 1
                print("error 订单编号冲突")
        elif command == "load":
            order_id, err = int_arg(0)
            cloth_id = args[1] if len(args) > 1 else ""
            print("ok" if err is None and load_cloth(state, order_id, cloth_id) else "error")
        elif command == "assign":
            order_id, err = int_arg(0)
            machine_id = args[1] if len(args) > 1 else ""
            print("ok" if err is None and assign_machine(state, order_id, machine_id) else "error 机位不可用")
        elif command == "fee":
            order_id, err = int_arg(0)
            pickup_day, err2 = int_arg(1)
            amount = fee(state, order_id, pickup_day) if err is None and err2 is None else None
            print(amount if amount is not None else "error")
        elif command == "cancel":
            order_id, err = int_arg(0)
            print("ok" if err is None and cancel_dry(state, order_id) else "error")
        elif command == "discount":
            order_id, err = int_arg(0)
            base, err2 = int_arg(1)
            amount = discount(state, order_id, base) if err is None and err2 is None else None
            print(amount if amount is not None else "error")
        elif command == "pickup":
            order_id, err = int_arg(0)
            paid = len(args) > 1 and args[1] in ("1", "true", "yes", "paid", "已付")
            print("ok" if err is None and pickup(state, order_id, paid) else "error 取件失败")
        elif command == "reserve":
            order_id, err = int_arg(0)
            machine_id = args[1] if len(args) > 1 else ""
            days, err2 = int_arg(2)
            ok = err is None and err2 is None and reserve(state, order_id, machine_id, days)
            print("ok" if ok else "error 预约失败")
        elif command == "expire":
            current_day, err = int_arg(0)
            print("ok" if err is None and expire(state, current_day) else "error")
        else:
            print("error 非法命令")


if __name__ == "__main__":
    main()
