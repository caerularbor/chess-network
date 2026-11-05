'''
v1.0.0
Added GUI for actual use
Connected functions to gui
First official publish
v0.8.0
Added game filters for rating and opening moves
to optimise training data 
Added analyseDatabase.py for future use
and analysing opening information for
pgn databases


v0.7.0
Added in database sharding to optimise PGN loading
for large files
Added random sampling for training games 
to counter overfitting


v0.6.0
Added in KL and JS divergence metrics
to analyse models
Compared 2000/5000 game models 
on same validation games


v0.5.2
Added weight decay to counter overfitting
First medium scale training run (2000 games)


v0.5.1
Successful training on 500 games
Overfitting issue persists
Fixed validation games with random seed


v0.5.0
Successful reconstuction of a .pgn 
with no illegal moves
Streamlined .pgn loading from lichess database
with zstandard and python-chess
Successful loading and encoding of 100 games
First successful small training run 
Added promotion encoding

v0.4.0
Added numpy and Adam for optimisation
'''