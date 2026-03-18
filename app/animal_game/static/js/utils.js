// utils.js
// =============================
// Utility functions & global page events
// =============================

import { id_player, language, state } from './state.js';

/**
 * Shuffle the array of cards
 * @param {*} array 
 * @returns 
 */
export function shuffle(array) {
    return array.sort(() => Math.random() - 0.5);
}

/**
 * Check if it's the first visit
 */
export function checkFirstVisit() {
    if (document.cookie.indexOf('mycookie') === -1) {
        document.cookie = 'mycookie=1';
        console.log("First visit...");
    } else {
        console.log("Not first visit...");
    }
}

/**
 * Handle page refresh / unload events
 */
export function setupUnloadEvents() {
    window.addEventListener('beforeunload', function (e) {
        if (!(state.numMatch == 8)) {
            const text = language === 'inglese'
                ? 'Are you sure you want to refresh the page? The game is not finished yet.'
                : 'Sei sicuro di voler aggiornare la pagina? Il gioco non è ancora finito.';
            (e || window.event).returnValue = text;
            return text;
        }
    });

    window.addEventListener('unload', function(event) {
        if (!(state.numMatch == 8)) {
            console.log('Un cheattone ha ricaricato la pagina nonostante il gioco non fosse finito.');
            fetch('/cheating/' + id_player)
                .then(response => response.text())
                .then(data => { console.log(data); })
                .catch(error => console.error('Error:', error));
        }
    });
}

/**
 * Setup exit button in congrats popup
 */
export function setupExitButton() {
    const exitBtn = document.getElementById('congrats-popup').querySelector('.exit');
    exitBtn.addEventListener('click', function() {
        console.log("User has pressed exit!");
        fetch('/exit', {
            method: 'GET', 
            headers: { 'Content-Type': 'application/json' }
        })
        .then(() => {
            console.log("Redirect to home page!");
            window.location.href = '/index';
        })
        .catch(error => console.error('Error:', error));
    });
}

/**
 * Change language of static labels
 */
export function changeLanguage() {
    if(language === 'inglese'){
        document.querySelector('label[for="formText2"]').textContent = "Thanks for playing!";
    }
}
