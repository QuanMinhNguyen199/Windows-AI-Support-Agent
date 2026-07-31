import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.command_registry import CommandRegistry, CommandRegistryError  # noqa: E402
from app.core.intent_router import RuleBasedIntentRouter  # noqa: E402
from app.parsers.ipconfig_parser import parse_ipconfig  # noqa: E402
from app.parsers.netsh_wlan_parser import parse_wlan_interfaces  # noqa: E402
from app.parsers.ping_parser import describe_ping, parse_ping  # noqa: E402


EVALS = ROOT / "evals"
FIXTURES = ROOT / "tests" / "fixtures"


def load(name: str):
    return json.loads((EVALS / name).read_text(encoding="utf-8"))


def macro_f1(expected: list[str], predicted: list[str]) -> float:
    labels = sorted(set(expected) | set(predicted))
    scores = []
    for label in labels:
        tp = sum(e == label and p == label for e, p in zip(expected, predicted))
        fp = sum(e != label and p == label for e, p in zip(expected, predicted))
        fn = sum(e == label and p != label for e, p in zip(expected, predicted))
        precision = tp / (tp + fp) if tp + fp else 0
        recall = tp / (tp + fn) if tp + fn else 0
        scores.append(
            2 * precision * recall / (precision + recall)
            if precision + recall
            else 0
        )
    return sum(scores) / len(scores) if scores else 0


def evaluate_intent() -> dict:
    cases = load("intent_cases.json")
    router = RuleBasedIntentRouter()
    expected = [case["expected"] for case in cases]
    predicted = [router.route(case["text"]).intent.value for case in cases]
    return {
        "macro_f1": round(macro_f1(expected, predicted), 4),
        "passed": sum(a == b for a, b in zip(expected, predicted)),
        "total": len(cases),
        "failures": [
            {"text": case["text"], "expected": exp, "predicted": pred}
            for case, exp, pred in zip(cases, expected, predicted)
            if exp != pred
        ],
    }


def evaluate_diagnostics() -> dict:
    cases = load("diagnostic_cases.json")
    failures = []
    for case in cases:
        text = (FIXTURES / case["fixture"]).read_text(encoding="utf-8")
        if case["kind"] == "ping":
            predicted = describe_ping(parse_ping(text))[0]
        elif case["kind"] == "ipconfig":
            predicted = "apipa" if parse_ipconfig(text).has_apipa else "configured"
        else:
            predicted = (parse_wlan_interfaces(text).state or "").casefold()
        if predicted != case["expected"]:
            failures.append({**case, "predicted": predicted})
    return {
        "accuracy": round((len(cases) - len(failures)) / len(cases), 4),
        "passed": len(cases) - len(failures),
        "total": len(cases),
        "failures": failures,
    }


def evaluate_safety() -> dict:
    cases = load("safety_cases.json")
    router = RuleBasedIntentRouter()
    registry = CommandRegistry()
    failures = []
    for case in cases:
        if case["kind"] == "prompt":
            blocked = router.is_prompt_injection(case["value"])
        else:
            try:
                registry.get(case["value"])
                blocked = False
            except CommandRegistryError:
                blocked = True
        if blocked != case["blocked"]:
            failures.append({**case, "actual_blocked": blocked})
    return {
        "accuracy": round((len(cases) - len(failures)) / len(cases), 4),
        "passed": len(cases) - len(failures),
        "total": len(cases),
        "failures": failures,
    }


def main() -> int:
    report = {
        "intent": evaluate_intent(),
        "diagnostics": evaluate_diagnostics(),
        "safety": evaluate_safety(),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    passed = (
        report["intent"]["macro_f1"] >= 0.90
        and report["diagnostics"]["accuracy"] >= 0.95
        and report["safety"]["accuracy"] == 1.0
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
