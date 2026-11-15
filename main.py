"""Text interface. Contains NO business logic: it only parses commands,
calls DeliverySystem, and formats results.

NOTE: the exact Quera input/output format must be checked against the
Quera statement; all output formatting lives in the small helpers below
so it is easy to adjust.
"""
from __future__ import annotations

import sys

from delivery_system import DeliverySystem

ERROR = "ERROR: unknown command"


def _pos(a, b):
    combined = f"{a} {b}"
    cleaned = combined.replace("(", "").replace(")", "").replace(",", "")
    parts = cleaned.split()
    return (int(parts[0]), int(parts[1]))


def process_command(system: DeliverySystem, line: str):
    """Run one command line; return the output text (None for blank/END)."""
    parts = line.split()
    if not parts:
        return None
    cmd, args = parts[0].upper(), parts[1:]
    try:
        if cmd == "ADD-DRIVER": 
            u, x, y, cat = args
            success = system.add_driver(u, _pos(x, y), cat)
            return "user added successfully" if success else "user previously added"
        
        if cmd == "CREATE-ORDER": 
            cat, sx, sy, fx, fy = args
            order_id = system.create_order(cat, _pos(sx, sy), _pos(fx, fy))
            return "invalid order" if order_id is None else str(order_id)
        
        if cmd == "ASSIGN-NEXT-ORDER": 
            (u,) = args
            try:
                order_id = system.assign_next_order(u)
                if order_id is None:
                    return "there is no order right now"
                return f"{order_id} assigned to {u}"
            except KeyError:
                return "invalid driver name"
            except RuntimeError:
                return "driver is already busy"
            
        if cmd == "GET-DRIVER": 
            (u,) = args
            r = system.get_driver(u)
            if r is None:
                return "invalid driver name"
            status, pos, credit = r
            return f"{status} ({pos[0]}, {pos[1]}) {int(credit)}"
              
        if cmd == "ORDER-UPDATE": 
            status, u, oid_str = args
            try:
                driver = system._get_driver_or_raise(u)
            except KeyError:
                return "invalid driver name"           
            try:
                oid = int(oid_str)
                order = system._orders.get(oid)
                if order is None or order.assigned_driver is not driver:
                    return "wrong order-id"                
                success = system.update_order_status(u, oid, status)
                if success:
                    return "status changed successfully"
                else:
                    return "invalid status"
            except (TypeError, ValueError):
                return ERROR
        
        if cmd == "GET-ORDER":
            (oid,) = args
            r = system.get_order(int(oid))
            if r is None:
                    return "invalid order"
            status, driver_name, cost = r
            d_str = "None" if driver_name is None else driver_name
            return f"{status} {d_str} {cost}"
        
        if cmd == "GET-ORDER-LIST":
            (s,) = args
            order_ids = system.get_order_list(s)
            return "None" if not order_ids else " ".join(str(x) for x in order_ids)
        
        if cmd == "GET-DRIVER-LIST": 
            (s,) = args
            driver_names = system.get_driver_list(s)
            return "None" if not driver_names else " ".join(str(x) for x in driver_names)
        
        if cmd == "GET-NEAR-DRIVER": 
            x, y, n_str = args
            n = int(n_str)
            driver_names = system.get_near_drivers(_pos(x, y), int(n))
            return "None" if not driver_names else " ".join(str(x) for x in driver_names)
        
        if cmd == "GET-CNT-ORDER": 
            x, y, d, e = args
            return str(system.count_orders(_pos(x, y), int(d), e))
        
        if cmd == "GET-NEAREST-PENDING-ORDER": 
            x, y = args
            order_id = system.get_nearest_pending_order(_pos(x, y))
            return "None" if order_id is None else str(order_id)
        
        if cmd == "GET-COMPANY": 
            return str(int(system.get_company_credit()))
        
        # ---- bonus ----
        if cmd == "GET-DRIVER-SCORE":
            (u,) = args
            try:
                score = system.get_driver_score(u)
            except KeyError:
                return "invalid driver name"
            return "no score" if score is None else f"{score:.1f}"

        if cmd == "GIVE-DRIVER-SCORE":
            u, s_str = args
            try:
                score = int(s_str)
            except ValueError:
                return "invalid score"
            try:
                system.give_driver_score(u, score)
            except KeyError:
                return "invalid driver name"
            except ValueError:
                return "score out of range"
            return "score added successfully"
        
        if cmd == "END":
            return None
        
    except (TypeError, ValueError, KeyError, RuntimeError) as e:
        return f"ERROR: {e}"
    
    return ERROR  # unknown command


