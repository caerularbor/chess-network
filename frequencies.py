
import chess
import chess.pgn
import zstandard
import io
import json

PGN_PATH = r"C:\Users\beatr\Downloads\lichess_db_standard_rated_2026-09.pgn.zst"

# Set this to the number of games actually used for training.
MAX_GAMES = 2000


def normalizePosition(board):
    return " ".join(board.fen().split()[:4])


def frequencyDataBase():
    frequency = {}

    gamesProcessed = 0

    print("Opening Lichess database...")

    with open(PGN_PATH, "rb") as compressedFile:
        decompressor = zstandard.ZstdDecompressor()

        with decompressor.stream_reader(compressedFile) as reader:
            textStream = io.TextIOWrapper(reader, encoding="utf-8")

            while gamesProcessed < MAX_GAMES:
                game = chess.pgn.read_game(textStream)

                if game is None:
                    break

                board = game.board()

                for move in game.mainline_moves():
                    position = normalizePosition(board)
                    uci = move.uci()

                    if position not in frequency:
                        frequency[position] = {}

                    if uci not in frequency[position]:
                        frequency[position][uci] = 0

                    frequency[position][uci] += 1

                    board.push(move)

                gamesProcessed += 1

                if gamesProcessed % 100 == 0:
                    print(
                        f"Processed {gamesProcessed}/{MAX_GAMES} games"
                    )

    print(f"Finished processing {gamesProcessed} games.")

    return frequency


def saveFrequencyDataBase(frequency, filename="frequency.json"):
    with open(filename, "w") as file:
        json.dump(frequency, file)


def loadFrequencyDataBase(filename="frequency.json"):
    with open(filename, "r") as file:
        return json.load(file)


def frequencyBaseline(frequency, board):
    position = normalizePosition(board)

    if position not in frequency:
        return None

    moves = frequency[position]

    if not moves:
        return None

    return max(moves, key=moves.get)


def getMoveFrequencies(frequency, board):
    position = normalizePosition(board)

    if position not in frequency:
        return {}

    moves = frequency[position]
    total = sum(moves.values())

    return {
        uci: count / total
        for uci, count in moves.items()
    }


if __name__ == "__main__":
    print("Building frequency database...")

    frequency = frequencyDataBase()

    saveFrequencyDataBase(frequency)

    print(f"Positions indexed: {len(frequency)}")
    print("Frequency database saved!")
