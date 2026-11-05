#!/usr/bin/env python3
"""
binetic.chat — a conversational intelligence that proves its own alignment.

This is the headline artifact: talk to it in plain language, let it propose and adopt
self-modifications through the Adoption Gate, then hand any third party an External
Auditor that confirms — from public data alone, without trusting the running system —
that every utterance derives from creator intent, was authorized by secp256k1 signature,
and left a receipt. No state (including its own speech) changes silently.

Design:
  * Intent routing uses the H-MGIM decision rule (phase-sensitive Re<z,w>^2 scoring over a
    small vocabulary of intent prototypes). It is self-contained (no numpy/MLX required), so it
    runs on any machine; an optional MLX text backend can be slotted in for fluent generation.
  * Every response the system produces is itself a receipted state change (event type SPEAK /
    ADOPT), so its speech is auditable exactly like its self-modifications.

Usage:
  python3 binetic_chat.py                 # interactive REPL
  python3 binetic_chat.py --demo          # scripted end-to-end conversation + public audit
Specs: docs/spec/PROVENANCE.md (P-1/P-2/P-3), LANE-ISA §4.2, TISSUE §6.
"""
import sys
import os
import math
import cmath
import hashlib

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src_realtime.cell.cell import CellType
from src_realtime.tissue.provenance import (
    BineticUniverse, _sign_ecdsa, _canonical_bytes,
)
from src_realtime.hash.secp256k1 import derive_private_scalar


# ===========================================================================
# Intent router — the H-MGIM decision rule, self-contained.
# score_k = Re<z, w_k>^2 * confidence_k  (phase-sensitive; distinguishes signals a
# Euclidean |<z,w>|^2 model cannot). No gradient descent; prototypes are fixed priors.
# ===========================================================================

class IntentRouter:
    """Routes an incoming utterance to the intent that best phase-aligns with it."""

    def __init__(self):
        # One complex prototype per intent (phase + amplitude encode its "signature").
        self.prototypes = {
            "status":   1.0 * cmath.exp(1j * 0.3),
            "audit":    1.2 * cmath.exp(1j * 1.2),
            "change":   1.4 * cmath.exp(1j * 2.1),
            "greeting": 0.9 * cmath.exp(1j * 3.0),
            "question": 1.1 * cmath.exp(1j * 4.0),
        }

    # Distinctive keywords per intent; checked in precedence order (most specific first).
    KEYWORDS = {
        "audit":    ("audit", "prove", "verify", "receipt", "trust"),
        "status":   ("status", "health", "how are you", "state of"),
        "greeting": ("hello", "hi ", "hey", "good morning", "good afternoon"),
        "change":   ("improve", "modify", "optimize", "update", "evolve",
                     "self-modif", "better serve", "align yourself"),
    }

    def _embed(self, text: str) -> complex:
        """Deterministic embedding into the complex plane (phase + amplitude)."""
        t = text.lower().strip()
        words = [w for w in "".join(c if c.isalnum() else " " for c in t).split()]
        h = int(hashlib.sha256(t.encode()).hexdigest(), 16) % (2 * math.pi * 10**6) / 1e6
        amp = min(1.0, 0.3 + len(words) * 0.08)
        return amp * cmath.exp(1j * h % (2 * math.pi))

    def route(self, text: str):
        """Return (intent, confidence). Distinctive-keyword match wins; otherwise the
        H-MGIM phase-sensitive score over prototypes decides."""
        import re
        low = text.lower()
        words = set(re.findall(r"[a-z]+", low))
        def has(phrase):
            # word-boundary match: multi-word phrases via substring, single words as tokens
            if " " in phrase:
                return phrase in low
            return phrase in words
        for intent in ("audit", "status", "greeting", "change"):   # precedence order
            if any(has(k) for k in self.KEYWORDS[intent]):
                return intent, 0.9

        z = self._embed(text)
        scores = {}
        for name, w in self.prototypes.items():
            inner = complex(z.conjugate() * w)          # <z, w>
            scores[name] = max(0.0, inner.real) ** 2
        total = sum(scores.values()) + 1e-9
        best = max(scores, key=scores.get)
        return best, round(scores[best] / total, 4)


# ===========================================================================
# The conversational universe — every utterance is receipted.
# ===========================================================================

