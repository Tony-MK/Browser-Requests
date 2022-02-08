import concurrent.futures;
import time;
import math;

PRIMES = [
    112272535095293,
    112582705942171,
    112272535095293,
    115280095190773,
    115797848077099,
    1099726899285419] * 10

N = 2;

def is_prime(n):
    if n < 2:
        return False
    if n == 2:
        return True
    if n % 2 == 0:
        return False

    sqrt_n = int(math.floor(math.sqrt(n)))
    for i in range(3, sqrt_n + 1, 2):
        if n % i == 0:
            return False
    return True

def process():

    with concurrent.futures.ProcessPoolExecutor(max_workers = 4) as executor:
        for number, prime in zip(PRIMES, executor.map(is_prime, PRIMES)):
            pass;#print('%d is prime: %s' % (number, prime));

def timer(func, n):

    ts = []
    for _ in range(n):
        t = time.perf_counter();
        func();
        ts.append(time.perf_counter() - t);
        pass;

    return sum(ts)/n;

def thread():
    with concurrent.futures.ThreadPoolExecutor(max_workers = 4) as executor:
        for number, prime in zip(PRIMES, executor.map(is_prime, PRIMES)):
            pass;#print('%d is prime: %s' % (number, prime));

if __name__ == '__main__':
    for n in range(1, N):
        print(n, 'Thread :', timer(thread, n), 'Process :', timer(process, n));


