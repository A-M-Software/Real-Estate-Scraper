# coding=utf-8

import asyncio

from src.employee_stats.bot.runner import main


if __name__ == "__main__":
    # Run the main function in an asynchronous event loop
    asyncio.run(main())
