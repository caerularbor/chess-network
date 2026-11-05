
import chess.pgn
import zstandard as zstd
import io
import os
import json
import csv
import math
from collections import Counter
from config import DATASET_DIR


# ============================================================
# CONFIG
# ============================================================

DATASET = os.path.abspath(DATASET_DIR)

OUTPUT_DIR = os.path.join(DATASET, "analysis")
os.makedirs(OUTPUT_DIR, exist_ok=True)

CHECKPOINT_PATH = os.path.join(
    OUTPUT_DIR, "checkpoint.jsonl"
)

CSV_PATH = os.path.join(
    OUTPUT_DIR, "section_statistics.csv"
)

# False = much faster, headers only
# True = parse all moves to calculate game length
ANALYSE_GAME_LENGTH = False

# Print progress every N games within a section
PROGRESS_INTERVAL = 10000

# ============================================================
# HELPERS
# ============================================================

def getYear(headers):

    date = headers.get(
        "UTCDate",
        headers.get("Date", "")
    )

    try:
        return int(date[:4])
    except (ValueError, TypeError):
        return None


def getRatings(headers):

    total = 0
    count = 0

    for colour in ("White", "Black"):

        try:
            rating = int(
                headers.get(colour + "Elo", "")
            )

            if rating > 0:
                total += rating
                count += 1

        except (ValueError, TypeError):
            pass

    return total, count


def getOpening(headers):

    return (
        headers.get("Opening")
        or headers.get("ECO")
        or "Unknown"
    )


def entropy(counter):

    total = sum(counter.values())

    if total == 0:
        return 0.0

    return -sum(
        (count / total) * math.log2(count / total)
        for count in counter.values()
    )


def emptyStats():

    return {
        "games": 0,

        "openings": Counter(),
        "results": Counter(),
        "years": Counter(),

        "rating_sum": 0,
        "rating_count": 0,

        "length_sum": 0,
        "length_count": 0,
    }


# ============================================================
# SECTION ANALYSIS
# ============================================================

def analyseSection(path):

    stats = emptyStats()

    with open(path, "rb") as compressed:

        decompressor = zstd.ZstdDecompressor()

        with decompressor.stream_reader(
            compressed
        ) as reader:

            with io.TextIOWrapper(
                reader,
                encoding="utf-8",
                errors="replace"
            ) as pgn:

                while True:

                    if ANALYSE_GAME_LENGTH:
                        game = chess.pgn.read_game(pgn)

                        if game is None:
                            break

                        headers = game.headers

                        stats["length_sum"] += sum(
                            1 for _ in game.mainline_moves()
                        )

                        stats["length_count"] += 1

                    else:
                        headers = chess.pgn.read_headers(pgn)

                        if headers is None:
                            break

                    stats["games"] += 1

                    stats["openings"][
                        getOpening(headers)
                    ] += 1

                    result = headers.get(
                        "Result", "Unknown"
                    )

                    stats["results"][result] += 1

                    year = getYear(headers)

                    if year is not None:
                        stats["years"][year] += 1

                    ratingSum, ratingCount = getRatings(
                        headers
                    )

                    stats["rating_sum"] += ratingSum
                    stats["rating_count"] += ratingCount

                    if (
                        stats["games"] % PROGRESS_INTERVAL == 0
                    ):
                        print(
                            f"    Processed "
                            f"{stats['games']:,} games"
                        )

    return stats


# ============================================================
# SERIALIZATION
# ============================================================

def serializeStats(stats):

    return {
        "games": stats["games"],

        "openings": dict(stats["openings"]),
        "results": dict(stats["results"]),
        "years": dict(stats["years"]),

        "rating_sum": stats["rating_sum"],
        "rating_count": stats["rating_count"],

        "length_sum": stats["length_sum"],
        "length_count": stats["length_count"],
    }


def deserializeStats(data):

    return {
        "games": data["games"],

        "openings": Counter(data["openings"]),
        "results": Counter(data["results"]),
        "years": Counter(data["years"]),

        "rating_sum": data["rating_sum"],
        "rating_count": data["rating_count"],

        "length_sum": data["length_sum"],
        "length_count": data["length_count"],
    }


