class TagGameAdapter:
    @staticmethod
    def adapt(raw: dict) -> dict:
        return {
            "appid": str(raw.get("appid", "")).strip(),
            "name": str(raw.get("name", "Sin nombre")).strip() or "Sin nombre",
            "positive": int(raw.get("positive", 0) or 0),
            "relevancia": float(raw.get("relevancia", 0) or 0),
        }