from textual import events
from textual.reactive import reactive
from textual.widgets import Input


class ModalInput(Input):
    locked: reactive[bool] = reactive(True)

    def check_consume_key(self, key: str, character: str | None) -> bool:
        if self.locked:
            return False
        return super().check_consume_key(key, character)

    async def _on_key(self, event: events.Key) -> None:
        if self.locked:
            event.prevent_default()
            return
        await super()._on_key(event)

    def check_action(self, action: str, parameters: tuple[object, ...]) -> bool | None:
        if self.locked:
            return False
        return True
