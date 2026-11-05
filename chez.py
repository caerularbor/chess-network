import re
import copy



class chessBoard:
    def __init__(self):
        
        #-----initialisation-----
        



        #move patterns
        self.pattern = r'''
            ^(?:                                     # Start of move
                O-O(?:-O)?[+#]?                           # Castling (O-O or O-O-O)
                |                                    # OR
                [KQBNR]?                             # Optional piece
                [a-h]?[1-8]?                         # Optional disambiguation
                x?                                   # Optional capture
                [a-h][1-8]                           # Destination square
                (?:=[QBNR])?                         # Optional promotion
                [+#]?                                # Optional check/checkmate
            )$                                       # End of move
        '''

        self.basicPattern = re.compile(self.pattern, re.VERBOSE)


        #board types for use 
        self.emptyBoard = [
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."]
        ]
        self.startingBoard = [
            ["r", "n", "b", "q", "k", "b", "n", "r"],
            ["p", "p", "p", "p", "p", "p", "p", "p"],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            [".", ".", ".", ".", ".", ".", ".", "."],
            ["P", "P", "P", "P", "P", "P", "P", "P"],
            ["R", "N", "B", "Q", "K", "B", "N", "R"]
        ]
        self.board = copy.deepcopy(self.startingBoard)




        #basic constants and important booleans
        self.turn= "white"
        self.lastMove = None
        self.enPassantTarget = None
        self.whiteKingMoved = False
        self.whiteKingRookMoved = False
        self.whiteQueenRookMoved = False
        self.blackKingMoved = False
        self.blackKingRookMoved = False
        self.blackQueenRookMoved = False


    def is_valid_chess_notation(self, move):
        pattern = r'^(?:[KQBNR]?[a-h]?[1-8]?x?[a-h][1-8](?:=[QBNR])?[+#]?|O-O(?:-O)?)$'
        return bool(self.basicPattern.fullmatch(move))

    def displayBoard(self, board):
        print(" " + " ".join([" ", "a", "b", "c", "d", "e", "f", "g", "h"]))
        print("  ┌─┬─┬─┬─┬─┬─┬─┬─┐")

        for i, row in enumerate(board):
            print(f"{8-i} |" + "|".join(row) + "|")
            if i < 7:
                print("  ├─┼─┼─┼─┼─┼─┼─┼─┤")
        
        print("  └─┴─┴─┴─┴─┴─┴─┴─┘")
    
#general helpers used throughout
    def legalCoords(self,row,col):
        return 0 <= row < 8 and 0 <= col < 8
    
    def resetBoard(self):
        self.board=copy.deepcopy(self.startingBoard)

        self.lastMove = None
        self.enPassantTarget = None
        self.turn = "white"

        self.whiteKingMoved = False
        self.whiteKingRookMoved = False
        self.whiteQueenRookMoved = False

        self.blackKingMoved = False
        self.blackKingRookMoved = False
        self.blackQueenRookMoved = False

    def isEnemy(self,piece,colour):
        if not piece or piece == ".":
            return False
    
        if colour == "white":
            return piece.islower()
        else:
            return piece.isupper()
    def squareToCoords(self,square):
        col = ord(square[0]) - ord('a')     #using ascii to convert the column letter to index
        row = 8 - int(square[1])
        return row,col

    def coordsToSquare(self,row,col):
        colLetter = chr(col + ord('a'))    #reversing squareToCoords
        rowNumber = str(8-row)
        return colLetter + rowNumber
