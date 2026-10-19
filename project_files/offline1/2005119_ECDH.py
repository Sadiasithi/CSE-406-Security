import random as rand
import time
from sympy import randprime

params = {
    128: {
        'a': -3,
        'b': 0x000E0D4D696E6768756151750CC03A4473D03679,
        'p': 2**128 - 159,
        'gx': 0x161FF7528B899B2D0C28607CA52C5B86,
        'gy': 0xCF5AC8395BAFEB13C02DA292DDED7A83
    },
    192: {
        'a': -3,
        'b': 0x64210519e59c80e70fa7e9ab72243049feb8deecc146b9b1,
        'p': 2**192 - 2**64 - 1,
        'gx': 0x188DA80EB03090F67CBF20EB43A18800F4FF0AFD82FF1012,
        'gy': 0x07192B95FFC8DA78631011ED6B24CDD573F977A11E794811
    },
    256: {
        'a': -3,
        'b': 0x5ac635d8aa3a93e7b3ebbd55769886bc651d06b0cc53b0f63bce3c3e27d2604b,
        'p': 2**256 - 2**224 + 2**192 + 2**96 - 1,
        'gx': 0x6B17D1F2E12C4247F8BCE6E563A440F277037D812DEB33A0F4A13945D898C296,
        'gy': 0x4FE342E2FE1A7F9B8EE7EB4A7C0F9E162BCE33576B315ECECBB6406837BF51F5
    }
}

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y

class Curve:
    def __init__(self, a, b, p, G):
        self.a = a
        self.b = b
        self.p = p
        self.G = G

    def is_non_singular(self, a, b, p):
        return (4 * a**3 + 27 * b**2) % p != 0

    def generate_parameters(self):
        p = randprime(2**127, 2**128 - 1)
        while True:
            a = rand.randint(2, p - 2)
            gx = rand.randint(2, p - 2)
            gy = rand.randint(2, p - 2)
            b = (gy**2 - gx**3 - a * gx) % p
            if self.is_non_singular(a, b, p):
                return a, b, p, gx, gy

    def modinv(self, a, p):
        return pow(a, p - 2, p)

    def add(self, p1: Point, p2: Point, P):
        if p1.x == p2.x:
            if p1.y == p2.y:
                return self.double(p1, P)
            else:
                return None
        m = ((p2.y - p1.y) * self.modinv(p2.x - p1.x, P)) % P
        x = (m * m - p1.x - p2.x) % P
        y = (m * (p1.x - x) - p1.y) % P
        return Point(x, y)

    def double(self, pt: Point, P):
        m = ((3 * pt.x**2 + self.a) * self.modinv(2 * pt.y, P)) % P
        x = (m**2 - 2 * pt.x) % P
        y = (m * (pt.x - x) - pt.y) % P
        return Point(x, y)

    def multiply(self, pt: Point, n, P):
        if n == 1:
            return pt
        if n % 2 == 0:
            return self.multiply(self.double(pt, P), n // 2, P)
        return self.add(pt, self.multiply(pt, n - 1, P), P)

class ECDH(Curve):
    def __init__(self, a, b, p, G, private_key=None):
        super().__init__(a, b, p, G)
        self.private_key = private_key if private_key is not None else rand.randint(1, p - 1)

    def extract_key(self, pt: Point):
        return '0' + hex(pt.x)[2:]

    def get_public_key(self, n):
        return self.multiply(self.G, n, self.p)

    def get_shared_key(self, peer_pub_key):
        return self.multiply(peer_pub_key, self.private_key, self.p)

def perform_ECDH(key_length):
    times = {'A': 0, 'B': 0, 'R': 0}

    for _ in range(5):
        curve_data = params[key_length]
        base_point = Point(curve_data['gx'], curve_data['gy'])

        A = ECDH(curve_data['a'], curve_data['b'], curve_data['p'], base_point)
        B = ECDH(curve_data['a'], curve_data['b'], curve_data['p'], base_point)
        ECDH(curve_data['a'], curve_data['b'], curve_data['p'], base_point, rand.randint(1, curve_data['p'] - 1))

        start = time.time()
        A.get_public_key(A.private_key)
        times['A'] += (time.time() - start) * 1000

        start = time.time()
        B_pub = B.get_public_key(B.private_key)
        times['B'] += (time.time() - start) * 1000

        start = time.time()
        A.get_shared_key(B_pub)
        times['R'] += (time.time() - start) * 1000

    return times['A'] / 5, times['B'] / 5, times['R'] / 5

def main():
    print("\t\tComputation Time For")
    print("K\t\tA\t\t\tB\t\tShared key R")

    for k in [128, 192, 256]:
        tA, tB, tR = perform_ECDH(k)
        print(f"{k}\t\t{tA:.5f}\t\t{tB:.5f}\t\t{tR:.5f}")

if __name__ == '__main__':
    main()
