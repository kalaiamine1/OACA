import json
import os
import random
import sys
from typing import Any, Dict, List, Optional, Tuple


def load_quiz_data(json_path: str) -> Dict[str, Any]:
    if not os.path.exists(json_path):
        print(f"Error: Quiz data file not found at {json_path}")
        sys.exit(1)
    try:
        with open(json_path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    except json.JSONDecodeError as exc:
        print(f"Error: Failed to parse JSON file: {exc}")
        sys.exit(1)


def prompt_int(prompt: str, min_value: int, max_value: int) -> int:
    while True:
        value = input(prompt).strip()
        if value.isdigit():
            number = int(value)
            if min_value <= number <= max_value:
                return number
        print(f"Please enter a number between {min_value} and {max_value}.")


def prompt_choice(prompt: str, choices: List[str]) -> str:
    valid = {c.upper() for c in choices}
    while True:
        value = input(prompt).strip().upper()
        if value in valid:
            return value
        print(f"Please choose one of: {', '.join(sorted(valid))}.")


def normalize_options(options: Dict[str, str]) -> List[Tuple[str, str]]:
    # Ensure options are presented in alphabetical key order (A, B, C, ...)
    return sorted(options.items(), key=lambda kv: kv[0])


def select_category(categories: List[Dict[str, Any]]) -> Optional[int]:
    print("\nAvailable categories:")
    for idx, cat in enumerate(categories, start=1):
        name = cat.get("name", f"Category {idx}")
        desc = cat.get("description", "")
        print(f"  {idx}. {name} - {desc}")
    print("  0. All categories")
    selection = prompt_int("Select a category number (0 for all): ", 0, len(categories))
    return None if selection == 0 else selection - 1


def gather_questions(categories: List[Dict[str, Any]], category_index: Optional[int]) -> List[Dict[str, Any]]:
    if category_index is None:
        all_questions: List[Dict[str, Any]] = []
        for cat in categories:
            all_questions.extend(cat.get("questions", []))
        return all_questions
    return list(categories[category_index].get("questions", []))


def run_quiz(quiz_data: Dict[str, Any]) -> None:
    header = quiz_data.get("quiz_data", {})
    title = header.get("title", "Quiz")
    description = header.get("description", "")
    categories = header.get("categories", [])

    print(f"\n=== {title} ===")
    if description:
        print(description)

    if not categories:
        print("No categories found in the quiz data.")
        return

    cat_idx = select_category(categories)
    questions = gather_questions(categories, cat_idx)
    if not questions:
        print("No questions found for the selected category.")
        return

    # Shuffle questions for variety
    random.shuffle(questions)

    # Optionally limit number of questions
    print(f"Total questions available: {len(questions)}")
    limit = prompt_int("How many questions to attempt? (enter 0 for all): ", 0, len(questions))
    if limit > 0:
        questions = questions[:limit]

    score = 0
    total_with_keys = 0
    unanswered_key_questions: List[int] = []
    incorrect: List[Tuple[int, str, str]] = []  # (id, your_answer, correct)

    for index, q in enumerate(questions, start=1):
        q_id = q.get("id")
        text = q.get("question", "")
        options: Dict[str, str] = q.get("options", {})
        correct: Optional[str] = q.get("correct_answer")

        print(f"\nQ{index}. {text}")
        for key, val in normalize_options(options):
            print(f"  {key}. {val}")

        # Determine valid option letters from provided options
        valid_letters = list(options.keys())
        if not valid_letters:
            print("No options provided. Skipping question.")
            continue

        answer = prompt_choice("Your answer: ", valid_letters)

        if correct is None:
            unanswered_key_questions.append(q_id)
            print("Recorded. (No answer key provided for scoring)")
            continue

        total_with_keys += 1
        if answer.upper() == str(correct).upper():
            score += 1
            print("Correct!")
        else:
            print(f"Incorrect. Correct answer: {correct}")
            incorrect.append((q_id, answer, str(correct)))

    print("\n=== Results ===")
    print(f"Attempted: {len(questions)} questions")
    print(f"Scored: {score}/{total_with_keys} (questions that had answer keys)")
    if incorrect:
        print("\nReview the following:")
        for q_id, your, corr in incorrect:
            print(f"- Question ID {q_id}: Your answer {your} | Correct {corr}")
    if unanswered_key_questions:
        print("\nNote: The following question IDs have no answer key and were not scored:")
        print(", ".join(str(q) for q in unanswered_key_questions))


def main() -> None:
    default_path = os.path.join(os.path.dirname(__file__), "aviation_quiz_data.json")
    data_path = sys.argv[1] if len(sys.argv) > 1 else default_path
    data = load_quiz_data(data_path)
    run_quiz(data)


if __name__ == "__main__":
    main()