#moving a piece
    #helpers
    def analyseMove(self,move):
        if not self.is_valid_chess_notation(move):
            return {"valid":False}
    
        if move.startswith("O-O"):
            castleMove = move.replace("+","").replace("#","")
    
            if castleMove == "O-O":
                return {
                    "valid": True,
                    "piece": "K",
                    "castle": "kingside",
                    "capture": False,
                    "promotion": None,
                    "check": "+" in move,
                    "checkmate": "#" in move,
                    "destination": None,
                    "disambiguation": ""
                }
    
            elif castleMove == "O-O-O":
                return {
                    "valid": True,
                    "piece": "K",
                    "castle": "queenside",
                    "capture": False,
                    "promotion": None,
                    "check": "+" in move,
                    "checkmate": "#" in move,
                    "destination": None,
                    "disambiguation": ""
                }
            
        piece = move[0] if move[0] in "KQBNR" else "P"
        capture = "x" in move
    
        promotion = None
        if "=" in move:
            promotion = move.split("=")[1][0]
    
        check = "+" in move
        checkmate = "#" in move
    
        destinationCheck = re.search(r'[a-h][1-8]',move)
        destination = destinationCheck.group() if destinationCheck else None
    
        #this bit separates out the disambiguation file/column
        temp = move
        if temp[0] in "KQBNR":
            temp = temp[1:]     #removing piece symbol
        if destination:
            temp = temp.replace(destination, '')
        temp = temp.replace('x','')     #removing square notation
        if '=' in temp:
            temp = temp.split('=')[0]     #removing promotion symbol
        temp = temp.replace('+','').replace('#','')        #removing check and mate symbols
        disambiguation = temp
    
        return {
            "valid": True,
            "piece": piece,
            "capture": capture,
            "promotion": promotion,
            "check": check,
            "checkmate": checkmate,
            "destination": destination,
            "disambiguation": disambiguation
        }
    
    
    def moveIsSafe(self,board,sourceRow,sourceCol,destRow,destCol,colour):
        piece = board[sourceRow][sourceCol]
        captured = board[destRow][destCol]

        if captured != "." and captured.lower() == "k":
            return False     #premature king capture check

        isPassant = (piece.lower() == "p" and captured == "." and abs(sourceCol-destCol) == 1 and self.enPassantTarget == self.coordsToSquare(destRow,destCol))
        passantCapturedRow = None
        passantCapturedCol = None
        passantCapturedPiece = None

        if isPassant:
            passantCapturedRow = destRow + 1 if colour == "white" else destRow - 1
            passantCapturedCol = destCol
            passantCapturedPiece = board[passantCapturedRow][passantCapturedCol]
            enemyPawn = "p" if colour == "white" else "P"

            if passantCapturedPiece != enemyPawn:
                return False

            board[passantCapturedRow][passantCapturedCol] = "."

        board[sourceRow][sourceCol] = "."
        board[destRow][destCol] = piece
            
        incheck = self.inCheck(board,colour)

        board[sourceRow][sourceCol] = piece
        board[destRow][destCol] = captured

        if isPassant:
            board[passantCapturedRow][passantCapturedCol] = passantCapturedPiece

        return not incheck

    def isLegalMove(self, board, move, colour):
        analysedMove = self.analyseMove(move)
        if not analysedMove['valid']:
            return False

        if analysedMove.get("castle"):
            side = analysedMove['castle']

            return self.canCastle(board,colour,side)

        if self.isEnPassant(board,move,colour):
            source = self.findPawnSource(board,analysedMove,colour)

            if not source:
                return False

            sourceRow,sourceCol = self.squareToCoords(source)
            destRow,destCol = self.squareToCoords(analysedMove['destination'])

            return self.moveIsSafe(board,sourceRow,sourceCol,destRow,destCol,colour)

        source = self.findSource(board,move,analysedMove,colour)

        if not source:
            return False

        destRow,destCol = self.squareToCoords(analysedMove['destination'])

        target = board[destRow][destCol]

        if analysedMove['capture']:
            if target == ".":
                return False
            if not self.isEnemy(target,colour):
                return False
        else:
            if target != ".":
                return False
            
        sourceRow,sourceCol = self.squareToCoords(source)
        legalMoves = self.allLegalMoves(board,colour)
        sourceSquare = self.coordsToSquare(sourceRow,sourceCol)
        destinationSquare = analysedMove['destination']

        promotion = analysedMove['promotion']
        for legalMove in legalMoves:

            if (legalMove['source'] == sourceSquare and legalMove['destination'] == destinationSquare and legalMove['promotion'] == promotion):
                return True

        return False

