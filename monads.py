from typing import Callable, Tuple, Any, TypeVar, Generic

ST = TypeVar("ST")  # State type


class StateMonad(Generic[ST]):
    def __init__(self, run: Callable[[ST], Tuple[Any, ST]]):
        self.run = run

    def then(self, action: Callable[[Any], "StateMonad[ST]"]) -> "StateMonad[ST]":
        def _run_state(state):
            result, new_state = self.run(state)
            monad = action(result)
            return monad.run(new_state)

        return StateMonad(_run_state)

    @staticmethod
    def get() -> "StateMonad[ST]":
        def _get(state: ST) -> tuple[ST, ST]:
            return (state, state)

        return StateMonad(_get)
