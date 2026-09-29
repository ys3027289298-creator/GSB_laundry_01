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
    if not isinstance(text, str) or not text.strip():
        raise ValueError("存档为空")
    state = json.loads(text)
    for key in ("orders", "machines", "reservations"):
        if not isinstance(state.get(key), dict):
            raise ValueError("存档缺少字段: %s" % key)
    for key in ("day", "order_id"):
        value = state.get(key)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("存档字段非法: %s" % key)
    return state


def create_order(state, order_id, member=False):
    if not isinstance(order_id, int) or isinstance(order_id, bool) or order_id <= 0:
        return False
    if order_id in state["orders"]:
        return False
    state["orders"][order_id] = {"clothes": [], "member": member, "machine": None}
    if order_id > state.get("order_id", 0):
        state["order_id"] = order_id
    return True


def next_order_id(state):
    state["order_id"] = state.get("order_id", 0) + 1
    return state["order_id"]


def load_cloth(state, order_id, cloth_id):
    order = state.get("orders", {}).get(order_id)
    if order is None or not isinstance(cloth_id, str) or not cloth_id:
        return False
    if cloth_id in order["clothes"]:
        return False
    order["clothes"].append(cloth_id)
    return True


def assign_machine(state, order_id, machine_id):
    order = state.get("orders", {}).get(order_id)
    machines = state.get("machines", {})
    if order is None or machine_id not in machines:
        return False
    if machines[machine_id] is not None or order.get("machine") is not None:
        return False
    machines[machine_id] = order_id
    order["machine"] = machine_id
    return True


def can_assign(state):
    return any(owner is None for owner in state.get("machines", {}).values())


def fee(state, order_id, pickup_day):
    if order_id not in state.get("orders", {}):
        return None
    days = pickup_day - state["day"]
    return days if days > 0 else 0


def cancel_dry(state, order_id):
    order = state.get("orders", {}).get(order_id)
    if order is None:
        return []
    returned = list(order.get("clothes", []))
    order["clothes"] = []
    return returned


MEMBER_DISCOUNT = 10


def discount(state, order_id, base):
    order = state.get("orders", {}).get(order_id)
    if order is None:
        return None
    if order.get("member"):
        return max(0, base - MEMBER_DISCOUNT)
    return base


def pickup(state, order_id, paid):
    order = state.get("orders", {}).get(order_id)
    if order is None or order.get("settled"):
        return False
    if not paid:
        return False
    machine_id = order.get("machine")
    if machine_id is not None:
        if state.get("machines", {}).get(machine_id) == order_id:
            state["machines"][machine_id] = None
        order["machine"] = None
    state.get("reservations", {}).pop(order_id, None)
    order["settled"] = True
    state["orders"].pop(order_id, None)
    return True


def reserve(state, order_id, machine_id, days):
    machines = state.get("machines", {})
    if machine_id not in machines:
        return False
    if machines[machine_id] is not None:
        return False
    if not isinstance(days, int) or isinstance(days, bool) or days < 0:
        return False
    machines[machine_id] = order_id
    state["reservations"][order_id] = {"machine": machine_id, "expires": state["day"] + days}
    return True


def expire(state, current_day):
    released = []
    due = [
        order_id
        for order_id, info in state.get("reservations", {}).items()
        if current_day >= info["expires"]
    ]
    for order_id in due:
        info = state["reservations"].pop(order_id)
        machine_id = info["machine"]
        if state.get("machines", {}).get(machine_id) == order_id:
            state["machines"][machine_id] = None
            released.append(machine_id)
        order = state.get("orders", {}).get(order_id)
        if order is not None and order.get("machine") == machine_id:
            order["machine"] = None
    return released


TRUE_WORDS = {"1", "true", "yes", "y", "paid"}


def _to_int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def main():
    print("洗衣店 - 命令: order/load/assign/fee/cancel/discount/pickup/reserve/expire/quit")
    state = new_game()
    while True:
        try:
            raw = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if raw == "quit":
            break
        if not raw:
            print("错误: 空命令")
            continue
        parts = raw.split()
        cmd, args = parts[0], parts[1:]
        if cmd == "order":
            member = bool(args) and args[0].lower() in TRUE_WORDS
            order_id = next_order_id(state)
            create_order(state, order_id, member)
            print("ok: 订单 %d 已建立 (会员=%s)" % (order_id, member))
        elif cmd == "load":
            if len(args) != 2:
                print("错误: 用法 load <订单号> <衣物号>")
                continue
            order_id = _to_int(args[0])
            print("ok" if order_id is not None and load_cloth(state, order_id, args[1]) else "错误: 投放被拒绝")
        elif cmd == "assign":
            if len(args) != 2:
                print("错误: 用法 assign <订单号> <机器号>")
                continue
            order_id = _to_int(args[0])
            print("ok" if order_id is not None and assign_machine(state, order_id, args[1]) else "错误: 机位不可用")
        elif cmd == "fee":
            if len(args) != 2:
                print("错误: 用法 fee <订单号> <取件日>")
                continue
            order_id, pickup_day = _to_int(args[0]), _to_int(args[1])
            amount = fee(state, order_id, pickup_day) if order_id is not None and pickup_day is not None else None
            print("费用: %s" % amount if amount is not None else "错误: 无法计费")
        elif cmd == "cancel":
            if len(args) != 1:
                print("错误: 用法 cancel <订单号>")
                continue
            order_id = _to_int(args[0])
            returned = cancel_dry(state, order_id) if order_id is not None else []
            if returned is None:
                print("错误: 订单不存在")
            else:
                print("ok: 已返还衣物 %s" % returned)
        elif cmd == "discount":
            if len(args) != 2:
                print("错误: 用法 discount <订单号> <基础费>")
                continue
            order_id, base = _to_int(args[0]), _to_int(args[1])
            amount = discount(state, order_id, base) if order_id is not None and base is not None else None
            print("折后: %s" % amount if amount is not None else "错误: 无法折扣")
        elif cmd == "pickup":
            if len(args) != 2:
                print("错误: 用法 pickup <订单号> <已付款:0/1>")
                continue
            order_id = _to_int(args[0])
            paid = args[1].lower() in TRUE_WORDS
            if order_id is not None and pickup(state, order_id, paid):
                print("ok: 取件完成")
            else:
                print("错误: 取件被拒绝，订单保留")
        elif cmd == "reserve":
            if len(args) != 3:
                print("错误: 用法 reserve <订单号> <机器号> <天数>")
                continue
            order_id, days = _to_int(args[0]), _to_int(args[2])
            ok = order_id is not None and days is not None and reserve(state, order_id, args[1], days)
            print("ok" if ok else "错误: 预约失败")
        elif cmd == "expire":
            if len(args) != 1:
                print("错误: 用法 expire <当前日>")
                continue
            current_day = _to_int(args[0])
            if current_day is None:
                print("错误: 日期非法")
                continue
            print("ok: 释放机位 %s" % expire(state, current_day))
        else:
            print("错误: 非法命令 %s" % cmd)


if __name__ == "__main__":
    main()