#square related finding
    def findPawnSource(self, board, analysedMove, colour):
        destRow, destCol = self.squareToCoords(analysedMove['destination'])
        pawnSymbol = "P" if colour == "white" else "p"
        direction = -1 if colour == "white" else 1
        startingRank = 6 if colour == "white" else 1
        candidates = []

        if analysedMove['capture']:
            sourceRow = destRow-direction

            if self.legalCoords(sourceRow, destCol):

                possibleCols = [destCol-1,destCol+1]

                if analysedMove['disambiguation']:
                    disambiguation = analysedMove['disambiguation']

                    if len(disambiguation) == 1 and disambiguation in "abcdefgh":
                        possibleCols = [ord(disambiguation) - ord('a')]
                    else:
                        return None

                for sourceCol in possibleCols:
                    if not self.legalCoords(sourceRow,sourceCol):
                        continue

                    if board[sourceRow][sourceCol] == pawnSymbol:
                        candidates.append((sourceRow,sourceCol))
            
        else:
            sourceRow = destRow - direction

            if self.legalCoords(sourceRow,destCol):
                if board[sourceRow][destCol] == pawnSymbol:
                    candidates.append((sourceRow,destCol))

            if destRow == (startingRank + 2 * direction):
                sourceRow = destRow - (2*direction)
                skippedRow = sourceRow + direction

                if (self.legalCoords(sourceRow,destCol) and board[sourceRow][destCol] == pawnSymbol and board[skippedRow][destCol] == "."):
                    candidates.append((sourceRow,destCol))

        if len(candidates) == 1:
            return self.coordsToSquare(*candidates[0])

        return None

    def findSource(self,board,move,analysedMove,colour):
    
            if analysedMove['piece'] == "P":
                return self.findPawnSource(board,analysedMove, colour)
    
            candidates = []

            for row in range(8):
                for col in range(8):

                    piece = board[row][col]

                    if piece.upper() != analysedMove['piece']:
                        continue

                    if colour == "white" and (not piece.isupper()):
                        continue
                    if colour == "black" and (not piece.islower()):
                        continue

                    square = self.coordsToSquare(row,col)

                    disambiguation = analysedMove['disambiguation']
                    if disambiguation:
                        if len(disambiguation) == 1:
                            if disambiguation not in square:
                                continue
                        else:
                            continue

                    if self.pieceCanMoveTo(board,row,col,*self.squareToCoords(analysedMove['destination']),piece,colour):
                        candidates.append(square)

            if len(candidates) == 1:
                return candidates[0]

            return None
        
    def getAllPiecePositions(self, board, piece):
        positions = []

        for row in range(8):
            for col in range(8):

                if board[row][col] == piece:
                    positions.append(self.coordsToSquare(row, col))

        return positions

    def getPieceAt(self, board, square):
        row, col = self.squareToCoords(square)

        return board[row][col]
    def getKingPos(self, board, piece):
        positions = self.getAllPiecePositions(board, piece)

        return positions[0] if positions else None
    
    def pieceCanMoveTo(self,board,row,col,destRow,destCol,piece,colour):
        if piece.lower() == "p":
            moves = self.pawnMoves(board,row,col,colour)

        elif piece.lower() == "n":
            moves = self.knightMoves(board,row,col,colour)

        elif piece.lower() == "b":
            moves = self.bishopMoves(board,row,col,colour)

        elif piece.lower() == "r":
            moves = self.rookMoves(board,row,col,colour)

        elif piece.lower() == "q":
            moves = self.queenMoves(board,row,col,colour)

        elif piece.lower() == "k":
            moves = self.kingMoves(board,row,col,colour)

        else:
            return False

        for move in moves:

            if move['destination'] == self.coordsToSquare(destRow,destCol):
                return True

        return False

    def ifPieceAttacksSquare(self,board,piece,square,target):
        row,col = self.squareToCoords(square)
        targetRow,targetCol = self.squareToCoords(target)
        pieceType = piece.lower()
        rowDif,colDif = targetRow-row,targetCol-col
        absRowDif,absColDif = abs(rowDif),abs(colDif)

