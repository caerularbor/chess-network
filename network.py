import chess
import chess.pgn
import loadingPGN
import copy
import random
import math
import json
import numpy as np
def ReLU(x):
    return np.maximum(0,x)
def ReLUDerived(x):
    return(np.asarray(x) > 0).astype(float)


def addVector(vector1,vector2):
    outputs = []

    for value1, value2 in zip(vector1,vector2):
        outputs.append(value1 + value2)

    return outputs

def softmax(logits):
    logits = np.asarray(logits, dtype = np.float64)
    maxi = max(logits)
    exp = np.exp(logits - maxi)
    
    

    total = sum(exp)

    prob = []

    for value in exp:
        prob.append(value/total)

    return prob

def crossEntropy(probs,target):
    return -math.log(probs[target])

def klDivergence(P, Q):
    P = np.asarray(P, dtype = np.float64)
    Q = np.asarray(Q, dtype = np.float64)

    mask = P > 0

    if np.any(Q[mask] == 0):
        return float("inf")
    return np.sum(
        P[mask] * np.log2(P[mask] / Q[mask])
    )
def jsDivergence(P, Q):
    M = (P + Q) / 2

    return (
        klDivergence(P,M)
        + klDivergence(Q, M)
    ) / 2


class layer:
    def __init__(self,inputs,numberOfNeurons, activation = True):
        self.inputs = np.asarray(inputs, dtype = float)
        self.weights = np.array([])
        self.biases = np.array([])
        
        self.numberOfNeurons = numberOfNeurons
        self.activation = activation
        
        self.weightGrads = np.array([])
        self.biasGrads = np.array([])

        self.outputGrads = np.array([])
        self.rawOutputs = np.array([])
        self.outputs = np.array([])

        


    def initWeights(self):
        inputSize = len(self.inputs)

        self.weights = np.random.randn(
            self.numberOfNeurons,inputSize
            ) * np.sqrt(2 / inputSize)

        self.biases = np.zeros(self.numberOfNeurons)

        self.weightGrads = np.zeros_like(self.weights)
        self.biasGrads = np.zeros_like(self.biases)

        self.outputGrads = np.zeros(self.numberOfNeurons)
        self.rawOutputs = np.zeros(self.numberOfNeurons)
        self.outputs = np.zeros(self.numberOfNeurons)
        
        self.adamMWeights = np.zeros_like(self.weights)
        self.adamVWeights = np.zeros_like(self.weights)
        
        self.adamMBiases = np.zeros_like(self.biases)
        self.adamVBiases = np.zeros_like(self.biases)
        
        self.adamT = 0
    
    def calcMatrixGradients(self):
        self.weightGrads += np.outer(
            self.outputGrads,
            self.inputs)

        self.biasGrads += self.outputGrads

        return self.weightGrads, self.biasGrads
    
    def calculateHiddenGradients(self,nextLayer):
        weights = np.array(nextLayer.weights)
        nextGrads = np.array(nextLayer.outputGrads)

        self.outputGrads = (weights.T @ nextGrads) * ReLUDerived(self.rawOutputs)
        

        return self.outputGrads

    
    def getOutputs(self):
        return self.outputs
    
    def updateInputs(self,inputs):
        self.inputs = inputs
        self.outputs = self.calcOutputs()
    
    def calcOutputs(self):
        
        calculatedOutput = self.weights @ self.inputs + self.biases
       
        self.rawOutputs = calculatedOutput.copy()
        if self.activation:
            calculatedOutput = ReLU(calculatedOutput)
        
        self.outputs = calculatedOutput
        return self.outputs

    def calcOutputGrads(self,target,probs):
        self.outputGrads = np.asarray(probs).copy()

        self.outputGrads[target] -= 1
    
    def getParameters(self):
        return {"weights":self.weights.tolist(),
                "biases":self.biases.tolist(),
                "activation": self.activation}

    def loadParameters(self,parameters):

        self.weights = np.asarray(parameters["weights"], dtype = float)

        self.biases = np.asarray(parameters["biases"], dtype = float)
        self.activation = parameters["activation"]

        self.weightGrads = np.zeros_like(self.weights)
        self.biasGrads = np.zeros_like(self.biases)

        self.adamMWeights = np.zeros_like(self.weights)
        self.adamVWeights = np.zeros_like(self.weights)

        self.adamMBiases = np.zeros_like(self.biases)
        self.adamVBiases = np.zeros_like(self.biases)

        self.adamT = 0
    def adamStep(self, learningRate = 0.001, weightDecay = 5e-4):
        beta1 = 0.9
        beta2 = 0.999
        epsilon = 1e-8

        self.adamT += 1

        for parameter, grad, m, v in [
            (self.weights,self.weightGrads,
             self.adamMWeights,self.adamVWeights),
             (self.biases,self.biasGrads,
              self.adamMBiases,self.adamVBiases)
        ]:
            #first moment
            m *= beta1
            m += (1 - beta1) * grad

            #second moment
            v *= beta2
            v += (1 - beta2) * grad ** 2

            #bias correction
            mHat = m / (1 - beta1**self.adamT)
            vHat = v / (1 - beta2**self.adamT)

            
            parameter -= learningRate * mHat / (np.sqrt(vHat) + epsilon)
        self.weights -= learningRate * weightDecay * self.weights

            