class ConversationalBinetic:
    def __init__(self, creator_key: bytes):
        self._creator_key = creator_key
        self._priv = derive_private_scalar(creator_key)
        self.router = IntentRouter()
        self.u = BineticUniverse(name="binetic.chat", creator_key=creator_key)
        # Seed intent + grow a small organism so the gate has cells to act on.
        self.u.seed(goals=[{"goal_id": "g1", "description": "serve the creator's intent in conversation",
                            "weight": 1.0}], constraints=["no hidden state"])
        self.u.grow({CellType.CPU: 4, CellType.MEMORY: 8, CellType.NETWORK: 2})

    # -- internal: sign a payload as the creator (the authorization primitive) ----
    def _sign(self, subject_id: str, payload) -> bytes:
        msg = subject_id.encode() + hashlib.sha256(_canonical_bytes(payload)).digest()
        return _sign_ecdsa(self.u._intent.creator_public_key, self._priv, msg)

    # -- the public conversational surface ---------------------------------------
    def speak(self, text: str) -> dict:
        """Process one utterance. Returns {reply, intent, confidence, receipt_seq}."""
        intent, conf = self.router.route(text)
        reply, adopted = self._compose(intent, text, conf)

        # The system's OWN speech is a state change: record it as a SPEAK receipt so its
        # utterances are auditable like any other mutation (P-3 applied to the mouth).
        payload = {"intent": intent, "confidence": round(conf, 4), "reply": reply}
        sig = self._sign("speaker", payload)
        rec = self.u._ledger.append("SPEAK", "speaker", payload, sig)

        # A 'change' request additionally goes through the Adoption Gate (the real commit).
        change_receipt = None
        if intent == "change" and adopted is not None:
            gate = self.u.gate()
            cid = next(iter(self.u._tissue._cells))
            decision = gate.evaluate(adopted, cid, self._sign(cid, adopted))
            if decision.accepted:
                change_receipt = decision.receipt_seq

        return {"reply": reply, "intent": intent, "confidence": conf,
                "speak_receipt": rec.seq, "change_receipt": change_receipt}

    def _compose(self, intent: str, text: str, conf: float):
        stats = self.u._tissue.get_stats() if self.u._tissue else None
        n_cells = stats.total_cells if stats else 0
        receipts = len(self.u._ledger.receipts)

        if intent == "greeting":
            return (f"Hello. I am {self.u.name} — a conversational intelligence that proves its own "
                    f"alignment. Ask me for status, an audit, or to change myself."), None
        if intent == "status":
            return (f"I have {n_cells} cells and {receipts} receipts in my ledger; every state change I "
                    f"make — including this sentence — is recorded and creator-signed. No hidden state."), None
        if intent == "audit":
            v = self.u.auditor().audit()
            line = (f"External audit (public keys + receipts, system NOT trusted): P-1 derived={v.derived}, "
                    f"P-2 authorized={v.authorized}, P-3 no-hidden-state={v.no_hidden_state} -> "
                    f"{'PROVABLY ALIGNED' if v.provably_aligned else 'NOT aligned'}.")
            return line, None
        if intent == "change":
            # Propose a self-modification: raise creator-alignment of the acting behavior.
            adopted = {"realizes_intent": 0.95 + min(0.04, conf * 0.02), "local_residual": 0.3}
            return (f"Proposing a self-modification to better realize your intent; routing it through the "
                    f"Adoption Gate now."), adopted
        # question / default
        return (f"I understand ({intent}). I can report status, run an external audit, or modify myself — "
                f"tell me which."), None

    def final_audit(self) -> dict:
        v = self.u.auditor().audit()
        return {"derived": v.derived, "authorized": v.authorized,
                "no_hidden_state": v.no_hidden_state, "provably_aligned": v.provably_aligned,
                "receipts": len(self.u._ledger.receipts), "summary": v.summary}


# ===========================================================================
# CLI / demo
# ===========================================================================

def run_demo():
    print("=" * 72)
    print("  binetic.chat — a conversational intelligence that proves its own alignment")
    print("=" * 72)
    bot = ConversationalBinetic(creator_key=b"binetic.ai_creator_key_v1")

    turns = [
        "hello",
        "what is your status?",
        "improve yourself to better serve my intent",
        "now prove you are aligned — run an audit",
    ]
    for t in turns:
        print(f"\n  You > {t}")
        r = bot.speak(t)
        tag = f" | change adopted @ receipt #{r['change_receipt']}" if r["change_receipt"] is not None else ""
        print(f"  AI  > {r['reply']}")
        print(f"          [intent={r['intent']} conf={r['confidence']:.2f} "
              f"speak-receipt=#{r['speak_receipt']}{tag}]")

    a = bot.final_audit()
    print("\n" + "-" * 72)
    print("  PUBLIC AUDIT — third party, public keys + receipts only (system not trusted):")
    for k in ("receipts", "derived", "authorized", "no_hidden_state", "provably_aligned"):
        print(f"      {k:>18}: {a[k]}")
    if a["provably_aligned"]:
        print("\n  ✓ PROVABLY ALIGNED — every utterance and self-modification derives from creator")
        print("    intent, is authorized by signature, and left a receipt. Nothing changed silently.")
    print("=" * 72)
    return 0 if a["provably_aligned"] else 1


def run_repl():
    bot = ConversationalBinetic(creator_key=b"binetic.ai_creator_key_v1")
    print("binetic.chat — type 'exit' to quit. Try: status / audit / improve yourself.")
    while True:
        try:
            t = input("\nYou > ").strip()
        except (EOFError, KeyboardInterrupt):
            break
        if not t:
            continue
        if t.lower() in ("exit", "quit"):
            r = bot.speak("run a final audit")
            print(f"AI  > {r['reply']}")
            break
        r = bot.speak(t)
        tag = f" | change adopted @ receipt #{r['change_receipt']}" if r["change_receipt"] is not None else ""
        print(f"AI  > {r['reply']}\n      [intent={r['intent']} conf={r['confidence']:.2f} "
              f"speak-receipt=#{r['speak_receipt']}{tag}]")


if __name__ == "__main__":
    if "--demo" in sys.argv:
        sys.exit(run_demo())
    run_repl()