#checking indexes or making pseudo legal moves to check for piece targets
        if pieceType == "n":
            return (absRowDif,absColDif) in ((1,2),(2,1))

        elif pieceType == "k":
            return max(absRowDif,absColDif) == 1

        elif pieceType == "p":
            direction = -1 if piece.isupper() else 1
            return (rowDif==direction and absColDif == 1)

        elif pieceType == "b":

            if absRowDif != absColDif:  #check if its a straight diagonal
                return False

            rowDirection = 1 if rowDif > 0 else -1
            colDirection = 1 if colDif > 0 else -1

            currentRow = row + rowDirection   #moving along the diagonal
            currentCol = col + colDirection

            while (currentRow,currentCol) != (targetRow,targetCol):

                if board[currentRow][currentCol] != ".":
                    return False

                currentRow += rowDirection   #continued movement
                currentCol += colDirection

            return True

        elif pieceType == "r":

            if row != targetRow and col != targetCol:   #checking if its a straight line
                return False

            if row == targetRow:   #moving along one direction, verticals by keeping row unchanged
                direction = 1 if targetCol > col else -1   
                currentCol = col + direction

                while currentCol != targetCol:

                    if board[row][currentCol] != ".":
                        return False

            else:   #moving along the rows by changing row
                direction = 1 if targetRow > row else -1
                currentRow = row + direction

                while currentRow != targetRow:

                    if board[currentRow][col] != ".":
                        return False

                    currentRow += direction

            return True

        elif pieceType == "q":
            diagonal = (absRowDif == absColDif and absRowDif != 0)
            straight = (row==targetRow or col == targetCol)

            if not diagonal and not straight:
                return False

            if diagonal:     #combining bishop and rook checks
                rowDirection = 1 if rowDif > 0 else -1
                colDirection = 1 if colDif > 0 else -1
                currentRow = row + rowDirection
                currentCol = col + colDirection

                while (currentRow,currentCol) != (targetRow,targetCol):

                    if board[currentRow][currentCol] != ".":
                        return False

                    currentRow += rowDirection
                    currentCol += colDirection

                return True

            if row == targetRow:
                direction = 1 if targetCol > col else -1
                currentCol = col + direction

                while currentCol != targetCol:

                    if board[row][currentCol] != ".":
                        return False

                    currentCol += direction

                return True

            direction = 1 if targetRow > row else -1
            currentRow = row + direction

            while currentRow != targetRow:

                if board[currentRow][col] != ".":
                    return False

                currentRow += direction

            return True

        return False
    def squareAttacked(self,board,row,col,colour):

        square = self.coordsToSquare(row,col)
        oppColour = "black" if colour == "white" else "white"

        for r in range(8):
            for c in range(8):

                piece = board[r][c]
                if piece == ".":
                    continue

                if oppColour == "white" and not piece.isupper():
                    continue
                if oppColour == "black" and not piece.islower():
                    continue

                pieceSquare = self.coordsToSquare(r,c)
                if self.ifPieceAttacksSquare(board,piece,pieceSquare,square):
                    return True

        return False
    
    #main moving function
    def makeMove(self, board, move, colour):
        if colour != self.turn:
            return False

        analysedMove = self.analyseMove(move)
        if not analysedMove['valid']:
            return False
        
        if analysedMove.get('castle'):
            result = self.castling(board, colour, analysedMove['castle'])

            if result:
                self.turn = "black" if self.turn == "white" else "white"

            return result

        if self.isEnPassant(board,move,colour):
            result = self.executeEnPassant(board,move,colour)

            if result:
                self.turn = "black" if self.turn == "white" else "white"

            return result

        if not self.isLegalMove(board,move,colour):
            return False


        source = self.findSource(board,move,analysedMove,colour)

        if not source:
            return False
    
        sourceRow, sourceCol = self.squareToCoords(source)
        destRow, destCol = self.squareToCoords(analysedMove['destination'])
        
        piece = board[sourceRow][sourceCol]
        target = board[destRow][destCol]
        if not self.pieceCanMoveTo(board,sourceRow,sourceCol,destRow,destCol,piece,colour):
            return False

        
        if analysedMove['capture']:
            if target == ".":
                return False
            if not self.isEnemy(target,colour):
                return False
            if target.lower() == "k":
                return False
        else:
            if target != ".":
                return False
        if not self.moveIsSafe(board,sourceRow,sourceCol,destRow,destCol,colour):
            return False
        
        if piece.lower() == "k":
            if colour == "white":
                self.whiteKingMoved = True
            else:
                self.blackKingMoved = True
        if piece.lower() == 'r':
            if colour == "white":
                if source == "h1":
                    self.whiteKingRookMoved = True
                elif source == "a1":
                    self.whiteQueenRookMoved = True
            else:
                if source == "h8":
                    self.blackKingRookMoved = True
                elif source == "a8":
                    self.blackQueenRookMoved = True

        if piece.lower() == "p":
            promotionRank = 0 if colour == "white" else 7
            if destRow == promotionRank and not analysedMove['promotion']:
                return False
            if destRow != promotionRank and analysedMove['promotion']:
                return False
            if destRow == promotionRank:
                if not analysedMove['promotion']:
                    return False
                
        board[destRow][destCol] = piece
        board[sourceRow][sourceCol] = "."
    
        if analysedMove['promotion']:
            promotionPiece = (analysedMove['promotion'] if colour == "white" else analysedMove['promotion'].lower())
            board[destRow][destCol] = promotionPiece

        self.lastMove = {
                        'piece': piece,
                        'source': source,
                        'destination': analysedMove['destination'],
                        'colour': colour,
                        'capture': analysedMove['capture'],
                        'promotion': analysedMove['promotion']
                            }
        

        if piece.lower() == "p" and abs(sourceRow - destRow) == 2:
            self.enPassantTarget = self.coordsToSquare((sourceRow + destRow) // 2, sourceCol)
        else:
            self.enPassantTarget = None

        self.turn = "black" if self.turn == "white" else "white"
        return True

#piece move lists
    def pawnMoves(self,board,row,col,colour):

        moves = []

        if colour == "white":
            direction = -1
            startingRank = 6
        else:
            direction = 1
            startingRank = 1


        newRow = row + direction

        if self.legalCoords(newRow,col):

            if board[newRow][col] == ".":

                moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,col),
                              'promotion':None,
                              'capture':False,
                              'enPassant': False,
                              'castling':None})

                if row == startingRank:  #allowing double pawn moves

                    doubleRow = row + (2*direction)

                    if (self.legalCoords(doubleRow,col) and board[doubleRow][col] == "."):

                        moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(doubleRow,col),
                              'promotion':None,
                              'capture':False,
                              'enPassant': False,
                              'castling':None})

        captureRow = row + direction

        if self.enPassantTarget is not None:   #normal captures

            targetRow,targetCol = self.squareToCoords(self.enPassantTarget)

            if targetRow == captureRow and abs(targetCol - col) == 1:

                moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.enPassantTarget,
                              'promotion':None,
                              'capture':True,
                              'enPassant': True,
                              'castling':None})

        if self.legalCoords(captureRow,col):

            for captureCol in (col-1,col+1):

                if not self.legalCoords(captureRow,captureCol):
                    continue

                target = board[captureRow][captureCol]

                if target != "." and self.isEnemy(target,colour):

                    if target.lower() != "k":

                        moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(captureRow,captureCol),
                              'promotion':None,
                              'capture':True,
                              'enPassant': False,
                              'castling':None})

        return moves

    def knightMoves(self,board,row,col,colour):
        moves = []
        offsets = [(2,1), (2,-1), (-2,1), (-2,-1), (1,2), (1,-2), (-1,2), (-1,-2)]

        for dr, dc in offsets:   #checking for each offset with unpacking

            newRow,newCol = row+dr,col+dc

            if self.legalCoords(newRow,newCol):

                target = board[newRow][newCol]
                if target == "." or (target != "." and self.isEnemy(target,colour)):

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':target != ".",
                              'enPassant': False,
                              'castling':None})
                
        return moves

    def bishopMoves(self,board,row,col,colour):
        moves = []
        offsets = [(1,1), (1,-1), (-1,1), (-1,-1)]  #also using unpacking

        for dr, dc in offsets:

            newRow,newCol = row + dr, col + dc
            while self.legalCoords(newRow,newCol):

                target = board[newRow][newCol]
                if target == ".":

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':False,
                              'enPassant': False,
                              'castling':None})

                elif self.isEnemy(target,colour):

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':True,
                              'enPassant': False,
                              'castling':None})
                    break   #stopping at an enemy piece since you cant move through
                else:
                    break

                newRow += dr   #moving along the diagonal
                newCol += dc

        return moves

    def rookMoves(self,board,row,col,colour):
        moves = []
        offsets = [(1,0), (-1,0), (0,1), (0,-1)]  #rook offsets

        for dr,dc in offsets:

            newRow, newCol = row + dr, col + dc
            while self.legalCoords(newRow,newCol):

                target = board[newRow][newCol]
                if target == ".":

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':False,
                              'enPassant': False,
                              'castling':None})

                elif self.isEnemy(target,colour):

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':True,
                              'enPassant': False,
                              'castling':None})
                    break  #same as above stopping at an enemy

                else:
                    break

                newRow += dr  #linear movement on the rows and verticals
                newCol += dc

        return moves

    def queenMoves(self,board,row,col,colour):
        moves = []
        offsets = [(1,0), (-1,0), (0,1), (0,-1), (1,1), (1,-1), (-1,1), (-1,-1)] #combined offsets of rook and bishop

        for dr, dc in offsets:

            newRow, newCol = row + dr, col + dc
            while self.legalCoords(newRow,newCol):

                target = board[newRow][newCol]
                if target == ".":

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':False,
                              'enPassant': False,
                              'castling':None})

                elif self.isEnemy(target,colour):

                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':True,
                              'enPassant': False,
                              'castling':None})
                    break #still stopping at a capture
                
                else:
                    break

                newRow += dr
                newCol += dc

        return moves

    def kingMoves(self, board, row, col, colour):
        moves = []

        offsets = [(1, 0),(-1, 0),(0, 1),(0, -1),(1, 1),(1, -1),(-1, 1),(-1, -1)]  #king offsets

        for dr, dc in offsets:
            newRow = row + dr
            newCol = col + dc

            if not self.legalCoords(newRow, newCol):
                continue

            target = board[newRow][newCol]

        
            if target == ".":
                moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':False,
                              'enPassant': False,
                              'castling':None})

        
            elif self.isEnemy(target, colour):
           
                if target.lower() != "k":
                    moves.append({'source':self.coordsToSquare(row,col),
                              'destination' : self.coordsToSquare(newRow,newCol),
                              'promotion':None,
                              'capture':True,
                              'enPassant': False,
                              'castling':None})

        return moves

