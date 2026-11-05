import chess
import chess.pgn

from network import moveToIndex, indexToMove

with open("gameTest.pgn", "r", encoding="utf-8") as pgn_file:
    game = chess.pgn.read_game(pgn_file)

if game is None:
    raise ValueError("No game found in pipelineTest.pgn")

original_board = game.board()
replay_board = game.board()

moves_checked = 0
promotions_checked = 0

for move in game.mainline_moves():
    moves_checked += 1

    # The original move must be legal.
    if move not in original_board.legal_moves:
        raise ValueError(
            f"Original move {moves_checked} is illegal: {move}"
        )

    # Encode the move as a neural-network output index.
    index = moveToIndex(move)

    # Decode it back into a chess.Move.
    decoded_move = indexToMove(index)

    if decoded_move != move:
        raise AssertionError(
            f"Move {moves_checked} failed round-trip: "
            f"{move} -> {index} -> {decoded_move}"
        )

    # The decoded move must also be legal.
    if decoded_move not in replay_board.legal_moves:
        raise AssertionError(
            f"Decoded move {moves_checked} is illegal: "
            f"{decoded_move}"
        )

    if move.promotion is not None:
        promotions_checked += 1

    original_board.push(move)
    replay_board.push(decoded_move)

# Both boards should reach the same final position.
assert original_board.fen() == replay_board.fen()

print("PIPELINE TEST PASSED")
print(f"Moves checked: {moves_checked}")
print(f"Promotions checked: {promotions_checked}")
print("Final positions match!")
