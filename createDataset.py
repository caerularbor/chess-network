import loadingPGN
from config import PGN_PATH

if __name__ == "__main__":
    loadingPGN.shardDatabase(
    inputPath=PGN_PATH,
    output="chess_dataset",
    gamesPerSection=5000,
    sectionPerShard=20,
    validationFraction=0.1,
    seed=42
)