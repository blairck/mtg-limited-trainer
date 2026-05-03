# Web UI Design: MTG Limited Trainer

## Overview
Convert the command-line quiz tool into a browser-based application. The core game loop remains unchanged; UI interactions migrate from terminal prompts to web forms.

## User Flow

### 1. Setup Page
- **Purpose:** Configure quiz parameters before starting
- **Elements:**
  - Magic Set selector (dropdown from available sets)
  - Difficulty radio buttons (easy, medium, hard)
  - Rarity checkboxes (C, U, R, M with defaults)
  - Rating key selector (dropdown from available keys like CARD_OHWR)
  - Number of questions input (default 15)
  - "Start Quiz" button
- **Output:** Display card count by rarity and rating ranges for selected difficulty

### 2. Quiz Page
- **Purpose:** Present cards and collect answers
- **Elements:**
  - Card image (left/top)
  - Card name and rarity badge
  - Question counter (e.g., "Question 3/15")
  - Multiple-choice buttons (labels vary by difficulty: 3 for easy, 4 for medium, 5 for hard)
  - Color coding on buttons (red/yellow/green/blue/magenta per difficulty)
- **Behavior:**
  - Show one card at a time, no feedback until round end
  - Disable submit button until an option is selected
  - Move to next card on selection or auto-advance

### 3. Round Results Page
- **Purpose:** Show round performance
- **Elements:**
  - Percentage correct
  - Count of correct/incorrect
  - List of cards answered incorrectly
- **Options:**
  - "Retry Wrong Cards" button (if <100% correct)
  - "Restart Quiz" button
  - "Exit" button

### 4. Final Results Page
- **Purpose:** Summary and exit
- **Elements:**
  - Final score percentage
  - Total rounds completed
  - Cards that remained difficult across rounds
  - "New Quiz" button (return to Setup Page)

## Architecture

### Backend
- **Framework:** Flask or FastAPI (lightweight)
- **Endpoints:**
  - `GET /api/config` – available sets, rating keys, card counts
  - `POST /api/quiz/init` – create new quiz session with parameters
  - `GET /api/quiz/<session_id>` – current question/state
  - `POST /api/quiz/<session_id>/answer` – submit answer, get feedback
  - `GET /api/quiz/<session_id>/results` – round results

### Frontend
- **Framework:** React or vanilla JS (simple form-based app)
- **State Management:** Session ID stored in URL or localStorage
- **Components:**
  - `SetupForm` → `QuizCard` → `RoundResults` → `FinalResults`

### Data Flow
1. Backend loads CSVs in memory (as done in `src/data.py`)
2. Session stores: quiz_id, cards_list, current_round_state, answer_history
3. Frontend requests next question, submits answer, displays results
4. Backend calculates round metrics and wrong-card list
5. On retry, backend filters quiz_cards to wrong answers only

## API Contracts

```json
POST /api/quiz/init
{
  "magic_set": "eoe",
  "difficulty": "medium",
  "rarities": ["C", "U"],
  "rating_key": "CARD_OHWR",
  "num_questions": 15
}
→ { "session_id": "abc123", "total_questions": 15 }

GET /api/quiz/abc123
→ {
  "card": { "Name": "...", "Rarity": "U", ... },
  "question_num": 1,
  "options": ["bad", "okay", "good", "great"],
  "colors": ["red", "yellow", "green", "blue"]
}

POST /api/quiz/abc123/answer
{ "card_name": "...", "selected_option": 1 }
→ { "correct": true, "next": {...} or "round_end": true }

GET /api/quiz/abc123/results
→ {
  "round": 1,
  "percentage_correct": 86.7,
  "wrong_cards": ["Card A", "Card B"],
  "has_wrong_cards": true
}
```

## Migration Strategy

1. **Reuse core logic:** Keep `src/data.py`, `src/cards.py`, `src/game_logic.py` unchanged
2. **Extract session logic:** Move round tracking and answer validation from `main.py` into a new `src/session.py` module
3. **API layer:** Create `app.py` with routes that delegate to session manager
4. **Frontend:** Lightweight HTML/JS pages or React SPA

## Tech Stack (Recommended)

- **Backend:** FastAPI (async, lightweight)
- **Frontend:** React with TypeScript or vanilla JS
- **Styling:** Tailwind CSS or Bootstrap
- **Deployment:** Docker container, host on any cloud (AWS, Render, etc.)

## Future Enhancements

- User accounts and score history
- Card difficulty heatmap (which cards trip up most users)
- Timed mode
- Mobile-responsive design
- Dark/light theme
