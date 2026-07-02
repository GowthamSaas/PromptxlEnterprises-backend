class HistoryService:
    def __init__(self) -> None:
        pass

    def record_generation(self, payload: dict[str, object]) -> dict[str, object]:
        return {"status": "recorded", **payload}
