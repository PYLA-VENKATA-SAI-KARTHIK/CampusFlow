import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect('postgresql://postgres:postgres@localhost:5432/campusflow_test')
        await conn.execute('GRANT ALL ON SCHEMA public TO campusflow_dev;')
        print('OK')
    except Exception as e:
        print(f"Failed with postgres:postgres: {e}")
        try:
            conn = await asyncpg.connect('postgresql://postgres@localhost:5432/campusflow_test')
            await conn.execute('GRANT ALL ON SCHEMA public TO campusflow_dev;')
            print('OK without password')
        except Exception as e2:
            print(f"Failed again: {e2}")

asyncio.run(main())
