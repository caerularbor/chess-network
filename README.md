# chess-network

A NumPy-based neural network trained on human chess games to predict opening moves and model human playing preferences.

Unlike traditional chess engines that aim to find the objectively strongest move, this project explores how machine learning can reproduce patterns in human chess decision-making.

## Overview

The project uses supervised learning to train a neural network on real chess games from the Lichess open source database at here: https://database.lichess.org/

Given a chess position, the network predicts a probability distribution over possible moves, learning which moves humans are more likely to choose in similar positions.

The goal is to model human playing behaviour rather than simply imitate an engine.

## Model Architecture

The network is implemented from scratch using Python and NumPy.

**Architecture:**

`768 → 128 → 4608`

| Layer | Dimensions | Description |
|---|---:|---|
| Input | 768 | Flattened 12-channel chessboard encoding |
| Hidden | 128 | Learns patterns in chess positions |
| Output | 4608 | Predicts probabilities for possible moves |

The output layer supports both standard moves and pawn promotions.

## How It Works

1. **Data Collection** – Uses human chess games from the Lichess rated games database.
2. **Data Processing** – Extracts chess positions and their corresponding moves from PGN files.
3. **Board Encoding** – Represents each position using 12 binary channels, one for each piece type and colour.
4. **Training** – Trains the neural network using supervised learning and backpropagation, with the Adam optimiser.
5. **Move Prediction** – Converts network outputs into probabilities and filters out illegal moves before selecting a move.

## Technologies

- Python 3
- NumPy
- python-chess
- Lichess game database (PGN)

## Project Goals

- Explore neural networks through a practical chess application.
- Learn human opening preferences from real-world game data.
- Investigate how effectively a relatively simple neural network can model chess decision-making.
- Compare human move preferences with traditional engine evaluations.

## Future Development

- Stockfish integration for position evaluation.
- Improved model generalisation and training performance.
- Interactive chess interface.
- Natural language explanations of predicted moves.

## Getting Started

Clone the repository:

```bash
git clone https://github.com/YOUR_USERNAME/chess-network.git
cd chess-network
```

Install dependencies:

```bash
pip install numpy python-chess
```

Further instructions for obtaining the dataset, configuring training, and running the model will be added as the project develops.

## Disclaimer

This project is an experimental machine learning implementation, not a replacement for traditional chess engines. Its primary objective is to model human move selection rather than calculate optimal chess play.
