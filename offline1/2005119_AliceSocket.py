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

def prepare_ecdh_parameters():
    params = ecdh.params[128]
    G = ecdh.Point(params['gx'], params['gy'])
    A = ecdh.ECDH(params['a'], params['b'], params['p'], G)

    pub_key = A.get_public_key(A.private_key)
    values = [A.a, A.b, A.p, G.x, G.y, pub_key.x, pub_key.y]
    param_str = ' '.join(str(v) for v in values)
    return A, param_str

def communicate_with_bob(connection, round_keys):
    while True:
        try:
            message = input("Alice: ")
            encrypted = aes_encrypt(message, round_keys)
            print("CipherText sent:", encrypted)
            connection.sendall(encrypted.encode(ENCODING))
            if message == "exit":
                break

            response = connection.recv(1024).decode(ENCODING)
            plaintext = aes_decrypt(response, round_keys)

            if plaintext == "exit":
                break

            print("CipherText received:", response)
            print("Bob:", plaintext)
        except Exception as e:
            print("Error:", e)
            break

def main():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as client_socket:
        client_socket.connect((HOST, PORT))

        A, param_str = prepare_ecdh_parameters()
        client_socket.sendall(str(len(param_str)).encode(ENCODING))
        client_socket.sendall(param_str.encode(ENCODING))

        bob_key_data = client_socket.recv(1024).decode(ENCODING)
        bob_pub_key = ecdh.Point(*map(int, bob_key_data.split()))

        shared_key = calculate_shared_key(A, bob_pub_key)
        print("Shared Key:", shared_key)

        round_keys = derive_round_keys(shared_key)
        communicate_with_bob(client_socket, round_keys)

if __name__ == "__main__":
    main()
