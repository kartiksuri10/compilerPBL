import tkinter as tk
from tkinter import filedialog, messagebox
from read_grammar_clr_temp import ReadGrammar

class CLR1Parser:
    def __init__(self, grammar):
        self.grammar = grammar
        self.terminals = self.grammar.get_terminals()
        self.non_terminals = self.grammar.get_non_terminals()
        self.first_sets = self.compute_first_sets()
        self.follow_sets = self.compute_follow_sets()
        self.compute_closure_goto()

    def compute_first_sets(self):
        first = {symbol: set() for symbol in self.non_terminals}
        for terminal in self.terminals:
            first[terminal] = {terminal}
        
        changed = True
        while changed:
            changed = False
            for non_terminal, productions in self.grammar.items():
                for production in productions:
                    if not production:
                        if '' not in first[non_terminal]:
                            first[non_terminal].add('')
                            changed = True
                        continue
                    
                    curr_symbol = production[0]
                    if curr_symbol in self.terminals:
                        if curr_symbol not in first[non_terminal]:
                            first[non_terminal].add(curr_symbol)
                            changed = True
                    elif curr_symbol in self.non_terminals:
                        first_of_curr = first[curr_symbol] - {''}
                        if not first_of_curr.issubset(first[non_terminal]):
                            first[non_terminal].update(first_of_curr)
                            changed = True
                        i = 0
                        epsilon_in_all = True
                        while i < len(production) and epsilon_in_all:
                            curr_symbol = production[i]
                            if curr_symbol in self.terminals:
                                if curr_symbol not in first[non_terminal]:
                                    first[non_terminal].add(curr_symbol)
                                    changed = True
                                epsilon_in_all = False
                            elif curr_symbol in self.non_terminals:
                                first_of_curr = first[curr_symbol] - {''}
                                if not first_of_curr.issubset(first[non_terminal]):
                                    first[non_terminal].update(first_of_curr)
                                    changed = True
                                if '' not in first[curr_symbol]:
                                    epsilon_in_all = False
                            i += 1
                        if epsilon_in_all and '' not in first[non_terminal]:
                            first[non_terminal].add('')
                            changed = True
        return first

    def compute_follow_sets(self):
        follow = {nt: set() for nt in self.non_terminals}
        start_symbol = list(self.grammar.keys())[0]
        follow[start_symbol].add('#')
        
        changed = True
        while changed:
            changed = False
            for non_terminal, productions in self.grammar.items():
                for production in productions:
                    for i, symbol in enumerate(production):
                        if symbol not in self.non_terminals:
                            continue
                        if i == len(production) - 1:
                            if not follow[non_terminal].issubset(follow[symbol]):
                                old_len = len(follow[symbol])
                                follow[symbol].update(follow[non_terminal])
                                if len(follow[symbol]) > old_len:
                                    changed = True
                        else:
                            next_symbol = production[i+1]
                            if next_symbol in self.terminals:
                                if next_symbol not in follow[symbol]:
                                    follow[symbol].add(next_symbol)
                                    changed = True
                            elif next_symbol in self.non_terminals:
                                first_of_next = self.first_sets[next_symbol] - {''}
                                if not first_of_next.issubset(follow[symbol]):
                                    old_len = len(follow[symbol])
                                    follow[symbol].update(first_of_next)
                                    if len(follow[symbol]) > old_len:
                                        changed = True
                                if '' in self.first_sets[next_symbol]:
                                    if not follow[non_terminal].issubset(follow[symbol]):
                                        old_len = len(follow[symbol])
                                        follow[symbol].update(follow[non_terminal])
                                        if len(follow[symbol]) > old_len:
                                            changed = True
                            j = i + 1
                            while j < len(production):
                                curr = production[j]
                                if curr in self.terminals:
                                    break
                                if curr in self.non_terminals and '' in self.first_sets[curr]:
                                    j += 1
                                    if j == len(production):
                                        if not follow[non_terminal].issubset(follow[symbol]):
                                            old_len = len(follow[symbol])
                                            follow[symbol].update(follow[non_terminal])
                                            if len(follow[symbol]) > old_len:
                                                changed = True
                                    elif production[j] in self.terminals:
                                        if production[j] not in follow[symbol]:
                                            follow[symbol].add(production[j])
                                            changed = True
                                    elif production[j] in self.non_terminals:
                                        first_of_next = self.first_sets[production[j]] - {''}
                                        if not first_of_next.issubset(follow[symbol]):
                                            old_len = len(follow[symbol])
                                            follow[symbol].update(first_of_next)
                                            if len(follow[symbol]) > old_len:
                                                changed = True
                                else:
                                    break
        return follow

    def first_of_sequence(self, sequence):
        if not sequence:
            return {''}
        first_set = set()
        i = 0
        epsilon_in_all = True
        while i < len(sequence) and epsilon_in_all:
            symbol = sequence[i]
            if symbol in self.terminals:
                first_set.add(symbol)
                epsilon_in_all = False
            elif symbol in self.non_terminals:
                first_set.update(self.first_sets[symbol] - {''})
                if '' not in self.first_sets[symbol]:
                    epsilon_in_all = False
            i += 1
        if epsilon_in_all:
            first_set.add('')
        return first_set

    def closure(self, items):
        closure_items = set(items)
        changed = True
        while changed:
            changed = False  # Fix: Corrected 'False36' to 'False'
            for item in list(closure_items):
                non_terminal, production, lookahead = item
                dot_index = production.index('.') if '.' in production else len(production)
                if dot_index < len(production) - 1:
                    next_symbol = production[dot_index + 1]
                    if next_symbol in self.non_terminals:
                        beta = production[dot_index + 2:] if dot_index + 2 < len(production) else ()
                        remainder = beta + (lookahead,) if lookahead else beta
                        first_of_remainder = self.first_of_sequence(remainder)
                        if '' in first_of_remainder:
                            first_of_remainder.remove('')  # Fix: Corrected syntax error
                            first_of_remainder.add(lookahead)
                        for production_of_next in self.grammar.get(next_symbol, []):
                            for la in first_of_remainder:
                                new_item = (next_symbol, ('.',) + production_of_next, la)
                                if new_item not in closure_items:
                                    closure_items.add(new_item)
                                    changed = True
        return frozenset(closure_items)

    def goto(self, items, symbol):
        goto_items = set()
        for item in items:
            non_terminal, production, lookahead = item
            dot_index = production.index('.') if '.' in production else len(production)
            if dot_index < len(production) - 1 and production[dot_index + 1] == symbol:
                new_production = production[:dot_index] + (symbol, '.') + production[dot_index + 2:]
                goto_items.add((non_terminal, new_production, lookahead))
        return self.closure(goto_items) if goto_items else frozenset()

    def compute_closure_goto(self):
        self.states = []
        self.transitions = {}
        all_symbols = sorted(set(
            [symbol for non_terminal in self.grammar for production in self.grammar[non_terminal] for symbol in production]
        ))
        start_symbol = list(self.grammar.keys())[0]
        initial_item = (start_symbol, ('.',) + self.grammar[start_symbol][0], '#')
        initial_state = self.closure({initial_item})
        self.states.append(initial_state)
        queue = [initial_state]
        while queue:
            current_state = queue.pop(0)
            for symbol in all_symbols:
                goto_state = self.goto(current_state, symbol)
                if goto_state:
                    if goto_state not in self.states:
                        self.states.append(goto_state)
                        queue.append(goto_state)
                    self.transitions[(self.states.index(current_state), symbol)] = self.states.index(goto_state)

    def build_parsing_table(self):
        self.action = {}
        self.goto_table = {}
        start_symbol = list(self.grammar.keys())[0]  # S'
        original_start_symbol = self.grammar[start_symbol][0][0]  # S
        
        for i, state in enumerate(self.states):
            for item in state:
                non_terminal, production, lookahead = item
                dot_index = production.index('.') if '.' in production else len(production)
                
                # Shift action
                if dot_index < len(production) - 1:
                    next_symbol = production[dot_index + 1]
                    if next_symbol in self.terminals:
                        if (i, next_symbol) in self.transitions:
                            next_state = self.transitions[(i, next_symbol)]
                            self.action[(i, next_symbol)] = f'S{next_state}'
                
                # Reduce or Accept action
                elif dot_index == len(production) - 1:
                    # Accept: [S' -> S., #]
                    if non_terminal == start_symbol and production == (original_start_symbol, '.') and lookahead == '#':
                        self.action[(i, '#')] = 'acc'
                    else:
                        # Reduce
                        prod_without_dot = production[:dot_index] + production[dot_index+1:]
                        prod_index = self.get_production_index(non_terminal, prod_without_dot)
                        if prod_index is not None:
                            self.action[(i, lookahead)] = f'r{prod_index}'
            
            # Build GOTO table
            for non_terminal in self.non_terminals:
                if (i, non_terminal) in self.transitions:
                    self.goto_table[(i, non_terminal)] = self.transitions[(i, non_terminal)]

    def get_production_index(self, non_terminal, production):
        index = 0
        for nt in self.grammar:
            for prod in self.grammar[nt]:
                if nt == non_terminal and prod == production:
                    return index
                index += 1
        return None

    def print_states(self):
        print("CLR(1) Parsing States:")
        for i, state in enumerate(self.states):
            print(f"State {i}:")
            for item in state:
                non_terminal, production, lookahead = item
                prod_str = ' '.join(production).replace(' . ', '.') if production else 'ε'
                print(f"  [{non_terminal} -> {prod_str}, {lookahead}]")
            print()

    def print_table(self):
        if not hasattr(self, 'action'):
            self.build_parsing_table()
        terminals = sorted(self.terminals)  # Sort terminals directly
        terminals.append('#')  # Append the end marker
        non_terminals = sorted(self.non_terminals)
        print("\nCLR(1) Parsing Table:")
        header = "State"
        for terminal in terminals:
            header += f" | {terminal:^8}"
        for non_terminal in non_terminals:
            header += f" | {non_terminal:^8}"
        print(header)
        print("-" * len(header))
        for i in range(len(self.states)):
            row = f"{i:^5}"
            for terminal in terminals:
                if (i, terminal) in self.action:
                    row += f" | {self.action[(i, terminal)]:^8}"
                else:
                    row += f" | {' ':^8}"
            for non_terminal in non_terminals:
                if (i, non_terminal) in self.goto_table:
                    row += f" | {self.goto_table[(i, non_terminal)]:^8}"
                else:
                    row += f" | {' ':^8}"
            print(row)
        print("-" * len(header))

    def parse_string(self, input_string):
        if not hasattr(self, 'action'):
            self.build_parsing_table()
        input_string += '#'
        state_stack = [0]
        symbol_stack = ['#']
        input_index = 0
        step = 1
        start_symbol = list(self.grammar.keys())[0]  # S'
        
        while True:
            current_state = state_stack[-1]
            current_symbol = input_string[input_index]
            print(f"Step {step:<4} | State Stack: {str(state_stack):<20} | Symbol Stack: {str(symbol_stack):<30} | "
                  f"Input: {input_string[input_index:]:<15} | ", end="")
            
            if (current_state, current_symbol) not in self.action:
                print(f"ERROR: No action defined for state {current_state} and symbol '{current_symbol}'")
                return False
            
            action = self.action[(current_state, current_symbol)]
            print(f"ACTION: {action:<10} | ", end="")
            
            if action.startswith('S'):
                next_state = int(action[1:])
                state_stack.append(next_state)
                symbol_stack.append(current_symbol)
                input_index += 1
                print("SHIFT")
            elif action.startswith('r'):
                production_index = int(action[1:])
                non_terminal = self.get_non_terminal_by_index(production_index)
                production = self.get_production_by_index(production_index)
                for _ in range(len(production)):
                    state_stack.pop()
                    symbol_stack.pop()
                symbol_stack.append(non_terminal)
                # Check if we've reduced to the start symbol and the stack is in accept state
                if non_terminal == start_symbol and symbol_stack == ['#', non_terminal] and input_string[input_index:] == '#':
                    print("ACCEPT")
                    return True
                goto_state = self.goto_table.get((state_stack[-1], non_terminal))
                if goto_state is None:
                    print(f"ERROR: No GOTO defined for state {state_stack[-1]} and non-terminal {non_terminal}")
                    return False
                state_stack.append(goto_state)
                print(f"REDUCE by {non_terminal} -> {''.join(production)}")
            elif action == 'acc':
                print("ACCEPT")
                return True
            step += 1

    def get_non_terminal_by_index(self, index):
        current_index = 0
        for non_terminal in self.grammar:
            for production in self.grammar[non_terminal]:
                if current_index == index:
                    return non_terminal
                current_index += 1
        return None

    def get_production_by_index(self, index):
        current_index = 0
        for non_terminal in self.grammar:
            for production in self.grammar[non_terminal]:
                if current_index == index:
                    return production
                current_index += 1
        return None


    def draw_dfa(self, output_file='dfa_diagram'):
        """Generate and render the DFA diagram of parser states using Graphviz"""
        from graphviz import Digraph
        dot = Digraph(comment='Parser DFA')
        dot.attr(rankdir='LR', size='10,8')
        dot.attr('node', shape='ellipse', fontsize='10')

        # Add states with item sets as labels
        for i, state in enumerate(self.states):
            label = f'I{i}\\n'
            for item in sorted(state):
                if len(item) == 2:
                    lhs, rhs = item
                    rhs_str = ' '.join(rhs).replace(' .', '•').replace('.', '•')
                    label += f'{lhs} → {rhs_str}\\n'
                elif len(item) == 3:
                    lhs, rhs, lookahead = item
                    rhs_str = ' '.join(rhs).replace(' .', '•').replace('.', '•')
                    label += f'{lhs} → {rhs_str}, {lookahead}\\n'
            dot.node(str(i), label)

        for (from_state, symbol), to_state in self.transitions.items():
            if isinstance(from_state, int):
                dot.edge(str(from_state), str(to_state), label=symbol)
            else:
                from_index = self.states.index(from_state)
                to_index = self.states.index(to_state)
                dot.edge(str(from_index), str(to_index), label=symbol)

        dot.render(output_file, format='pdf', view=True)
        print(f"DFA diagram saved as {output_file}.pdf")

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw()
    info_message = """
    Example grammar format:
    E -> aA
    E -> bB
    A -> cA
    A -> d
    B -> cB
    B -> d
    """
    messagebox.showinfo("Info", info_message)
    grammar_file_path = filedialog.askopenfilename(
        title="Select Grammar File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )
    if not grammar_file_path:  # Fix: Add check for empty file path
        print("No file selected. Exiting.")
        exit(1)
   
    grammar = ReadGrammar(grammar_file_path)
    parser = CLR1Parser(grammar)
    
    while True:
        print("\nChoose an option:")
        print("1. View states")
        print("2. View parsing table")
        print("3. Parse string")
        print("4. Exit")
        print("5. Generate DFA diagram")
        
        choice = input("Enter your choice (1-5): ")
        
        if choice == '1':
            parser.print_states()
        elif choice == '2':
            print("-------------------------------")
            parser.print_table()
            print("-------------------------------")
        elif choice == '3':
            input_string = input("Enter the string to parse: ")
            result = parser.parse_string(input_string)
            if result:
                print(f'The input string: "{input_string}" belongs to the grammar.')
            else:
                print(f'The input string: "{input_string}" does NOT belong to the grammar.')
        elif choice == '4':
            print("Exiting successfully.")
            break
        elif choice == '5':
            parser.draw_dfa()
        else:
            print("Invalid choice!")

