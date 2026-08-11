import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "src"))

import asyncio

from src.make_call import main

if __name__ == "__main__":
    asyncio.run(main())