# ============================================================
# AGGREGATION
# ============================================================

def mergeStats(target, source):

    target["games"] += source["games"]

    for key in ("openings", "results", "years"):
        target[key].update(source[key])

    for key in (
        "rating_sum",
        "rating_count",
        "length_sum",
        "length_count"
    ):
        target[key] += source[key]


# ============================================================
# CHECKPOINT / RESUME
# ============================================================

def metadata(manifest):

    return {
        "dataset": DATASET,
        "section_count": len(manifest["sections"]),
        "analyse_game_length": ANALYSE_GAME_LENGTH,
        "version": 1,
    }



def loadCheckpoint(manifest):

    meta = metadata(manifest)

    aggregate = {
        "train": emptyStats(),
        "validation": emptyStats()
    }

    completed = set()

    if not os.path.exists(CHECKPOINT_PATH):

        with open(
            CHECKPOINT_PATH, "w", encoding="utf-8"
        ) as file:
            file.write(json.dumps({"meta": meta}) + "\n")

        return aggregate, completed

    with open(
        CHECKPOINT_PATH, "r+", encoding="utf-8"
    ) as file:

        firstLine = file.readline()

        try:
            header = json.loads(firstLine)
        except json.JSONDecodeError:
            raise ValueError("Invalid checkpoint header.")

        if header.get("meta") != meta:
            raise ValueError(
                "Checkpoint does not match dataset/config. "
                "Use a new checkpoint."
            )

        validEnd = file.tell()

        while True:

            line = file.readline()

            if not line:
                break

            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print("Repairing incomplete checkpoint...")
                file.seek(validEnd)
                file.truncate()
                break

            path = record["path"]

            if path not in completed:

                split = record["split"]

                if split not in aggregate:
                    raise ValueError("Invalid checkpoint split.")

                stats = deserializeStats(record["stats"])

                mergeStats(aggregate[split], stats)
                completed.add(path)

            validEnd = file.tell()

    return aggregate, completed



def saveCheckpoint(path, split, stats):

    record = {
        "path": path,
        "split": split,
        "stats": serializeStats(stats)
    }

    with open(
        CHECKPOINT_PATH, "a", encoding="utf-8"
    ) as file:

        file.write(json.dumps(record) + "\n")
        file.flush()


# ============================================================
# DATASET ANALYSIS
# ============================================================

def analyseDataset():

    manifestPath = os.path.join(
        DATASET, "manifest.json"
    )

    with open(
        manifestPath, "r", encoding="utf-8"
    ) as file:
        manifest = json.load(file)

    sections = manifest["sections"]

    print("=" * 60)
    print("DATABASE ANALYSIS")
    print("=" * 60)

    print("Dataset:", DATASET)
    print("Manifest games:", f"{manifest['totalGames']:,}")
    print("Sections:", f"{len(sections):,}")

    aggregate, completed = loadCheckpoint(manifest)

    print("Already completed:", f"{len(completed):,}")
    print(
        "Remaining sections:",
        f"{len(sections) - len(completed):,}"
    )

    for index, section in enumerate(sections, 1):

        relativePath = section["path"]
        split = section["split"]

        if relativePath in completed:
            continue

        path = os.path.join(DATASET, relativePath)

        if not os.path.exists(path):
            raise FileNotFoundError(path)

        print(
            f"\n[{index}/{len(sections)}] "
            f"{relativePath} ({split})"
        )

        stats = analyseSection(path)

        mergeStats(aggregate[split], stats)

        saveCheckpoint(
            relativePath,
            split,
            stats
        )

        completed.add(relativePath)

        print(
            f"  Games: {stats['games']:,}"
        )

    print("\nAll sections processed.")

    return aggregate, manifest


# ============================================================
# REPORT
# ============================================================

