// shuffle.js
// =============================
// shuffle logic
// =============================

import { state, language } from './state.js';
import { runTimer, myRunTimer, stopTimer, myStopTimer } from './timers.js';
import { printMoves, starCount, printTrials } from './score.js';
import { shuffle } from './utils.js';

// Handle shuffle logic
// this function is called when two cards do not match
export function handleShuffle(firstCard, secondCard) {
    return new Promise((resolve) => {
        // compute the number of shuffle trials based on the number of remaining cards, but only at the first shuffle (turn 0), 
        // then it will be updated after each shuffle based on the remaining cards
        if(state.turns == 4){
            state.shuffleTrials = Math.round(state.remainingCards / state.k);
            state.consecutiveUnsuccessfulAttempts = state.shuffleTrials;
        }
        
        // check malus for shuffle
        // 1. Check if the user knew one or both cards (i.e., they were in the set of seen cards)
        let malus = 0;
        const firstSeen = state.seenCards.has(firstCard);
        const secondSeen = state.seenCards.has(secondCard);
        
        if (firstSeen && secondSeen) {
            // the user knew both cards but still failed to match
            malus = 2; 
        } else if (firstSeen || secondSeen) {
            // the user knew one of the two cards
            malus = 1;
        } else {
            // the user did not know either card -> exploration 
            malus = 0.5;
        }
        
        // 2. update counter
        state.consecutiveUnsuccessfulAttempts -= malus;

        // 3. color text of trails in order to give feedback to the user about how close they are to shuffle
        const desc = document.querySelector('.trials');
        desc.style.color = 'red';
        
        // 4. add seen cards to the set of seen cards
        state.seenCards.add(firstCard);
        state.seenCards.add(secondCard);
        
        console.log(`Malus is: ${malus}. T = ${state.shuffleTrials}`);
        console.log("Trials: " + state.consecutiveUnsuccessfulAttempts + " <= " + state.shuffleTrials)

        printTrials();

        setTimeout(() => {
            desc.style.color = '';  // reset color after feedback
        }, 1500);                   // feedback duration
        
        if(state.consecutiveUnsuccessfulAttempts <= 0){
            state.consecutiveUnsuccessfulAttempts = state.shuffleTrials;
            state.boardChanging = true;

            state.seenCards.clear(); // reset seen cards when shuffle happens

            starCount();
            printMoves();

            setTimeout(() => {
                changeBoard().then(() => {
                    printTrials();
                    console.log("New shuffle");
                    resolve();
                });
            }, 750);
        } else {
            resolve(); 
        }
    });
}

/** ******************************************************************************************************************
 *                                           ANIMATION WHEN CARD CHANGES                                            *                                               
 * ******************************************************************************************************************* 
 * */ 

function changeBoard(){
    /* Once the user has done many consecutive attempts the board game will change */
    return new Promise(resolve => {
        stopTimer();
        myStopTimer();

        changeBoardPopUp();
        printTrials();

        setTimeout(() => {
            hideBoardPopup();
        }, 500);

        setTimeout(async () => {
            await shuffleUnmatchedCards();
            resolve();
        }, 1500);
    });
}

// Pop-up when the robot provide a suggestion
function changeBoardPopUp() {
    const popup = document.getElementById('blur-popup');
    const title = popup.querySelector('.popup-title');
    const desc = popup.querySelector('.popup-description');

    if (language === 'en') {
        title.textContent = 'Oh no! The board game is changing!';
        desc.textContent = 'Please wait while the new board is being generated.';
    } else {
        title.textContent = 'Oh no! Il tabellone sta cambiando!';
        desc.textContent = 'Attendi un momento mentre il nuovo tabellone viene generato.';
    }

    setTimeout(() => {
        popup.style.display = 'flex';
    }, 10);
    
}

