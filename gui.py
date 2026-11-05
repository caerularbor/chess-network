from pathlib import Path
import random

import chess
import numpy as np

MODEL_PATH = Path(__file__).resolve().with_name("chez_model.json")


def load_model():
    from network import ChessNN, layer

    model = ChessNN([0] * 768)
    model.initLayers(layer([0] * 768, 128))
    model.initLayers(layer([0] * 128, 4608, activation=False))
    model.load(str(MODEL_PATH))

    return model


def display_board(board):
    print("\n    a   b   c   d   e   f   g   h")
    print("  +" + "---+" * 8)

    for rank in range(7, -1, -1):
        cells = []

        for file in range(8):
            piece = board.piece_at(chess.square(file, rank))
            cells.append(piece.symbol() if piece else " ")

        print(f"{rank + 1} | " + " | ".join(cells) + f" | {rank + 1}")
        print("  +" + "---+" * 8)

    print("    a   b   c   d   e   f   g   h")


def display_move_history(board):
    if not board.move_stack:
        print("\n move history: (no moves yet)")
        return

    replay = chess.Board()
    moves = []

    for move in board.move_stack:
        if replay.turn == chess.WHITE:
            moves.append(f"{replay.fullmove_number}.")

        moves.append(replay.san(move))
        replay.push(move)

    print("\n move history:")
    print(" ".join(moves))


def get_model_move(board, model):
    from network import encodingBoard, flattening, moveToIndex

    legal_moves = list(board.legal_moves)

    if not legal_moves:
        return None, 0.0, []

    inputs = np.asarray(
        [flattening(encodingBoard(board))],
        dtype=np.float32
    )

    hidden, _ = model.forwardHidden(inputs)
    output_layer = model.layers[-1]

    indices = [moveToIndex(move) for move in legal_moves]

    logits = (
        output_layer.weights[indices] @ hidden[0]
        + output_layer.biases[indices]
    )

    weights = np.exp(logits - np.max(logits))
    probabilities = weights / weights.sum()

    # Sort all legal moves by probability.
    top_indices = np.argsort(probabilities)[::-1][:5]

    top_moves = [
        (board.san(legal_moves[i]), float(probabilities[i]))
        for i in top_indices
    ]

    # Always choose the highest-probability move.
    best_index = top_indices[0]

    return legal_moves[best_index], float(probabilities[best_index]), top_moves


def get_human_move(board):
    while True:
        raw = input("\n ur move (SAN, or help/moves/quit): ").strip()
        command = raw.lower()

        if command == "quit":
            return "quit"

        if command == "help":
            print("enter moves in SAN plz  e4 O-O exd5")
            print("commands: help, moves, quit")
            continue

        if command == "moves":
            display_move_history(board)
            continue

        try:
            return board.parse_san(raw)

        except ValueError:
            print("invalid :( try again plz")


def show_result(board, human_color):
    outcome = board.outcome(claim_draw=True)

    if outcome is None:
        return

    print("\n" + "=" * 38)
    print("              GAME OVER")
    print("=" * 38)

    print(
        f"result: {outcome.result()} — "
        f"{outcome.termination.name.replace('_', ' ').title()}"
    )

    if outcome.winner is None:
        print("draw :)")
    elif outcome.winner == human_color:
        print("you won :)")
    else:
        print("chez ai won :(")


def play_session(model):
    board = chess.Board()

    human_color = random.choice([chess.WHITE, chess.BLACK])
    human_side = "White" if human_color == chess.WHITE else "Black"

    print(f"\n chess time youre {human_side}")

    while not board.is_game_over(claim_draw=True):
        display_board(board)

        if board.turn == human_color:
            move = get_human_move(board)

            if move == "quit":
                print("session ended :/")
                return "menu"

            san = board.san(move)
            board.push(move)

            print(f"user played: {san}")

        else:
            try:
                move, probability, top_moves = get_model_move(board, model)

            except Exception as exc:
                print(f"model prediction failed :( {exc}")
                return "menu"

            if move is None:
                break

            print("\n chez ai predictions:")
            print("-" * 32)

            for rank, (san, prob) in enumerate(top_moves, 1):
                print(f"{rank}. {san:<8} {prob:>7.2%}")

            san = board.san(move)
            board.push(move)

            print(f"\nchez ai played: {san}")
            print(f"selected prob: {probability:.2%}")

    display_board(board)
    display_move_history(board)
    show_result(board, human_color)

    return "finished"


def display_menu():
    print("\n" + "=" * 38)
    print("       NEURAL CHESS OPENING TRAINER")
    print("=" * 38)
    print("\n1. start new session")
    print("2. quit\n")

    return input("select plz ").strip()


def finished_menu():
    print("\n" + "=" * 38)
    print("          SESSION FINISHED")
    print("=" * 38)
    print("\n1. start new session")
    print("2. return to main menu")
    print("3. quit\n")

    return input("select plz").strip()


def main():
    try:
        model = load_model()
        print(f"Loaded trained model: {MODEL_PATH.name}")

    except Exception as exc:
        print("\n couldnt load the neural network model :(")
        print(f"Details: {exc}")
        print("check your model is present and dependencies are installed")
        return

    while True:
        choice = display_menu()

        if choice == "1":
            while True:
                state = play_session(model)

                if state == "menu":
                    break

                next_choice = finished_menu()

                if next_choice == "1":
                    continue

                if next_choice in ("2", ""):
                    break

                if next_choice == "3":
                    print("X X XXX")
                    return

                print("select 1, 2, or 3.")

        elif choice == "2":
            print("X X XXX")
            return

        else:
            print("select 1 or 2.")


if __name__ == "__main__":
    main()
