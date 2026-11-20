# Trusted grader: edit per-case limits, comparisons, and scoring here.
import json

def grade(ctx):
    for case in json.loads(ctx.assets["cases"]):
        ctx.check(case["input"], case["expected"], points=10,
                  hidden=case.get("hidden", True), large=case.get("large", False),
                  timeout=2, memory_mb=256, compile_timeout=30)
