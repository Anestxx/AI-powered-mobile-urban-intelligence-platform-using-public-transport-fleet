from .config import PRIORITY_RULE_VERSION


def review_priority(bus_ids):
    count = len({value for value in bus_ids if value})
    priority = "high" if count >= 3 else "medium" if count == 2 else "low"
    return {"priority": priority, "priority_reason": f"Reported by {count} distinct bus{'es' if count != 1 else ''}",
            "priority_rule_version": PRIORITY_RULE_VERSION, "distinct_bus_count": count}
