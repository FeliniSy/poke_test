from datetime import datetime

from etl.PokemonETL import PokemonETLManager

if __name__ == "__main__":
    start_time = datetime.now()
    pipeline = PokemonETLManager()
    pipeline.run(13)
    print(datetime.now() - start_time)
