// score.js
// =============================
// this file containts functions to manage the score such as stars, moves, matches, trials, ecc
// =============================

import { state } from './state.js';
import { showStar } from './config.js';

// for shuffle
export function printTrials() {
    document.querySelectorAll('.trials').forEach(move => move.innerHTML = `<b>${state.consecutiveUnsuccessfulAttempts}</b>`);
}

// Print "stars", "moves", "matches" to the page
export function printStars() {
    document.querySelectorAll('.stars').forEach(panel => panel.innerHTML = showStar[state.numStars - 1]);
}

export function printMoves() {
    document.querySelectorAll('.moves').forEach(move => move.innerHTML = `<b>${state.numMoves}</b>`);
}

/**
 * Calculate Stars by the moves and print it
 */
export function starCount() {
    if (state.numMoves <= 20) {
        state.numStars = 3;
    } else if (state.numMoves <= 27) {
        state.numStars = 2;
    } else {
        state.numStars = 1;
    }
    printStars();
}
