from src.quiz import (
    round_to_increment,
    round_to_half,
    make_question,
    generate_questions,
    Question,
    DEFAULT_NUM_CHOICES,
)


def test_round_to_increment():
    # Test rounding to nearest step for various values
    assert round_to_increment(5.3, 2) == 6
    assert round_to_increment(5.2, 2) == 6
    assert round_to_increment(5.2, 0.5) == 5.0
    assert round_to_increment(4.75, 0.5) == 5.0
    assert round_to_increment(4.74, 0.5) == 4.5


def test_round_to_half():
    # round_to_half should use a step of 0.5
    assert round_to_half(5.3) == round_to_increment(5.3, 0.5)
    assert round_to_half(2.24) == round_to_increment(2.24, 0.5)


def test_make_question_deterministic_branch(monkeypatch):
    # Force random.random >= 0.67 to take the sampling branch
    monkeypatch.setattr("src.quiz.random.random", lambda: 1.0)
    # Make sample and shuffle deterministic
    monkeypatch.setattr("src.quiz.random.sample", lambda seq, k: list(seq)[:k])
    monkeypatch.setattr("src.quiz.random.shuffle", lambda x: None)

    # Prepare a test card with a float-like string rating
    card = {"value": "2.3"}
    q = make_question(card, "value", 0.0, 5.0, step=1.0)

    # Expect default number of options
    assert isinstance(q, Question)
    assert len(q.options) == DEFAULT_NUM_CHOICES

    # Given true_rounded of 2.0, candidates are [0,1,2,3,4,5]
    # Wrong picks should be first 4 others [0,1,3,4] and then true 2.0
    # shuffle is a no-op, so order is known
    assert q.options == [0.0, 1.0, 3.0, 4.0, 2.0]

    # Correct indices are where abs(option - true_val) < step => abs(opt - 2.3) < 1.0
    assert q.correct_indices == [2, 4]


def test_generate_questions(monkeypatch):
    # Prepare simple card list
    cards = [{"v": "1"}, {"v": "2"}, {"v": "3"}]
    # Ensure sampling returns first items
    monkeypatch.setattr("src.quiz.random.sample", lambda seq, k: seq[:k])

    qs = generate_questions(cards, "v", 0.0, 2.0, num_questions=2, step=1.0)
    # Should generate exactly 2 questions
    assert len(qs) == 2
    # Questions should be instances of Question and correspond to first two cards
    assert all(isinstance(item, Question) for item in qs)
    assert [item.card for item in qs] == cards[:2]
