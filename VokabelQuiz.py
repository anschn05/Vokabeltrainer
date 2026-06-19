import random
import sys

# --------- Einzeltaste ----------
def get_single_key():
    try:
        import msvcrt
        key = msvcrt.getch().decode("utf-8")
        print(key)
        return key
    except ImportError:
        import sys, tty, termios
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
            print(key)
            return key
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

# --------------------------------

def load_vocab(filename):
    vocab = []
    with open(filename, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) != 2:
                continue
            en = parts[0].strip()
            de = [x.strip() for x in parts[1].split(";")]
            vocab.append((en, de))
    return vocab


def print_feedback(correct, solution):
    if correct:
        print("\t✔\n")
    else:
        print(f"\t✘ richtig: {solution}\n")


def print_progress(done, correct, total, mistakes):
    print(f"\nZwischenstand: {correct}/{done} (von {total}) | Fehler: {mistakes}\n")


def check_abort(user_input, done, correct, total, mistakes):
    if user_input.strip().lower() == "q":
        print(f"\nAbbruch: {correct}/{done} | Fehler: {mistakes}\n")
        sys.exit(0)


def handle_wrong_answer(solution, correct_count, mistakes):
    mistakes += 1
    print_feedback(False, solution)
    user = input("\tc = als richtig werten, Enter = falsch lassen, q = Abbruch: ").strip().lower()

    if user == "c":
        print("\t→ als richtig gewertet\n")
        return correct_count + 1, True, mistakes
    elif user == "q":
        print("\nAbbruch\n")
        sys.exit(0)

    return correct_count, False, mistakes


def ask_question(en, de_list, mode, vocab):
    # -------- Normal ----------
    if mode == 1:
        return input(f"{en} -> "), de_list

    elif mode == 2:
        de = random.choice(de_list)
        return input(f"{de} -> "), [en]

    # -------- MC EN -> DE ----------
    elif mode == 3:
        correct_de = random.choice(de_list)

        wrong = random.sample([v for v in vocab if v[0] != en], min(3, len(vocab)-1))
        options = [correct_de] + [random.choice(w[1]) for w in wrong]
        random.shuffle(options)

        print(f"{en} ->")
        for i, opt in enumerate(options):
            print(f"{i+1}: {opt}")

        print("-> ", end="", flush=True)
        return get_single_key(), options, correct_de

    # -------- MC DE -> EN ----------
    elif mode == 4:
        correct_de = random.choice(de_list)

        wrong = random.sample([v for v in vocab if v[0] != en], min(3, len(vocab)-1))
        options = [en] + [w[0] for w in wrong]
        random.shuffle(options)

        print(f"{correct_de} ->")
        for i, opt in enumerate(options):
            print(f"{i+1}: {opt}")

        print("-> ", end="", flush=True)
        return get_single_key(), options, en


def run_session(vocab, mode):
    correct = 0
    total_done = 0
    mistakes = 0

    order = random.sample(vocab, len(vocab))
    wrong_buffer = []

    for i, (en, de_list) in enumerate(order, start=1):

        try:
            if mode in [3, 4]:
                answer, options, correct_solution = ask_question(en, de_list, mode, vocab)
            else:
                answer, solutions = ask_question(en, de_list, mode, vocab)
        except KeyboardInterrupt:
            print(f"\nAbbruch: {correct}/{total_done} | Fehler: {mistakes}\n")
            sys.exit(0)

        check_abort(answer, total_done, correct, len(vocab), mistakes)
        answer = answer.strip().lower()

        if mode in [3, 4]:
            try:
                choice = int(answer)
                if options[choice-1] == correct_solution:
                    correct += 1
                    print_feedback(True, "")
                else:
                    correct, ok, mistakes = handle_wrong_answer(correct_solution, correct, mistakes)
                    if not ok:
                        wrong_buffer.append((en, de_list))
            except:
                correct, ok, mistakes = handle_wrong_answer(correct_solution, correct, mistakes)
                if not ok:
                    wrong_buffer.append((en, de_list))

        else:
            if answer in [s.lower() for s in solutions]:
                correct += 1
                print_feedback(True, "")
            else:
                correct, ok, mistakes = handle_wrong_answer(", ".join(solutions), correct, mistakes)
                if not ok:
                    wrong_buffer.append((en, de_list))

        total_done += 1

        if i % 10 == 0:
            print_progress(total_done, correct, len(vocab), mistakes)

            if wrong_buffer:
                print("Wiederholung falscher Wörter:\n")
                retry = wrong_buffer
                wrong_buffer = []

                for en2, de_list2 in retry:
                    try:
                        if mode in [3, 4]:
                            answer, options, correct_solution = ask_question(en2, de_list2, mode, vocab)
                        else:
                            answer, solutions = ask_question(en2, de_list2, mode, vocab)
                    except KeyboardInterrupt:
                        print(f"\nAbbruch: {correct}/{total_done} | Fehler: {mistakes}\n")
                        sys.exit(0)

                    check_abort(answer, total_done, correct, len(vocab), mistakes)
                    answer = answer.strip().lower()

                    if mode in [3, 4]:
                        try:
                            choice = int(answer)
                            if options[choice-1] == correct_solution:
                                correct += 1
                                print_feedback(True, "")
                            else:
                                correct, ok, mistakes = handle_wrong_answer(correct_solution, correct, mistakes)
                                if not ok:
                                    wrong_buffer.append((en2, de_list2))
                        except:
                            correct, ok, mistakes = handle_wrong_answer(correct_solution, correct, mistakes)
                            if not ok:
                                wrong_buffer.append((en2, de_list2))
                    else:
                        if answer in [s.lower() for s in solutions]:
                            correct += 1
                            print_feedback(True, "")
                        else:
                            correct, ok, mistakes = handle_wrong_answer(", ".join(solutions), correct, mistakes)
                            if not ok:
                                wrong_buffer.append((en2, de_list2))

    return correct, mistakes


def main():
    vocab = load_vocab("vocab.txt")

    if not vocab:
        print("Keine Vokabeln geladen.")
        return

    print("Modus wählen:")
    print("1: Englisch -> Deutsch")
    print("2: Deutsch -> Englisch")
    print("3: Multiple Choice EN -> DE")
    print("4: Multiple Choice DE -> EN")
    print("(Abbruch mit q)")

    mode = input("Auswahl: ").strip()

    if mode not in ["1", "2", "3", "4"]:
        print("Ungültig")
        return

    correct, mistakes = run_session(vocab, int(mode))

    print(f"\nEndergebnis: {correct}/{len(vocab)} | Fehler gesamt: {mistakes}")


if __name__ == "__main__":
    main()