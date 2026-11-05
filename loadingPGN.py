import chess
import chess.pgn
import zstandard as zstd
import io
import random
import json
import os
from config import*
import math
def parseGame(game):
    opening = game.headers.get("Opening")
    variation = game.headers.get("Variation")
    board = game.board()
    moves = []

    for move in game.mainline_moves():
        san = board.san(move)
        moves.append({"san":san,
                      "uci":move.uci(),
                      "fen":board.fen()})
        board.push(move)
    return{
            "opening":opening,
            "variation":variation,
            "moves":moves
        }
def loadDatabase(db):
    pgns = []
    with open(db,"r") as pgn:
        while True:
            game = chess.pgn.read_game(pgn)
            if game is None:
                break
            pgns.append(game)
    return pgns

def readPGNGames(path, maxGames=None):
    """Read PGN games from a compressed .pgn.zst file."""

    with open(path, "rb") as compressedFile:
        decompressor = zstd.ZstdDecompressor()

        with decompressor.stream_reader(compressedFile) as reader:
            with io.TextIOWrapper(
                reader,
                encoding="utf-8",
                errors="replace"
            ) as pgnFile:

                gamesRead = 0

                while maxGames is None or gamesRead < maxGames:
                    game = chess.pgn.read_game(pgnFile)

                    if game is None:
                        break

                    gamesRead += 1
                    yield game

def isValidGame(game):
    headers = game.headers

    # --------------------------------------------------------
    # RATING FILTER
    # --------------------------------------------------------

    try:
        whiteElo = int(headers.get("WhiteElo", 0))
        blackElo = int(headers.get("BlackElo", 0))
    except (ValueError, TypeError):
        return False, "rating"

    if REQUIRE_BOTH_PLAYERS:
        if whiteElo < MIN_RATING or blackElo < MIN_RATING:
            return False, "rating"
    else:
        if max(whiteElo, blackElo) < MIN_RATING:
            return False, "rating"

    # --------------------------------------------------------
    # OPENING FILTER
    # --------------------------------------------------------

    if FILTER_OPENINGS:

        board = game.board()
        firstMove = next(iter(game.mainline_moves()), None)

        if firstMove is None:
            return False, "opening"

        # Only filter White's first move.
        if board.turn == chess.WHITE:

            firstSAN = board.san(firstMove)
            opening = headers.get("Opening", "")

            if (
                firstSAN in EXCLUDED_FIRST_MOVES
                and opening not in KEEP_OPENINGS
            ):
                return False, "opening"

    return True, None
def readRandomGames(
        datasetDir,
        maxGames,
        split="train",
        sectionsToRead=None,
        seed=None
):
    if maxGames <= 0:
        return []

    if split not in ("train", "validation"):
        raise ValueError(f"invalid dataset split: {split}")

    manifestPath = os.path.join(
        datasetDir, "manifest.json"
    )

    with open(manifestPath, "r", encoding="utf-8") as file:
        manifest = json.load(file)

    sections = [
        section for section in manifest["sections"]
        if section["split"] == split
    ]

    if not sections:
        raise ValueError(f"no sections found for {split}")

    rng = random.Random(seed)

    averageSize = sum(
        s["games"] for s in sections
    ) / len(sections)

    requiredSections = max(
        MIN_SECTIONS,
        math.ceil(maxGames / averageSize * 3)
    )

    if sectionsToRead is not None:
        requiredSections = max(
            requiredSections, sectionsToRead
        )

    requiredSections = min(
        requiredSections, len(sections)
    )

    rankedSections = sorted(
        sections,
        key=lambda s: rng.random() ** (1 / s["games"]),
        reverse=True
    )

    selectedSections = rankedSections[:requiredSections]

    print(f"reading {len(selectedSections)} sections")

    selected = []

    totalScanned = 0
    totalValid = 0

    rejectedRating = 0
    rejectedOpening = 0
    rejectedInvalid = 0

    # --------------------------------------------------------
    # RESERVOIR SAMPLING
    # --------------------------------------------------------

    def processGame(lines):
        nonlocal totalScanned, totalValid
        nonlocal rejectedRating, rejectedOpening
        nonlocal rejectedInvalid

        if not lines:
            return

        totalScanned += 1

        rawGame = "".join(lines)

        try:
            game = chess.pgn.read_game(
                io.StringIO(rawGame)
            )

            if game is None:
                rejectedInvalid += 1

                if rejectedInvalid <= 5:
                    print("PGN PARSING RETURNED NONE:")
                    print(rawGame[:300])

                return

            valid, reason = isValidGame(game)

            if not valid:
                if reason == "rating":
                    rejectedRating += 1
                elif reason == "opening":
                    rejectedOpening += 1
                return

        except Exception as e:
            rejectedInvalid += 1

            if rejectedInvalid <= 5:
                print("INVALID GAME ERROR:", repr(e))
                print(rawGame[:300])

            return

        totalValid += 1

        if len(selected) < maxGames:
            selected.append(rawGame)

        else:
            index = rng.randrange(totalValid)

            if index < maxGames:
                selected[index] = rawGame

    # --------------------------------------------------------
    # STREAMING
    # --------------------------------------------------------

    for sectionIndex, section in enumerate(selectedSections, 1):

        path = os.path.join(
            datasetDir, section["path"]
        )

        currentGame = []

        with open(path, "rb") as compressedFile:

            decompressor = zstd.ZstdDecompressor()

            with decompressor.stream_reader(
                compressedFile
            ) as reader:

                with io.TextIOWrapper(
                    reader,
                    encoding="utf-8",
                    errors="replace"
                ) as pgnFile:

                    for line in pgnFile:

                        if line.startswith("[Event ") and currentGame:
                            processGame(currentGame)
                            currentGame = [line]

                        elif currentGame or line.strip():
                            currentGame.append(line)

                    processGame(currentGame)

        print(
            f"section {sectionIndex}/{len(selectedSections)} | "
            f"valid: {totalValid:,}"
        )

    # --------------------------------------------------------
    # REPORT
    # --------------------------------------------------------

    print("\n" + "=" * 50)
    print("FILTER REPORT")
    print("=" * 50)

    print(f"Games scanned:       {totalScanned:,}")
    print(f"Eligible games:      {totalValid:,}")
    print(f"Rejected by rating:  {rejectedRating:,}")
    print(f"Rejected by opening: {rejectedOpening:,}")
    print(f"Invalid games:       {rejectedInvalid:,}")
    print(f"Games selected:      {len(selected):,}")

    if totalValid < maxGames:
        print(
            f"WARNING: Only found {totalValid:,} "
            f"eligible games (requested {maxGames:,})."
        )

    # --------------------------------------------------------
    # PARSE SELECTED GAMES
    # --------------------------------------------------------

    rng.shuffle(selected)

    games = []

    for rawGame in selected:

        game = chess.pgn.read_game(
            io.StringIO(rawGame)
        )

        if game is not None:
            games.append(game)

    print(f"\ngames parsed: {len(games):,}")

    return games