#comprehensive move list for checking mate/stalemate
    def allLegalMoves(self,board,colour):

        allMoves = []
       
        for row in range(8):
            for col in range(8):

                piece = board[row][col]

                if piece == ".":
                    continue

                if (colour == "white" and piece.isupper()) or (colour == "black" and piece.islower()):
                    if piece.lower() == "p":
                        moves = self.pawnMoves(board,row,col,colour)
                        
                    elif piece.lower() == "n":
                        moves = self.knightMoves(board,row,col,colour)

                    elif piece.lower() == "b":
                        moves = self.bishopMoves(board,row,col,colour)

                    elif piece.lower() == "r":
                        moves = self.rookMoves(board,row,col,colour)

                    elif piece.lower() == "q":
                        moves = self.queenMoves(board,row,col,colour)

                    elif piece.lower() == "k":
                        moves = self.kingMoves(board,row,col,colour)

                    else:
                        continue

                    for move in moves:
                        destRow,destCol = self.squareToCoords(move['destination'])

                        if not self.moveIsSafe(board,row,col,destRow,destCol,colour):
                            continue

                        if piece.lower() == "p":

                            promotionRank = 0 if colour == "white" else 7

                            if destRow == promotionRank:

                                for promotionPiece in "QRBN":

                                    allMoves.append({"source":self.coordsToSquare(row,col),
                                         "destination":self.coordsToSquare(destRow,destCol),
                                         "promotion":promotionPiece,
                                         "capture":board[destRow][destCol] != ".",
                                         "enPassant":False,
                                         "castling":None})
                                continue

                        allMoves.append({"source":self.coordsToSquare(row,col),
                                         "destination":self.coordsToSquare(destRow,destCol),
                                         "promotion":None,
                                         "capture":board[destRow][destCol] != ".",
                                         "enPassant":False,
                                         "castling":None})

        row = 7 if colour == "white" else 0        

        if self.canCastle(board,colour,"kingside"):

            allMoves.append({"source":self.coordsToSquare(row,4),
                                         "destination":self.coordsToSquare(row,6),
                                         "promotion":None,
                                         "capture":False,
                                         "enPassant":False,
                                         "castling":"kingside"})

        if self.canCastle(board,colour,"queenside"):

            allMoves.append({"source":self.coordsToSquare(row,4),
                                         "destination":self.coordsToSquare(row,2),
                                         "promotion":None,
                                         "capture":False,
                                         "enPassant":False,
                                         "castling":"queenside"})
        return allMoves 
        
    
    
    
