import socket
import importlib

ecdh = importlib.import_module("2005119_ECDH")
aes = importlib.import_module("2005119_AES")

PORT = 12345
HOST = "127.0.0.1"
ENCODING = 'utf-8'

def calculate_shared_key(ecdh_obj, other_public_key):
    return ecdh_obj.extract_key(ecdh_obj.get_shared_key(other_public_key))

def derive_round_keys(shared_key):
    key_str = str(shared_key)
    key_matrix = aes.build_key_matrix(key_str, 4)
    scheduled_keys = aes.schedule_key(key_matrix, 11, 4)
    return aes.generate_round_keys(scheduled_keys, 11)

def aes_encrypt(plaintext, round_keys):
    blocks = aes.generate_blocks(plaintext)
    matrix = aes.build_block_matrix(blocks)
    iv = aes.generate_IV()
    ciphertext_matrix = aes.encrypt(matrix, round_keys, iv)
    return ciphertext_matrix

def aes_decrypt(ciphertext, round_keys):
    blocks = aes.generate_blocks(ciphertext)
    matrix = aes.build_block_matrix(blocks)
    return aes.decrypt(matrix, round_keys)

def receive_ecdh_parameters(connection):
    length = int(connection.recv(1024).decode(ENCODING))
    data = connection.recv(length).decode(ENCODING).split()

    a, b, p = map(int, data[:3])
    G = ecdh.Point(int(data[3]), int(data[4]))
    pub_key_alice = ecdh.Point(int(data[5]), int(data[6]))

    return a, b, p, G, pub_key_alice

def handle_communication(connection, round_keys):
    while True:
        try:
            ciphertext = connection.recv(1024).decode(ENCODING)
            if not ciphertext:
                break
            plaintext = aes_decrypt(ciphertext, round_keys)
            if plaintext == "exit":
                break
            print("CipherText received : " + ciphertext)
            print("Alice: " + plaintext)

            message = input("Bob: ")
            encrypted = aes_encrypt(message, round_keys)
            print("CipherText sent : " + encrypted)
            connection.sendall(encrypted.encode(ENCODING))

            if message == "exit":
                break
        except Exception as e:
            print("Error:", e)
            break

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
        server_socket.bind((HOST, PORT))
        server_socket.listen(1)
        print("Waiting for Alice to connect...")

        conn, addr = server_socket.accept()
        with conn:
            print("Connected to Alice")
            a, b, p, G, pub_key_alice = receive_ecdh_parameters(conn)

            ecdh_bob = ecdh.ECDH(a, b, p, G)
            pub_key_bob = ecdh_bob.get_public_key(ecdh_bob.private_key)

            pub_key_str = f"{pub_key_bob.x} {pub_key_bob.y}"
            conn.sendall(pub_key_str.encode(ENCODING))
            shared_key = calculate_shared_key(ecdh_bob, pub_key_alice)
            print("Shared Key:", shared_key)
            round_keys = derive_round_keys(shared_key)
            handle_communication(conn, round_keys)

if __name__ == "__main__":
    main()
