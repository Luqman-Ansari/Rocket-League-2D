# laya_controller/controller.py
"""LayaController: a car driven by Laya, with the same predict() the game calls on SB3 models."""
import time
from concurrent.futures import ThreadPoolExecutor

from src.settings import BALL_FRICTION, CAR_FRICTION
from laya_controller.features import canonical, facts, world_action
from laya_controller.versions import DEFAULT_VERSION, VERSIONS

MODEL_ID = "convaiinnovations/laya"

_laya = ThreadPoolExecutor(max_workers=1)  # one Laya call at a time, shared by all controllers
_agent = None
_cache = {}  # (version, state text) -> (action, probability); Laya answers the same text the same way


def ask(questions, text):
    """Laya's answers to `questions` about `text`, and the ms it took. Loads the model on first use."""
    global _agent
    if _agent is None:
        import laya  # the torch/transformers import and model load happen here, off the game thread

        _agent = laya.load(MODEL_ID)
    start = time.perf_counter()
    answers = _agent.predict(text, questions)["answers"]
    return answers, (time.perf_counter() - start) * 1000


class LayaController:
    def __init__(self, version=DEFAULT_VERSION, side="left", every=6, sync=False,
                 ball_friction=BALL_FRICTION, car_friction=CAR_FRICTION):
        """
        version: a key of versions.VERSIONS.  side: the half the car starts on ("left" is Blue, "right" is Red).
        every: frames between decisions (6 = 10 a second at 60 FPS).
        sync: wait for each answer instead of driving on while Laya thinks (deterministic headless runs).
        ball_friction, car_friction: the game mode's, for predicting where the ball goes (v5+).
        """
        self.version = version
        self.v = VERSIONS[version]
        self.side, self.every, self.sync = side, every, sync
        self.frictions = {"ball_friction": ball_friction, "car_friction": car_friction}
        self.choice = None  # Laya's latest action; None until it has answered once
        self.prob = 0.0
        self.label = "Laya loading..."  # shown above the car in-game
        self.failed = False
        self.asks, self.hits, self.ms = 0, 0, []
        self._frame = 0
        self._pending = None

    def predict(self, obs, deterministic=True):
        """Same shape as an SB3 model's predict(): returns (action, None)."""
        f = facts(canonical(obs, self.side))
        f.update(self.frictions)
        self._collect()
        if self._frame % self.every == 0:
            self._decide(self.v.describe(f))
        self._frame += 1

        if self.choice is None:  # Laya is still loading, or failed: this version's rules drive
            action = self.v.teacher(f)
            self.label = f"rules: {action}"
        else:
            action = self.choice
            self.label = f"{action} {self.prob:.0%}"
        return world_action(self.v.act(action, f), self.side), None

    def _decide(self, text):
        key = (self.version, text)
        if key in _cache:
            self.hits += 1
            self.choice, self.prob = _cache[key]
        elif self._pending is None and not self.failed:
            self._pending = key, _laya.submit(ask, self.v.questions, text)
            if self.sync:
                self._collect(wait=True)

    def _collect(self, wait=False):
        """Take Laya's answer if it has arrived."""
        if self._pending is None or not (wait or self._pending[1].done()):
            return
        key, future = self._pending
        self._pending = None
        try:
            answers, ms = future.result()
        except Exception as e:
            self.failed = True
            print(f"[laya] {e!r} - the scripted rules will drive this car")
            return
        _cache[key] = self.v.decide(answers)
        self.asks += 1
        self.ms.append(ms)
        self.choice, self.prob = _cache[key]
