# from Youtube Tutorial https://www.youtube.com/watch?v=t5Bo1Je9EmE

import asyncio

async def fetch_data():
    print("fetach_data begin")
    await asyncio.sleep(2)
    print("fetach_data end")
    return {"data": 1}

async def print_numbers():
    for i in range(10):
        print(i)
        await asyncio.sleep(0.25)
        
async def main():
    task1 = asyncio.create_task(fetch_data())
    task2 = asyncio.create_task(print_numbers())
    
    value = await task1
    print(value)
    
    await task2
    
if __name__ == "__main__":
    asyncio.run(main())