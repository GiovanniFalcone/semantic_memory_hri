// board.js
// =============================
// Board Creation and Card Logic
// =============================

import { state, maxMatch, shuffleBoard } from './state.js';
import { pairs } from './config.js';
import { sendFlask } from './flask.js';   
import { stopTimer, myStopTimer } from './timers.js';
import { starCount, printMoves, printTrials } from './score.js';
import { handleShuffle } from './shuffle.js';
import { congrats, turnPopUp, hideTurnPopup, turnPopUpUser, hideTurnPopupUser } from './popups.js';
import { shuffle } from './utils.js';

/**
 * Generate cards from pairs
 */
function generatePossibleCards() {
    Object.entries(pairs).forEach(([city, country]) => {
        state.possibleCards.push(city);
        state.possibleCards.push(country);
    });
}


/**
 * Create deck
 */
export function createCards() {
    // put all possible cards in the array
    generatePossibleCards();
    // shuffle the cards
    const shuffledCards = shuffle(state.possibleCards);
    // send board to server
    const data = {
        "deck": pairs,                  // dictionary of card
        "shuffled_deck": shuffledCards  // list of card shuffled
    }
    sendFlask("board", data, '/game_board');

    shuffledCards.forEach((card, index) => {
        const cardElement = document.createElement('li');
        cardElement.classList.add('card');
        cardElement.id = index;
        cardElement.innerHTML = `<img src="/static/images/${card}.svg"/>`;
        cardElement.setAttribute('data-name', card);
        cardElement.addEventListener('click', () => cardClickListener(cardElement, card));
        document.querySelector('.deck').appendChild(cardElement);
    });
}

/**
 * Handle card clicks
 */
export async function cardClickListener(cardElement, card) {
    // if pair is already found the card of pair can't be clicked
    // or the game board is changing
    if (cardElement.classList.contains('match') || state.boardChanging) {
        return;
    }

    card = cardElement.getAttribute('data-name');

    document.querySelectorAll(".card").forEach(card => {
        card.classList.remove('hint');
        card.classList.remove('flipInY');
        document.querySelector('.speech-bubble').style.display = 'none';
    });

    if (cardElement.classList.contains('show')) {
        return;
    }

    cardElement.classList.add('show', 'animated', 'flipInY');
    state.opened.push(card);

    const filename = card.replace(/^.*[\\\/]/, '');
    const clickedCardName = filename.replace(/\..+$/, '');

    // get coordinates of clicked card
    const positionCard = Number(cardElement.id);
    const indexRow = Math.floor(positionCard / 4);
    const indexCol = positionCard % 4;

    const clickedCardPosition = [indexRow, indexCol];
    console.log("Clicked card: " + clickedCardName + " at position " + clickedCardPosition + " at turn " + state.turns);

    

    if (state.opened.length > 1) {
        const first = state.opened[0];
        const second = state.opened[1];
        if (pairs[first] === second || pairs[second] === first) {
            match();
            // update shuffle trials and remaining cards if shuffle is enabled
            state.remainingCards -= 2;
            state.shuffleTrials = Math.round(state.remainingCards / state.k);
            state.consecutiveUnsuccessfulAttempts = state.shuffleTrials;
            state.cardsFound.push(first);
            state.cardsFound.push(second);
            console.log("Cards found so far: " + state.cardsFound);

            // color shuffle trials
            const desc = document.querySelector('.trials');
            desc.style.color = '#27ae60';

            setTimeout(() => {
                desc.style.color = '';  // reset color after feedback
            }, 1500);                   // feedback duration
        } else {
            console.log("Shuffle board is " + shuffleBoard)
            // if shuffle is True check if the board should be changed
            if(shuffleBoard == true && state.turns >= 4){
                unmatch();

                // if shuffle trials are over, shuffle the board and reset cards seen, counter, ...
                await handleShuffle(first, second);
            } else {
                unmatch();
            }
        }
    } else {
        state.isMatch = false;
    }

    starCount();
    printMoves();
    printTrials();

    if(state.numMatch === maxMatch() ) {
        stopTimer();
        myStopTimer();
        congrats();
    }

    // console.log("Returning after shuffle if any... the array is " + state.allCardNames)
    sendFlask("game", {
        "open_card_name": clickedCardName,
        "position": clickedCardPosition,
        "index": positionCard,
        "pairs": state.numMatch,
        "turn": state.turns,
        "match": state.isMatch,
        "is_robot_turn": state.isRobotTurn,
        "is_wrong_card": state.hasProvidedWrongCard,
        "robot_subject": state.robotSubject,
        "n_face_up": state.opened.length,
        "time_until_match": `${state.myMinutes}:${state.mySeconds}`,
        "time_game": `${state.minutes}:${state.seconds}`,
        "cards_found": state.cardsFound,
        "board_changed": state.boardChanging,
        "new_board": state.allCardNames
    }, "/player_move");

    // update the board changing in case shuffle was done
    state.boardChanging = false;
    state.allCardNames = [];
    state.robotSubject = "";

    // update turns number
    state.turns++;

    // reset to track time for pair
    if (state.isMatch) {
        state.myMinutes = 0;
        state.mySeconds = 0;
    }
}

/**
 * When the user finds a pair, the pair will not be covered.
 */
export function match() {
    state.numMoves++;
    state.numMatch++;
    state.isMatch = true;
    state.opened = [];

    document.querySelectorAll(".show").forEach(matchedCard => {
        matchedCard.classList.add('match', 'animated', 'flip');
        matchedCard.classList.remove('show');
    });
}

/**
 * When user has not find a pair show error and increase moves.
 */
export function unmatch() {
    state.numMoves++;
    state.isMatch = false;
    state.opened = [];

    document.querySelectorAll(".show:not(.match)").forEach(unmatchedCard => {
        unmatchedCard.classList = 'card show unmatch animated shake';
        document.querySelectorAll('.unmatch').forEach(unmatchedCard => {
            setTimeout(() => {
                unmatchedCard.classList = 'animated flipInY card';
            }, 600);
        });
    });
}


