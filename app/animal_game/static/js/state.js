// state.js
// =============================
// Global State Variables
// =============================

export const state = {
    possibleCards: [],
    cardsFound: [],
    opened: [],
    numStars: 3,
    numMatch: 0,
    numMoves: 0,
    turns: 1,
    isMatch: false,
    isRobotTurn: false,                     // To know if it's robot's turn 
    robotSubject: "",
    hasProvidedWrongCard: false,            // use for SC and NC conditions

    // When agent/robot helps
    hintCards: [],
    timeHint: 3500,
    speechFinished: false,

    // Game timer 
    seconds: 0,
    minutes: 0,
    t: null,

    // Pair timer
    myMinutes: 0,
    mySeconds: 0,
    myT: null,

    // reset cards                          // All cards names of new board
    consecutiveUnsuccessfulAttempts: 0,     // moves
    boardChanging: false,

    // shuffle settings
    shuffleTrials: 0,

    // for communication with server
    socket_address: ''
};

export const numCards = () => state.possibleCards.length;
export const maxMatch = () => state.possibleCards.length / 2;

// For communication with Server
export const sessionId = document.getElementById('session-data-id').dataset.sessionId;
export const language = document.getElementById('session-data').dataset.sessionLan;
export const shuffleDiv = document.getElementById('session-data-shuffle');
export const shuffleBoard = shuffleDiv.getAttribute('data-session-shuffle') == 'True'

// Read shuffle trial count from DOM (fallback to 0 if missing)
const sessionTrialsElement = document.getElementById('session-data-trials');
export const shuffleTrials = parseInt(sessionTrialsElement?.getAttribute('data-session-trials') ?? '0', 10) || 0;

// Mirror value on the shared state object so other modules can access it via state.shuffleTrials
state.shuffleTrials = shuffleTrials;

export let id_player = sessionId
export const url = ''
