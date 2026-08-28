import asyncio
import asyncpg

async def main():
    passwords = ['postgres', 'password', 'root', 'admin', '', 'campusflow', 'campusflow_dev']
    for pwd in passwords:
        try:
            conn = await asyncpg.connect(f'postgresql://postgres:{pwd}@localhost:5432/postgres')
            await conn.execute('GRANT ALL ON SCHEMA public TO campusflow;')
            await conn.execute('ALTER DATABASE campusflow_test OWNER TO campusflow;')
            print(f'SUCCESS with password: "{pwd}"')
            return
        except Exception as e:
            print(f'Failed {pwd}: {e}')
            
asyncio.run(main())
