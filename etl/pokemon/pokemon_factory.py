from etl.pokemon.pokemon import Pokemon


class PokemonFactory:

    @staticmethod
    def from_api(data: dict) -> Pokemon:
        return Pokemon(
            id=data["id"],
            name=data["name"],
            base_experience=data["base_experience"],
            height=data["height"],
            weight=data["weight"],
            poke_order=data["order"]
        )
