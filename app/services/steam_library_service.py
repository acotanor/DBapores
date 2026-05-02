class SteamLibraryService:
    def __init__(self, steam_api_client, disk_cache=None):
        self.steam_api_client = steam_api_client
        self.disk_cache = disk_cache

    def get_owned_games(self, steam_id: str) -> list[dict]:
        return self.steam_api_client.get_owned_games(steam_id)

    def get_game_achievements(self, steam_id: str, game: dict) -> dict:
        """Fetches and processes achievements for a game (no disk caching for achievements)."""
        appid = str(game.get('appid', ''))
        game_name = game.get('name', 'Sin nombre')
        
        try:
            logros = self.steam_api_client.get_player_achievements(steam_id, appid)
            if not logros:
                return None
            
            total_logros = len(logros)
            obtenidos = [l for l in logros if l.get('achieved') == 1]
            total_obtenidos = len(obtenidos)
            porcentaje = round((total_obtenidos / total_logros) * 100) if total_logros > 0 else 0
            
            # Fetch global percentages
            global_percs = self.steam_api_client.get_global_achievement_percentages(appid)
            
            for l in obtenidos:
                l['global_percent'] = global_percs.get(l.get('apiname', ''), 100.0)
            
            obtenidos.sort(key=lambda x: x.get('global_percent', 100.0))
            
            rarest = []
            for l in obtenidos[:3]:
                percent = l.get('global_percent', 100.0)
                icon = None
                if percent < 5:
                    icon = 'oro.png'
                elif percent < 20:
                    icon = 'plata.png'
                elif percent < 50:
                    icon = 'bronce.png'
                
                rarest.append({
                    'name': l.get('name', l.get('apiname', 'Desconocido')),
                    'description': l.get('description', 'Sin descripción'),
                    'icon': icon,
                    'global_percent': round(percent, 1)
                })
            
            result = {
                'game_name': game_name,
                'percentage': porcentaje,
                'total_obtained': total_obtenidos,
                'total': total_logros,
                'rarest': rarest
            }
            
            return result
        except Exception as e:
            print(f"Error in SteamLibraryService.get_game_achievements for {appid}: {e}")
            return None