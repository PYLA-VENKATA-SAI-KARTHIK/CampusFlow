import asyncio
import asyncpg

async def main():
    try:
        conn = await asyncpg.connect('postgresql://campusflow:campusflow_dev@localhost:5432/campusflow_test')
        await conn.execute('CREATE SCHEMA IF NOT EXISTS campusflow AUTHORIZATION campusflow;')
        print('SUCCESS schema created')
    except Exception as e:
        print(f'Failed: {e}')
            
asyncio.run(main())