#castling check helpers
    def kingHasntMoved(self,board,colour):
        if colour == "white":
            return self.getPieceAt(board,"e1") == "K" and not self.whiteKingMoved

        else:
            return self.getPieceAt(board,"e8") == "k" and not self.blackKingMoved

    def rookHasntMoved(self,board,colour,side):
        if side == "kingside":

            if colour == "white":
                return self.getPieceAt(board, "h1") == "R" and not self.whiteKingRookMoved
            else:
                return self.getPieceAt(board, "h8") == "r" and not self.blackKingRookMoved

        else:  # queenside

            if colour == "white":
                return self.getPieceAt(board, "a1") == "R" and not self.whiteQueenRookMoved
            else:
                return self.getPieceAt(board, "a8") == "r" and not self.blackQueenRookMoved

    def kingRookPathClear(self,board,colour,side):
        if side == "kingside":

            if colour == "white":
                return board[7][5] == "." and board[7][6] == "."
            else:
                return board[0][5] == "." and board[0][6] == "."
            
        if side == "queenside":

            if colour == "white":
                return board[7][1] == "." and board[7][2] == "." and board[7][3] == "."
            else:
                return board[0][1] == "." and board[0][2] == "." and board[0][3] == "."
        return False

    def canCastle(self,board,colour,side):    #compiled castle check
        if not self.kingHasntMoved(board,colour):
            return False

        if not self.rookHasntMoved(board,colour,side):
            return False

        if not self.kingRookPathClear(board,colour,side):
            return False

        if self.inCheck(board,colour):
            return False

        if colour == "white":
            row = 7

        else:
            row = 0

        if side == "kingside":
            if self.squareAttacked(board,row,5,colour):
                return False
            if self.squareAttacked(board,row,6,colour):
                return False

        else:
            if self.squareAttacked(board,row,3,colour):
                return False
            if self.squareAttacked(board,row,2,colour):
                return False

        return True


