import psycopg2
import os

def connect_market_db():
    try:
        with psycopg2.connect(
            host=os.environ['MARKET_DB_HOST'],
            dbname=os.environ['MARKET_DB_DATABASE'],
            user=os.environ['MARKET_DB_USER'],
            password=os.environ['MARKET_DB_PASSWORD'],
        ) as conn:
            print('Connected to the PostgreSQL server.')
            return conn
    except (psycopg2.DatabaseError, Exception) as error:
        print(error)
        
def save_market_to_db(supermarket, cursor, geocoder):
    id = get_market_by_url(cursor, supermarket.url)
    if(id):
        sup_values = (
            supermarket.delivery_price, 
            supermarket.takeout,
            id
        )
        cursor.execute(
            """
                UPDATE supermarket 
                SET delivery_price = %s, 
                    takeout = %s
                WHERE id = %s
            """,
            sup_values
        )
    else:
        response = geocoder.forward(
            supermarket.address,
            types=['address'],
            limit=1,
            country=['br']
        )
        [longitude, latitude] = response.geojson()['features'][0]['geometry']['coordinates']
        sup_values = (
            supermarket.name, 
            supermarket.url, 
            supermarket.zip_code, 
            supermarket.address,
            latitude,
            longitude,
            f'Point({latitude} {longitude})',
            supermarket.cnpj, 
            supermarket.delivery_price, 
            supermarket.takeout
        )
        cursor.execute(
            """
                INSERT INTO supermarket (name, url, zip_code, address, latitude, longitude, coordinate_geom, cnpj, delivery_price, takeout)
                VALUES (%s::text, %s::text, %s::text, %s::text, %s, %s, ST_GeomFromText(%s, 4326), %s::text, %s, %s)
                RETURNING id
            """,
            sup_values
        )
        id = cursor.fetchone()[0]
    return id

def save_working_hours(market_id, supermarket, cursor):
    for day_of_week in vars(supermarket.working_hours):
        # See how to add timestamp type to postgres
        wh_day = getattr(supermarket.working_hours, day_of_week)
        wh_values = (
            market_id,
            day_of_week,
            wh_day.start if wh_day != None else None,
            wh_day.end if wh_day != None else None,
            wh_day.start if wh_day != None else None,
            wh_day.end if wh_day != None else None
        )
        cursor.execute(
            """
                INSERT INTO working_hours (market_id, day_of_week, opening_time, closing_time)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (market_id, day_of_week)
                DO UPDATE SET
                    opening_time = %s,
                    closing_time = %s
            """,
            wh_values
        )

def save_products_to_db(market_id, supermarket, cursor):
    cursor.execute(
        """
            DELETE
            FROM market_product
            WHERE market_id = %s
        """,
        (market_id,)
    )
    for product in supermarket.products:
        # See how to add timestamp type to postgres
        # GET MARKET ID, CREATE OR GET FROM RESPONSE OF MARKET ADD
        product_values = (product.ean, product.name, product.description)
        cursor.execute(
            """
                INSERT INTO product (ean, name, description)
                VALUES (%s, %s::text, %s::text)
                ON CONFLICT DO NOTHING
            """,
            product_values
        )
        mp_values = (market_id, product.ean, product.price)
        cursor.execute(
            """
                INSERT INTO market_product (market_id, ean, price)
                VALUES (%s, %s, %s::float)
                ON CONFLICT DO NOTHING
            """,
            mp_values
        )

def save_to_db(supermarket, conn, geocoder):
    print('Saving Market: ', supermarket.name)
    cursor = conn.cursor()
    market_id = save_market_to_db(supermarket, cursor, geocoder)
    print('save market')
    save_working_hours(market_id, supermarket, cursor)
    print('save hours')
    save_products_to_db(market_id, supermarket, cursor)
    print('save products')
    cursor.close()
    conn.commit()
    return

def get_market_by_url(cursor, url):
    try:
        cursor.execute(
            """
                SELECT id 
                FROM supermarket
                WHERE url = %s
            """,
            (url,)
        )
        res = cursor.fetchone()
        return res[0] if res != None else None
    except (psycopg2.DatabaseError, Exception) as error:
        print('Error getting market by url')
        raise error
        