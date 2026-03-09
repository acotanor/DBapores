from juego import Juego


class ListaJuegos:
    def __init__(self, juegos=None):
        self.juegos = juegos if juegos is not None else []

    def agregar_juego(self, juego):
        if isinstance(juego, Juego):
            self.juegos.append(juego)
        else:
            raise TypeError("Solo se pueden agregar objetos de tipo Juego.")

    def ordenar_por_tiempo_jugado(self, descendente=True):
        self.juegos.sort(key=lambda juego: juego.playtime_forever, reverse=descendente)

    def total_juegos(self):
        return len(self.juegos)

    def mostrar_por_consola(self, top=None):
        if not self.juegos:
            print("La lista de juegos está vacía.")
            return

        juegos_a_mostrar = self.juegos[:top] if top is not None else self.juegos

        print(f"\nTotal de juegos en la lista: {self.total_juegos()}\n")
        print(f"{'Juego':<40} | {'Horas jugadas':<15} | {'AppID'}")
        print("-" * 75)

        for juego in juegos_a_mostrar:
            print(f"{juego.name[:40]:<40} | {juego.horas_jugadas:<15} | {juego.appid}")

    @classmethod
    def desde_api(cls, games_data):
        lista = cls()

        for game in games_data:
            juego = Juego(
                appid=game.get("appid"),
                name=game.get("name", "Sin nombre"),
                playtime_forever=game.get("playtime_forever", 0),
                playtime_2weeks=game.get("playtime_2weeks", 0),
                img_icon_url=game.get("img_icon_url", ""),
                img_logo_url=game.get("img_logo_url", ""),
                has_community_visible_stats=game.get("has_community_visible_stats", False)
            )
            lista.agregar_juego(juego)

        return lista

    def __str__(self):
        return f"ListaJuegos con {self.total_juegos()} juegos"