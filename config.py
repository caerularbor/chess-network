PGN_PATH = r"C:\Users\beatr\Downloads\lichess_db_standard_rated_2026-09.pgn.zst"
MAX_GAMES = 10000
DATASET_DIR = "chess_dataset"

# Minimum number of shard sections to read per split. Raising this spreads
# the sample across more of the database instead of draining a few sections.
MIN_SECTIONS = 20

MIN_RATING = 1800
REQUIRE_BOTH_PLAYERS = True

EXCLUDED_FIRST_MOVES = {
    "a3", "c3", "d3", "e3", "f3", "h3",
    "a4", "b4", "f4", "g4", "h4",
    "Na3", "Nh3", "Nc3"
}
FILTER_OPENINGS = True
KEEP_OPENINGS = {
    #transposing moves from excluded moves
    #can be added here
}