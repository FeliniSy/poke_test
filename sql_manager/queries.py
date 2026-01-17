insert_into_ability = """
                               INSERT INTO ability(name, url, url_id)
                               VALUES %s
                               ON CONFLICT (url_id) DO NOTHING
                           """

insert_into_pokemon = """
                           INSERT INTO pokes(id_pokes, name, base_experience, height, weight, poke_order)
                           VALUES %s
                           ON CONFLICT (id_pokes) DO NOTHING
                       """

insert_into_pokemon_ability = """
                        INSERT INTO pokes_ability(id_ability, id_pokes)
                        VALUES %s
                        ON CONFLICT (id_ability, id_pokes) DO NOTHING
                    """



insert_into_poke_media = """
                        insert into poke_media(name, media_url)
                        values %s
                        ON CONFLICT (name, media_url) DO NOTHING
                        """


find_ability_ids = "SELECT id_ability, url_id FROM ability WHERE url_id = ANY(%s)"

save_gcs_url = "SELECT id_pokes, name FROM pokes ORDER BY id_pokes"