def printReport(name, data):

    print("\n" + "=" * 60)
    print(name.upper())
    print("=" * 60)

    games = data["games"]

    print("Games:", f"{games:,}")

    if data["rating_count"]:

        print(
            "Average player rating:",
            round(
                data["rating_sum"] / data["rating_count"],
                2
            )
        )

    if data["length_count"]:

        print(
            "Average game length:",
            round(
                data["length_sum"] / data["length_count"],
                2
            ),
            "plies"
        )

    print(
        "Opening entropy:",
        round(entropy(data["openings"]), 4)
    )

    print(
        "Unique openings:",
        len(data["openings"])
    )

    print("\nTop 20 openings:")

    for opening, count in data["openings"].most_common(20):

        print(
            f"{opening[:40]:40} "
            f"{count:12,} "
            f"{count / games * 100:8.3f}%"
        )

    print("\nResults:")

    for result, count in data["results"].most_common():

        print(
            f"{result:12} "
            f"{count:12,} "
            f"{count / games * 100:8.3f}%"
        )

    print("\nYears:")

    for year, count in sorted(data["years"].items()):

        print(
            f"{year}: {count:,} "
            f"({count / games * 100:.2f}%)"
        )


# ============================================================
# DISTRIBUTION COMPARISON
# ============================================================

def compareOpenings(train, validation):

    print("\n" + "=" * 60)
    print("OPENING DISTRIBUTION DIFFERENCES")
    print("=" * 60)

    allOpenings = (
        set(train["openings"]) |
        set(validation["openings"])
    )

    differences = []

    for opening in allOpenings:

        trainPct = (
            train["openings"][opening]
            / train["games"] * 100
        )

        valPct = (
            validation["openings"][opening]
            / validation["games"] * 100
        )

        differences.append((
            abs(trainPct - valPct),
            opening,
            trainPct,
            valPct
        ))

    differences.sort(reverse=True)

    for difference, opening, trainPct, valPct in differences[:30]:

        print(
            f"{opening[:35]:35} "
            f"Train: {trainPct:7.3f}% "
            f"Val: {valPct:7.3f}% "
            f"Diff: {difference:7.3f}pp"
        )


# ============================================================
# SECTION CSV
# ============================================================

def createSectionCSV():

    with open(
        CHECKPOINT_PATH, "r", encoding="utf-8"
    ) as checkpoint:

        next(checkpoint)

        with open(
            CSV_PATH, "w", newline="", encoding="utf-8"
        ) as output:

            fields = [
                "path",
                "split",
                "games",
                "avg_rating",
                "avg_length",
                "opening_entropy",
                "unique_openings",
                "most_common_opening",
            ]

            writer = csv.DictWriter(
                output,
                fieldnames=fields
            )

            writer.writeheader()

            for line in checkpoint:

                record = json.loads(line)
                stats = deserializeStats(record["stats"])

                mostCommon = stats["openings"].most_common(1)

                writer.writerow({
                    "path": record["path"],
                    "split": record["split"],
                    "games": stats["games"],

                    "avg_rating": (
                        stats["rating_sum"] /
                        stats["rating_count"]
                        if stats["rating_count"] else 0
                    ),

                    "avg_length": (
                        stats["length_sum"] /
                        stats["length_count"]
                        if stats["length_count"] else 0
                    ),

                    "opening_entropy": entropy(
                        stats["openings"]
                    ),

                    "unique_openings": len(
                        stats["openings"]
                    ),

                    "most_common_opening": (
                        mostCommon[0][0]
                        if mostCommon else "Unknown"
                    )
                })


# ============================================================
# MAIN
# ============================================================

def main():

    aggregate, manifest = analyseDataset()

    printReport(
        "Training",
        aggregate["train"]
    )

    printReport(
        "Validation",
        aggregate["validation"]
    )

    compareOpenings(
        aggregate["train"],
        aggregate["validation"]
    )

    createSectionCSV()

    print("\n" + "=" * 60)
    print("ANALYSIS COMPLETE")
    print("=" * 60)

    print("Checkpoint:", CHECKPOINT_PATH)
    print("Section CSV:", CSV_PATH)


if __name__ == "__main__":
    main()
