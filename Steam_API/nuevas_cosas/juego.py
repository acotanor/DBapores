class Juego:
    def __init__(
        self,
        appid,
        name="Sin nombre",
        playtime_forever=0,
        playtime_2weeks=0,
        img_icon_url="",
        img_logo_url="",
        has_community_visible_stats=False
    ):
        self.appid = appid
        self.name = name
        self.playtime_forever = playtime_forever
        self.playtime_2weeks = playtime_2weeks
        self.img_icon_url = img_icon_url
        self.img_logo_url = img_logo_url
        self.has_community_visible_stats = has_community_visible_stats

    @property
    def horas_jugadas(self):
        return round(self.playtime_forever / 60, 1)

    @property
    def horas_2_semanas(self):
        return round(self.playtime_2weeks / 60, 1)

    def __str__(self):
        return (
            f"Juego: {self.name}\n"
            f"  AppID: {self.appid}\n"
            f"  Horas jugadas totales: {self.horas_jugadas}\n"
            f"  Horas últimas 2 semanas: {self.horas_2_semanas}\n"
            f"  Icono: {self.img_icon_url}\n"
            f"  Logo: {self.img_logo_url}\n"
            f"  Estadísticas visibles: {self.has_community_visible_stats}"
        )