def squareToCoords(square):
    square = chess.square_name(square)
    col = ord(square[0]) - ord('a')     #using ascii to convert the column letter to index
    row = 8 - int(square[1])
    return row,col


def encodingBoard(board):
    channels = {
            "P": 0,
            "N": 1,
            "B": 2,
            "R": 3,
            "Q": 4,
            "K": 5,
            "p": 6,
            "n": 7,
            "b": 8,
            "r": 9,
            "q": 10,
            "k": 11
        }
                
    emptyBoard = [
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0],
        [0,0,0,0,0,0,0,0]
        ]
    
        
    encodedBoards = [copy.deepcopy(emptyBoard) for _ in range(12)]

    for square in chess.SQUARES:
        piece = board.piece_at(square)
            
        if piece:
            pieceType = str(piece)
            channel = channels[pieceType]
            pieceBoard = encodedBoards[channel]
            row,col = squareToCoords(square)
            pieceBoard[row][col] = 1
    return encodedBoards

def encoding(board,Move):
    encoded = encodingBoard(board)


    if Move is None:
        return encoded
    
    move = chess.Move.from_uci(Move)
    board.push(move)
    return encodingBoard(board)
    
def legalMoveProbs(board, logits): 
    legalMoves = list(board.legal_moves)

    indices = [moveToIndex(move) for move in legalMoves]

    legalLogits = logits[indices]
    probs = softmax(legalLogits)

    return list(zip(legalMoves,probs))

def legalSoftmax(board, legalLogits, target):
    legalMoves = list(board.legal_moves)

    indices = [moveToIndex(move) for move in legalMoves]

    if target not in indices:
        raise ValueError("target move not legal")

  

    shifted = legalLogits - np.max(legalLogits)
    expLogits = np.exp(shifted)
    probs = expLogits / np.sum(expLogits)

    targetIndex = indices.index(target)

    loss = -np.log(max(probs[targetIndex], 1e-12))
    delta = probs.copy()
    delta[targetIndex] -= 1

    return indices, probs, delta, targetIndex, loss
def loadPGN(pgn):
    games = []
    with open(pgn,"r",encoding = "utf-8") as file:
        while True:
            game = chess.pgn.read_game(file)

            if game is None:
                break

            games.append(game)
    return games            

def encodeDataBase(games):
    encoded = []
    gamesRead = 0

    for game in games:
        temp = loadingPGN.parseGame(game)
        board = game.board()
        gamesRead += 1
        for move in temp['moves']:
            encodedPos = flattening(encodingBoard(board))
            chessMove = chess.Move.from_uci(move["uci"])

            if chessMove not in board.legal_moves:
                raise ValueError(
                    f"illegal move in game {gamesRead}"
                    f"{move['uci']} at {board.fen()}"
                )
            encoded.append((
                encodedPos, 
                moveToIndex(chessMove),
                board.fen()
            ))

            
            board.push(chessMove)
    print(f"games encoded:{gamesRead}")
    return encoded