def shardDatabase(
        inputPath, output,
        gamesPerSection, sectionPerShard,
        validationFraction, seed = 42
):
    manifestPath = os.path.join(output, "manifest.json")

    if os.path.exists(manifestPath):
        raise FileExistsError(
            "dataset exists :( use a new output directory"
        )
    os.makedirs(output, exist_ok = True)

    rng = random.Random(seed)
    compressor = zstd.ZstdCompressor(level=3)

    total = 0
    sectionIndex = 0
    sectionGames = 0

    writer = None
    outputFile = None
    currentEntry = None

    sections = []
    currentGame = []

    def openSection():
        nonlocal writer, outputFile, currentEntry

        shardIndex = sectionIndex // sectionPerShard
        localIndex = sectionIndex % sectionPerShard

        split = (
            "validation" if rng.random() < validationFraction
            else "train"
        )

        relativePath = os.path.join(
            split, 
            f"shard_{shardIndex:04d}",
            f"section_{localIndex:03d}.pgn.zst"
        )

        fullPath = os.path.join(output, relativePath)

        os.makedirs(os.path.dirname(fullPath), exist_ok = True)

        outputFile = open(fullPath, "wb")

        writer = compressor.stream_writer(
            outputFile, closefd = False
        )

        currentEntry = {
            "path": relativePath,
            "split": split,
            "shard": shardIndex,
            "section": localIndex,
            "games": 0
        }
    def closeSection():
        nonlocal writer, outputFile
        nonlocal currentEntry, sectionIndex, sectionGames

        if writer is None:
            return

        writer.close()
        outputFile.close()

        sections.append(currentEntry)

        writer = None
        outputFile = None
        currentEntry = None

        sectionIndex += 1
        sectionGames = 0

    def writeGame(lines):
        nonlocal total, sectionGames

        if not lines:
            return

        if writer is None:
            openSection()

        writer.write(b"".join(lines))

        total += 1
        sectionGames += 1

        currentEntry["games"] = sectionGames

        if sectionGames >= gamesPerSection:
            closeSection()

        if total % 100000 == 0:
            print(f"analysed {total:,} games")

    with open(inputPath, "rb") as compressedFile:
        decompressor = zstd.ZstdDecompressor()

        with decompressor.stream_reader(
            compressedFile
        ) as reader:
            with io.BufferedReader(reader) as bufferedReader:


                while True:
                    line = bufferedReader.readline()

                    if not line: 
                        break

                    if line.startswith(b"[Event ") and currentGame:
                        writeGame(currentGame)
                        currentGame = [line]

                    elif currentGame or line.strip():

                        currentGame.append(line)

                writeGame(currentGame)

    closeSection()

    manifest = {
        "totalGames": total,
        "gamesPerSection": gamesPerSection,
        "sectionPerShard": sectionPerShard,
        "validationFraction" : validationFraction,
        "seed": seed,
        "sections": sections


    }
    with open(manifestPath, "w", encoding = "utf-8") as file:
        json.dump(manifest, file, indent = 2)

    print("finished sharding :D")
    print(f"total games:{total,}")
    print(f"total sections {len(sections):,}")
    print(f"training sections:"
          f"{sum(s['split'] == 'train' for s in sections)}")
    print(f"validation sections:"
          f"{sum(s['split'] == 'validation' for s in sections)}")



        