#executing castling
    def executeCastling(self,board,colour,side):

        row = 7 if colour == "white" else 0
        king = "K" if colour == "white" else "k"

        if board[row][4] != king:
            return False

        rook = "R" if colour == "white" else "r"
        rookCol = 7 if side == "kingside" else 0

        if board[row][rookCol] != rook:
            return False

        if side == "kingside":
            board[row][6] = board[row][4]
            board[row][4] = "."
            board[row][5] = board[row][7]
            board[row][7] = "." 

        else:
            board[row][2] = board[row][4]
            board[row][4] = "."
            board[row][3] = board[row][0]
            board[row][0] = "."

        if colour == "white":
            self.whiteKingMoved = True

            if side == "kingside":
                self.whiteKingRookMoved = True
            else:
                self.whiteQueenRookMoved = True

        else:
            self.blackKingMoved = True

            if side == "kingside":
                self.blackKingRookMoved = True
            else:
                self.blackQueenRookMoved = True

        self.lastMove = {
            'piece': 'K' if colour == "white" else 'k',
            'source':self.coordsToSquare(row,4),
            'destination': self.coordsToSquare(row,6 if side == "kingside" else 2),
            'colour':colour,
            'capture':False,
            'promotion':None,
            'castling':side
        } 

        self.enPassantTarget = None
        return True

    def castling(self,board,colour,side):    #simple compiled castle function
        if not self.canCastle(board,colour,side):
            return False

        return self.executeCastling(board,colour,side)


