from psycopg2.extras import execute_values

from sql_manager.queries import insert_into_ability
from sql_manager.pool import pool

class Ability:

    @staticmethod
    def ability_generator(data):
        for row in data:
            url = row["url"]
            yield (
                row["name"],
                url,
                url.rstrip("/").split("/")[-1]
            )

    @staticmethod
    def keep_abilities_in_db(abilities):
        conn = None
        try:
            conn = pool.getconn()
            with conn:
                with conn.cursor() as cursor:
                    execute_values(cursor, insert_into_ability, abilities)
        finally:
            if conn:
                pool.putconn(conn)



# if __name__ == "__main__":
#     response = requests.get(ABILITY_URL)
#     data = response.json()
#     all_abilities = data['results']
#     Ability.keep_abilities_in_db(Ability.ability_generator(all_abilities))