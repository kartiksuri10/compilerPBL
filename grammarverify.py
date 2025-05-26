import re

def parse_grammar(grammar_lines):
    grammar = {}
    non_terminals = set()

    for line in grammar_lines:
        line = re.sub(r'\s+', ' ', line.strip())  # normalize whitespace

        if "->" not in line:
            print(f"❌ Invalid production (missing '->'): {line}")
            return None

        left, right = map(str.strip, line.split("->", 1))

        if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", left):
            print(f"❌ Invalid non-terminal name: {left}")
            return None

        productions = [p.strip() for p in right.split('|') if p.strip()]
        if not productions:
            print(f"❌ No valid production rules on the right-hand side for: {left}")
            return None

        for prod in productions:
            if not re.fullmatch(r"[A-Za-z0-9+\-*/ε() ]+", prod):
                print(f"⚠️  Warning: Possibly invalid characters in production: {left} -> {prod}")

        if left not in grammar:
            grammar[left] = []

        # Check for duplicate productions
        duplicates = set(productions) & set(grammar[left])
        if duplicates:
            print(f"⚠️  Warning: Duplicate production(s) for {left}: {', '.join(duplicates)}")

        grammar[left].extend(productions)
        non_terminals.add(left)

    return grammar, non_terminals


def find_undefined_non_terminals(grammar, defined_non_terminals):
    used_non_terminals = set()
    for productions in grammar.values():
        for prod in productions:
            for symbol in re.findall(r'[A-Z][A-Za-z0-9]*', prod):  # extended to multi-letter NTs
                used_non_terminals.add(symbol)
    undefined = used_non_terminals - defined_non_terminals
    return undefined


def detect_left_recursion(grammar):
    left_recursive = {}
    for nt, prods in grammar.items():
        recursives = [p for p in prods if p.startswith(nt)]
        if recursives:
            left_recursive[nt] = recursives
    return left_recursive


def remove_immediate_left_recursion(grammar):
    updated_grammar = {}

    for nt, prods in grammar.items():
        alpha = []
        beta = []

        for p in prods:
            if p.startswith(nt):
                alpha.append(p[len(nt):])
            else:
                beta.append(p)

        if alpha:
            new_nt = nt + "'"
            if beta:
                updated_grammar[nt] = [b + new_nt for b in beta]
            else:
                updated_grammar[nt] = [new_nt]

            updated_grammar[new_nt] = [a + new_nt for a in alpha]
            updated_grammar[new_nt].append('ε')
        else:
            updated_grammar[nt] = prods

    return updated_grammar


def display_grammar(grammar):
    for nt, prods in grammar.items():
        print(f"{nt} -> {' | '.join(prods)}")


def grammar_verifier_interface():
    print("Enter grammar productions (one per line). Type 'done' to finish.")
    print("Example: E -> E+T | T\n")

    lines = []
    while True:
        line = input(">> ").strip()
        if line.lower() == "done":
            break
        if line:
            lines.append(line)

    result = parse_grammar(lines)
    if not result:
        return

    grammar, defined_non_terminals = result

    undefined_nts = find_undefined_non_terminals(grammar, defined_non_terminals)
    if undefined_nts:
        print(f"\n❌ Error: Undefined non-terminals used: {', '.join(undefined_nts)}")
        return

    print("\n✅ Grammar successfully parsed.")
    print("Original Grammar:")
    display_grammar(grammar)

    left_recursions = detect_left_recursion(grammar)
    if left_recursions:
        print("\n⚠️  Immediate Left Recursion detected in:")
        for nt, prods in left_recursions.items():
            print(f"  {nt}: {', '.join(prods)}")

        print("\nNote: Only immediate left recursion is handled. Indirect left recursion is not detected.")

        choice = input("\nDo you want to remove immediate left recursion? (y/n): ").strip().lower()
        if choice == 'y':
            grammar = remove_immediate_left_recursion(grammar)
            print("\n✅ Updated Grammar (Left Recursion Removed):")
            display_grammar(grammar)
    else:
        print("\n✅ No immediate left recursion found.")


if __name__ == "__main__":
    grammar_verifier_interface()