#google en passant

    def isEnPassant(self,board,move,colour):  #en passant check
        analysedMove = self.analyseMove(move)
    
        if not analysedMove['piece'] == "P":
            return False

        if not analysedMove['capture'] == True:
            return False

        destRow, destCol = self.squareToCoords(analysedMove['destination'])
        source = self.findPawnSource(board,analysedMove,colour)

        if not source:
            return False

        sourceRow,sourceCol = self.squareToCoords(source)

        if abs(sourceCol-destCol) != 1:
            return False

        if not ((destRow == 5 and colour == "black") or (destRow == 2 and colour == "white")):
            return False

        if not self.enPassantTarget:
            return False

        if not analysedMove['destination'] == self.enPassantTarget:
            return False

        return True

#executing en passant 
    def executeEnPassant(self,board,move,colour):  
        analysedMove = self.analyseMove(move)
        if not analysedMove['valid']:
            return False
        
        source = self.findPawnSource(board,analysedMove,colour)
        if not source:
            return False
        
        sourceRow,sourceCol = self.squareToCoords(source)
        destRow,destCol = self.squareToCoords(analysedMove['destination'])

        if colour == "white":
            capturedRow = destRow + 1
            enemyPawn = "p"

        else:
            capturedRow = destRow - 1
            enemyPawn = "P"

        if self.enPassantTarget != analysedMove['destination']:
            return False

        capturedCol = destCol

        if board[destRow][destCol] != ".":
            return False
        if board[capturedRow][capturedCol] != enemyPawn:
            return False
        piece = board[sourceRow][sourceCol]
        

        capturedPiece = board[capturedRow][capturedCol]
        destPiece = board[destRow][destCol]

        board[sourceRow][sourceCol] = "."
        board[capturedRow][capturedCol] = "."
        board[destRow][destCol] = piece

        if self.inCheck(board,colour):
            board[sourceRow][sourceCol] = piece
            board[capturedRow][capturedCol] = capturedPiece
            board[destRow][destCol] = destPiece

            return False
        
        
        self.enPassantTarget = None
        self.lastMove = {
            'piece':piece,
            'source':source,
            'destination':analysedMove['destination'],
            'colour': colour,
            'capture': True,
            'promotion':None,
            'enPassant' : True

        }
        
        return True
    
    
#game logic

    
                        
                        
        
    def inCheck(self,board,colour):
        kingPos = self.getKingPos(board,"K" if colour == "white" else "k")
        if not kingPos:
            return False

        kingRow, kingCol = self.squareToCoords(kingPos)
        return self.squareAttacked(board,kingRow,kingCol,colour)
    
    def isMate(self,board,colour):
        if self.inCheck(board,colour) is True and len(self.allLegalMoves(board,colour)) == 0:
            return True
        return False
    
    def isStalemate(self,board,colour):
        if self.inCheck(board,colour) is False and len(self.allLegalMoves(board,colour)) == 0:
            return True
        return False






board = chessBoard()
input('''       chez
        ovo
    to start game press enter''')
board.resetBoard()
board.displayBoard(board.board)
positions = []
while True: 
    print(f"{board.turn}'s turn to move")
    print(" ")
    
    print('''   to move type the 
    standard chess notation 
    for your move owo
    castling and en passant 
    are supported''')
    print(" ")
    while True:
        move = input("enter move plz >w<    ")
        
        if not board.is_valid_chess_notation(move):
            print("enter a valid chess move plz")
            continue
        if not board.isLegalMove(board.board,move,board.turn):
            print("enter a legal chess move plz")
            continue
        break

    board.makeMove(board.board,move,board.turn)
    positions.append(copy.deepcopy(board))
    board.displayBoard(board.board)

    if board.isMate(board.board,board.turn):
        print(f"{board.turn} is mated :(")
        print("ggs")
        break
    if board.isStalemate(board.board,board.turn):
        print("stalemate you guys are lucky lol")
        break






#>w<