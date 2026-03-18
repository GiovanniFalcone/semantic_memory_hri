// main.js
// =============================
// Entry point of the game
// =============================

import { id_player, state } from './state.js';
import { runTimer, myRunTimer, resetTimer, myResetTimer } from './timers.js';
import { checkFirstVisit, setupUnloadEvents, setupExitButton, changeLanguage } from './utils.js';
import { hintReceivedByRobot, moveReceivedByRobot } from './robot.js';
import { printStars, printMoves, printTrials } from './score.js';
import { createCards } from './gameplay.js';

// Wait until the DOM is loaded
document.addEventListener('DOMContentLoaded', () => {

    // Check if it's first visit
    checkFirstVisit();

    // Setup global events
    setupUnloadEvents();
    setupExitButton();

    // Start the game
    initializeGame();
});

/**
 * Initialize the game
 */
function initializeGame() {
    // socket with robot
    console.log("Init");
    console.log("Player ID:", id_player);
    let socket_address = 'robot_hint_' + id_player
    console.log("beginning addr", socket_address)
    hintReceivedByRobot(socket_address)
    moveReceivedByRobot(socket_address)

    //document.querySelector('.overlay').style.display = 'none';
    document.querySelector('.deck').innerHTML = '';
    
    resetGameVariables();
    resetTimer();
    runTimer();
    myResetTimer();
    myRunTimer();
    printStars();
    printMoves();
    printTrials();
    changeLanguage()

    createCards();
}

/**
 * Reset variables when game is finished.
 */
function resetGameVariables() {
    state.opened = [];
    state.numStars = 3;
    state.numMoves = 0;
    state.numMatch = 0;
    state.turns = 1;
    state.isMatch = false;
}
