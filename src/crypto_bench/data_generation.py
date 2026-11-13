import random

def payload(size, seed):
    r = random.Random(seed)
    return bytes(r.randrange(256) for _ in range(size))