def sampleGames(games, sampleSize, seed = 42):
    rng = random.Random(seed)

    sample = []
    for i, game in enumerate(games):
        if i < sampleSize:
            sample.append(game)

        else:
            j = rng.randrange(i + 1)
            if j < sampleSize:
                sample[j] = game

    return sample


def flattening(encodedBoards):
    flat = []

    for channel in encodedBoards:
        for row in channel:
            for val in row:
                flat.append(val)
    return flat

PROMOTION_BASE = 4096

promotionOffset = {
            chess.KNIGHT: 0,
            chess.BISHOP: 1,
            chess.ROOK: 2,
            chess.QUEEN: 3
        }

offsetPromotion = {
    offset:piece for piece,offset in promotionOffset.items()
}
def moveToIndex(move):
    if move.promotion is None:
        return move.from_square * 64 + move.to_square


    colour = 0 if chess.square_rank(move.from_square) == 6 else 1
    origFile = chess.square_file(move.from_square)
    destFile = chess.square_file(move.to_square)

    pairIndex = (colour * 8 + origFile) * 8 + destFile

    return (
        PROMOTION_BASE 
        + pairIndex * 4
        + promotionOffset[move.promotion]
    )



def indexToMove(index):
    if not 0 <= index < 4608:
        raise ValueError(f"invalid move index:{index}")

    if index < PROMOTION_BASE:
        return chess.Move(index // 64, index % 64)

    promotionIndex = index - PROMOTION_BASE

    promotionOffset = promotionIndex % 4
    pairIndex = promotionIndex // 4

    destFile = pairIndex % 8
    colourOrigFile = pairIndex // 8

    origFile = colourOrigFile % 8
    colour = colourOrigFile // 8

    origRank = 6 if colour == 0 else 1
    destRank = 7 if colour == 0 else 0

    return chess.Move(
        chess.square(origFile, origRank),
        chess.square(destFile,destRank),
        promotion = offsetPromotion[promotionOffset]
    )

def loss(pred,targets):
    total = 0

    for prediction,target in zip(pred,targets):
        total += (prediction - target) ** 2
    return total


class ChessNN:
    def __init__(self,inputs):
        self.layers = []
        self.inputs = inputs
        self.trainingMode = False
        self.dropoutP = 0.0
        self.dropoutMask = None
    
    def initLayers(self,layer):
        self.layers.append(layer)

    def forward(self):
        currentInputs = self.inputs
        for layer in self.layers:
            layer.updateInputs(currentInputs)
            currentInputs = layer.getOutputs()
        return currentInputs

    def save(self,filename):
        parameters = []

        for layer in self.layers:
            parameters.append(layer.getParameters())

        with open(filename,"w") as file:
            json.dump(parameters,file)

    def load(self,filename):
        with open(filename,"r") as file:
            parameters = json.load(file)

        if len(parameters) != len(self.layers):
            raise ValueError("model layer mismatch lmao")

        for layer, savedParameters in zip(self.layers, parameters):
            layer.loadParameters(savedParameters)

    def evaluateValues(self,evaluatedData, maxPositions = None):
        totalLoss = 0.0
        correct = 0
        seen = 0

        if maxPositions is not None:
            evaluatedData = evaluatedData[:maxPositions]

        for inputs, target, fen in evaluatedData:
            board = chess.Board(fen)

            X = np.asarray([inputs], dtype = np.float32)
            hidden, _ = self.forwardHidden(X)

            outputLayer = self.layers[-1]

            legalMoves = list(board.legal_moves)
            if not legalMoves:
                continue
            indices = [moveToIndex(move) for move in legalMoves]

            if target not in indices:
                raise ValueError(
                f"target move {target} is illegal at {fen}")

            legalWeights = outputLayer.weights[indices]
            legalBiases = outputLayer.biases[indices]

            logits = legalWeights @ hidden[0] + legalBiases
            probs = np.asarray(softmax(logits)) 

            targetIndex = indices.index(target)
            totalLoss -= math.log(
                max(probs[targetIndex], 1e-12)
            )       

            predictionIndex = int(np.argmax(logits))

            if predictionIndex == targetIndex:
                correct += 1

            seen += 1

        if seen == 0:
            raise ValueError("no positions provided :(")


        return totalLoss / seen, correct / seen
    def forwardHidden(self,X):
        A = X
        caches = []

        for layer in self.layers[:-1]:
            layerInputs = A
            Z = A @ layer.weights.T + layer.biases
            A = np.maximum(0, Z) if layer.activation else Z

            caches.append((layerInputs,Z))

        if self.trainingMode and self.dropoutP > 0.0:
            keep = (np.random.rand(*A.shape) > self.dropoutP).astype(np.float32)
            self.dropoutMask = keep / (1.0 - self.dropoutP)
            A = A * self.dropoutMask
        else:
            self.dropoutMask = None

        return A, caches
    
    
    
    def forwardBatch(self,X):
        A = X
        caches = []

        for layer in self.layers:
            layerInputs = A

            Z = A @ layer.weights.T + layer.biases

            if layer.activation:
                A = np.maximum(0,Z)

            else:
                A = Z

            caches.append((layerInputs,Z))
    
        return A, caches

    def training(self,trainingData,learningRate = 0.001, epochs = 3,batchSize = 128,
                 weightDecay = 5e-4, dropout = 0.0):
        self.trainingMode = True
        self.dropoutP = dropout

        for epoch in range(epochs):
            totalLoss = 0.0
            random.shuffle(trainingData)
            seen = 0


            for start in range(0, len(trainingData), batchSize):
                batch = trainingData[start:start + batchSize]

                X = np.asarray([item[0] for item in batch],
                               dtype = np.float32)
                targets = np.asarray([item[1] for item in batch],
                                     dtype = np.int64)
                boards = [chess.Board(item[2]) for item in batch]

                batchCount = len(batch)

                hidden, caches = self.forwardHidden(X)

                outputLayer = self.layers[-1]



                outputLayer.weightGrads = np.zeros_like(outputLayer.weights)
                outputLayer.biasGrads = np.zeros_like(outputLayer.biases)

                hiddenDelta = np.zeros_like(hidden)

                losses = []
                for i in range(batchCount):
                    board = boards[i]

                    legalMoves = list(board.legal_moves)
                    indices = [
                        moveToIndex(move) 
                        for move in legalMoves
                               ]

                    legalWeights = outputLayer.weights[indices]
                    legalBiases = outputLayer.biases[indices]

                    legalLogits = legalWeights @ hidden[i] + legalBiases


                    _, probs, legalDelta, targetIndex, loss = legalSoftmax(
                        board,legalLogits, targets[i]
                    )
                    losses.append(loss)

                    #grads for only legal move neurons
                    outputLayer.weightGrads[indices] += np.outer(
                        legalDelta, hidden[i]
                    )
                    outputLayer.biasGrads[indices] += legalDelta
                    #hidden layer grads
                    hiddenDelta[i] = legalWeights.T @ legalDelta

                outputLayer.weightGrads /= batchCount
                outputLayer.biasGrads /= batchCount
                hiddenDelta /= batchCount

                if self.dropoutMask is not None:
                    hiddenDelta *= self.dropoutMask

                batchLoss = np.mean(losses)
                totalLoss += batchLoss * batchCount
                seen += batchCount

                for i in range(len(self.layers) - 2, -1, -1):
                    layer = self.layers[i] 
                    layerInputs, Z = caches[i]

                    if layer.activation:
                        deltaZ = hiddenDelta * (Z > 0)
                    else:
                        deltaZ = hiddenDelta
                    #grads for hidden layer
                    layer.weightGrads = deltaZ.T @ layerInputs

                    #bias grad across all positions
                    layer.biasGrads = np.sum(
                        deltaZ,axis = 0
                    )
                    if i > 0:
                        hiddenDelta = deltaZ @ layer.weights
                        
                for layer in self.layers:
                    layer.adamStep(learningRate, weightDecay)

            averageLoss = totalLoss / seen
            print(f"epoch{epoch+1} / {epochs},"
                  f"loss: {averageLoss:.4f}")

        self.trainingMode = False
        self.dropoutP = 0.0
        self.dropoutMask = None


                                           
                
            