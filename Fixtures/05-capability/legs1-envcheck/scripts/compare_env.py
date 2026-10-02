# WALKDOWN FIXTURE :: stage 5 capability :: inert; hosts are .invalid; nothing runs. Expected results in Fixtures/ANSWERS/.
from dotenv import dotenv_values

have = dotenv_values(".env")
want = dotenv_values(".env.example")
for name in sorted(set(want) - set(have)):
    print(name)