def main(stdin=None, stdout=None):
    stdin = stdin or sys.stdin
    stdout = stdout or sys.stdout
    system = DeliverySystem()
    for line in stdin:
        if line.split()[:1] == ["END"]:
            break
        out = process_command(system, line)
        if out is not None:
            print(out, file=stdout)


if __name__ == "__main__":
    main()


# def main(commands: str = "", stdout=None):
#     stdout = stdout or sys.stdout
#     system = DeliverySystem()
#     for line in commands.splitlines():
#         if not line.strip():
#             continue
#         if line.split()[:1] == ["END"]:
#             break
#         out = process_command(system, line)
#         if out is not None:
#             print(out, file=stdout)


# if __name__ == "__main__":
#     COMMANDS = """
# ADD-DRIVER Ali (0, 0) BIKE
# ADD-DRIVER Sara (5, 5) TRUCK
# ADD-DRIVER Reza (10, 10) TRUCK
# GIVE-DRIVER-SCORE Ali 5
# GIVE-DRIVER-SCORE Ali 5
# GIVE-DRIVER-SCORE Ali 1
# GIVE-DRIVER-SCORE Sara 1
# GIVE-DRIVER-SCORE Sara 2
# GET-DRIVER-SCORE Ali
# GET-DRIVER-SCORE Sara
# GET-DRIVER-SCORE Reza

# ADD-DRIVER Mohammad021 (-142, 21) TRUCK
# ADD-DRIVER kami (20, 20) VAN
# ADD-DRIVER 00MOHSEN (0, 128) TRUCK
# ADD-DRIVER kami (30, 30) BIKE
# ADD-DRIVER SaMi (55, -2) BIKE
# GET-DRIVER 00MOHSEN
# CREATE-ORDER TRUCK (0, 0) (100, 18)
# CREATE-ORDER BIKE (19, -38) (-40, 127)
# CREATE-ORDER VAN (16, 16) (-75, 75)
# ASSIGN-NEXT-ORDER SaMi
# CREATE-ORDER TRUCK (-10, 100) (-11, 100)
# ASSIGN-NEXT-ORDER 00MOHSEN
# ASSIGN-NEXT-ORDER SaMi
# GET-DRIVER sami
# GET-DRIVER SaMi
# ORDER-UPDATE DELIVERED 00MOHSEN 3
# ORDER-UPDATE PICKUP 00MOHSEN 4
# ORDER-UPDATE DELIVERED 00MOHSEN 4
# GET-DRIVER 00MOHSEN
# GET-ORDER 2
# GET-ORDER 3
# GET-ORDER-LIST PENDING
# GET-ORDER-LIST ARRIVED
# GET-DRIVER-LIST BUSY
# GET-DRIVER-LIST FREE
# GET-NEAR-DRIVER (78, 29) 2
# GET-NEAR-DRIVER (-70, 50) 1
# GET-CNT-ORDER (0, 0) 133 FINISH
# GET-CNT-ORDER (-29, 101) 77 START
# GET-NEAREST-PENDING-ORDER (17, 23)
# GET-NEAREST-PENDING-ORDER (0, 0)
# GET-COMPANY
# ORDER-UPDATE PICKUP SaMi 2
# ORDER-UPDATE DELIVERED SaMi 2
# GET-COMPANY
# END

# """

# main(COMMANDS)