// Hide pop-up
function hideBoardPopup() {
    const popup = document.getElementById('blur-popup');
    const card = popup.querySelector('.popup-card');

    // after 1250 ms the animation will go
    setTimeout(() => {
        card.style.transition = 'opacity 0.4s ease';
        card.style.opacity = '0';

        popup.style.backgroundColor = 'transparent';
        popup.style.backdropFilter = 'none';

        setTimeout(() => {
            popup.style.display = 'none';

            card.style.opacity = '1';
            popup.style.backgroundColor = 'rgba(0, 0, 0, 0.6)';
            popup.style.backdropFilter = 'blur(8px)';
        }, 200); // transition animation time
    }, 1250); // time of popup
}


// shuffle un-matched cards and send to flask the last move and new board
function shuffleUnmatchedCards() {
    return new Promise(resolve => {

        const deck = document.querySelector('.deck');
        const allCards = Array.from(deck.querySelectorAll('.card'));
        const unmatchedCards = allCards.filter(card => !card.classList.contains('match'));
        const matchedCards = allCards.filter(card => card.classList.contains('match'));

        const deckRect = deck.getBoundingClientRect();

        document.querySelectorAll(".card").forEach(card => {
            card.classList.remove('hint');
            card.classList.remove('flipInY');
            document.querySelector('.speech-bubble').style.display = 'none';
        });

        // Get center of grid
        const centerX = deckRect.width / 2;
        const centerY = deckRect.height / 2;

        // 0: hide pairs already found
        matchedCards.forEach(card => {
            card.classList.add('matched-hidden');
        });

        // 1. Animation towards the center of the board
        unmatchedCards.forEach(card => {
            const cardRect = card.getBoundingClientRect();
            const offsetX = centerX - (cardRect.left - deckRect.left + cardRect.width / 2);
            const offsetY = centerY - (cardRect.top - deckRect.top + cardRect.height / 2);

            card.style.setProperty('--center-x', `${offsetX}px`);
            card.style.setProperty('--center-y', `${offsetY}px`);

            // add first animation
            card.classList.add('shuffle-start', 'trail');
        });

        // Shuffle cards 
        requestAnimationFrame(() => {
            setTimeout(() => {
                // get the images of unmatched cards
                const unmatchedImages = unmatchedCards.map(card => {
                    const img = card.querySelector('img');
                    return img.getAttribute('src');
                });
                // shuffle them
                const shuffledImages = shuffle(unmatchedImages);
                // get the name of each card
                const unmatchedNames = shuffledImages.map(imgPath => {
                    const filename = imgPath.replace(/^.*[\\\/]/, '');
                    return filename.replace(/\..+$/, '');
                });

                // update unmatched cards (name and new index)
                unmatchedCards.forEach((card, index) => {
                    const img = card.querySelector('img');
                    img.setAttribute('src', shuffledImages[index]);

                    const newName = shuffledImages[index].replace(/^.*[\\\/]/, '').replace(/\..+$/, '');
                    card.setAttribute('data-name', newName);

                    // hide cards
                    card.classList.remove('show', 'animated', 'flipInY');
                });

                // the cards have been shuffled -> add the second animation
                unmatchedCards.forEach(card => {
                    card.classList.remove('shuffle-start');
                    card.classList.add('shuffle-end');
                });

                // Combines the pairs not found and those already found so that you have the whole board
                state.allCardNames = allCards.map(card => card.getAttribute('data-name'));

                // remove animations and send the new board to flask
                setTimeout(() => {
                    unmatchedCards.forEach(card => {
                        card.classList.remove('shuffle-end', 'trail');
                    });
                    
                    matchedCards.forEach(card => {
                        card.classList.remove('matched-hidden');
                    });

                    console.log("New board: " + state.allCardNames)
                    console.log("Unmatched: " + unmatchedNames)

                    // if board is changed do not send the move just done
                    console.log("Board changed? " + state.boardChanging) 

                    resolve(); 
                    
                }, 850); // total time between start -> end

                runTimer();
                myRunTimer();

            }, 1000); // Waiting time for movement to the center
        });
    });
}

