import socket
import threading
import pickle

# Estado inicial do jogo
GRID_SIZE = 4  # Define o tamanho do grid (4x4 para linhas e 3x3 para caixas)
game_state = {
    "horizontal_lines": [[0] * (GRID_SIZE) for _ in range(GRID_SIZE + 1)],  # Linhas horizontais
    "vertical_lines": [[0] * (GRID_SIZE + 1) for _ in range(GRID_SIZE)],    # Linhas verticais
    "boxes": [[None] * GRID_SIZE for _ in range(GRID_SIZE)],  # Propriedade das caixas (None, 'player1', 'player2')
    "turn": "player1",
    "scores": {"player1": 0, "player2": 0}
}

# Configurações do servidor
HOST = '0.0.0.0'
PORT = 65432

# Lista de clientes conectados
clients = {}
player_turns = ["player1", "player2"]

def check_for_completed_boxes(x, y, player):
    completed_box = False
    # Checa ao redor das linhas horizontais e verticais para identificar caixas completadas

    # Verifica a caixa acima da linha horizontal
    if y < GRID_SIZE:
        if all([
            game_state["horizontal_lines"][y][x],
            game_state["horizontal_lines"][y + 1][x],
            game_state["vertical_lines"][x][y],
            game_state["vertical_lines"][x + 1][y] if x + 1 < GRID_SIZE + 1 else 0  # Verifica se x + 1 está dentro dos limites
        ]):
            game_state["boxes"][y][x] = player
            game_state["scores"][player] += 1
            completed_box = True

    # Verifica a caixa abaixo da linha horizontal (se y for maior que 0)
    if y > 0:
        if all([
            game_state["horizontal_lines"][y - 1][x],
            game_state["horizontal_lines"][y][x],
            game_state["vertical_lines"][x][y - 1],
            game_state["vertical_lines"][x + 1][y - 1] if x + 1 < GRID_SIZE + 1 else 0  # Verifica se x + 1 está dentro dos limites
        ]):
            game_state["boxes"][y - 1][x] = player
            game_state["scores"][player] += 1
            completed_box = True

    return completed_box


def handle_client(conn, player_id):
    clients[player_id] = conn
    conn.send(pickle.dumps(game_state))

    while True:
        try:
            data = conn.recv(1024)
            if not data:
                break

            move = pickle.loads(data)
            x, y, orientation = move['x'], move['y'], move['orientation']

            if game_state["turn"] == player_id:
                completed_box = False

                # Corrige a atualização da linha com base na orientação
                if orientation == "horizontal":
                    if y < len(game_state["horizontal_lines"]) and x < len(game_state["horizontal_lines"][y]):
                        if game_state["horizontal_lines"][y][x] == 0:
                            game_state["horizontal_lines"][y][x] = 1
                            completed_box = check_for_completed_boxes(x, y, player_id)
                elif orientation == "vertical":
                    if y < len(game_state["vertical_lines"]) and x < len(game_state["vertical_lines"][y]):
                        if game_state["vertical_lines"][y][x] == 0:
                            game_state["vertical_lines"][y][x] = 1
                            completed_box = check_for_completed_boxes(x, y, player_id)

                if not completed_box:
                    game_state["turn"] = "player2" if game_state["turn"] == "player1" else "player1"

                for client in clients.values():
                    client.send(pickle.dumps(game_state))
            else:
                conn.send(pickle.dumps({"error": "Não é seu turno ou movimento inválido"}))

        except ConnectionResetError:
            break
        except IndexError:
            conn.send(pickle.dumps({"error": "Coordenadas inválidas"}))

    del clients[player_id]
    conn.close()



# Inicia o servidor
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
    server.bind((HOST, PORT))
    server.listen(1)
    print("Servidor iniciado, aguardando jogadores...")

    player_count = 0
    while True:
        conn, addr = server.accept()
        player_id = player_turns[player_count % 2]
        threading.Thread(target=handle_client, args=(conn, player_id)).start()
        player_count += 1
