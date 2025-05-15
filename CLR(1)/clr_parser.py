import tkinter as tk
from tkinter import filedialog, messagebox
from read_grammar_clr_temp import ReadGrammar


class CLR1Parser:
    def __init__(self, grammar):
        # Initialize CLR(1) parser with the given grammar
        self.grammar = grammar
        # Get all terminals, non-terminals, and compute first sets
        self.terminals = self.grammar.get_terminals()
        self.non_terminals = self.grammar.get_non_terminals()
        self.first_sets = self.compute_first_sets()
        # Compute follow sets for all non-terminals
        self.follow_sets = self.compute_follow_sets()
        # Compute closures and transitions
        self.compute_closure_goto()

    def compute_first_sets(self):
        """
        Compute FIRST sets for all grammar symbols
        """
        first = {symbol: set() for symbol in self.non_terminals}
        # For terminals, FIRST is just the terminal itself
        for terminal in self.terminals:
            first[terminal] = {terminal}
        
        changed = True
        while changed:
            changed = False
            for non_terminal, productions in self.grammar.items():
                for production in productions:
                    # If production is empty (epsilon), add epsilon to FIRST set
                    if not production:
                        if '' not in first[non_terminal]:
                            first[non_terminal].add('')
                            changed = True
                        continue
                    
                    # Get symbols from the production
                    curr_symbol = production[0]
                    
                    # If first symbol is a terminal, add it to FIRST
                    if curr_symbol in self.terminals:
                        if curr_symbol not in first[non_terminal]:
                            first[non_terminal].add(curr_symbol)
                            changed = True
                    
                    # If first symbol is a non-terminal
                    elif curr_symbol in self.non_terminals:
                        # Add all symbols from FIRST of the current symbol to FIRST of non_terminal
                        first_of_curr = first[curr_symbol] - {''}
                        if not first_of_curr.issubset(first[non_terminal]):
                            first[non_terminal].update(first_of_curr)
                            changed = True
                        
                        # Check if we need to compute FIRST for the next symbol
                        i = 0
                        epsilon_in_all = True
                        
                        while i < len(production) and epsilon_in_all:
                            curr_symbol = production[i]
                            # If terminal, add to FIRST and break
                            if curr_symbol in self.terminals:
                                if curr_symbol not in first[non_terminal]:
                                    first[non_terminal].add(curr_symbol)
                                    changed = True
                                epsilon_in_all = False
                            # If non-terminal, check if it can derive epsilon
                            elif curr_symbol in self.non_terminals:
                                first_of_curr = first[curr_symbol] - {''}
                                if not first_of_curr.issubset(first[non_terminal]):
                                    first[non_terminal].update(first_of_curr)
                                    changed = True
                                if '' not in first[curr_symbol]:
                                    epsilon_in_all = False
                            i += 1
                        
                        # If all symbols in the production can derive epsilon, add epsilon to FIRST
                        if epsilon_in_all and '' not in first[non_terminal]:
                            first[non_terminal].add('')
                            changed = True
        
        return first

    def compute_follow_sets(self):
        """
        Compute FOLLOW sets for all non-terminals in grammar
        """
        follow = {nt: set() for nt in self.non_terminals}
        
        # Add end marker to FOLLOW of start symbol
        start_symbol = list(self.grammar.keys())[0]
        follow[start_symbol].add('#')
        
        changed = True
        while changed:
            changed = False
            
            for non_terminal, productions in self.grammar.items():
                for production in productions:
                    for i, symbol in enumerate(production):
                        # We're only interested in non-terminals
                        if symbol not in self.non_terminals:
                            continue
                        
                        # Check if this is the last symbol
                        if i == len(production) - 1:
                            # Add FOLLOW of LHS to FOLLOW of current non-terminal
                            if not follow[non_terminal].issubset(follow[symbol]):
                                old_len = len(follow[symbol])
                                follow[symbol].update(follow[non_terminal])
                                if len(follow[symbol]) > old_len:
                                    changed = True
                        else:
                            # Get next symbol
                            next_symbol = production[i+1]
                            
                            # If next symbol is terminal, add it to FOLLOW
                            if next_symbol in self.terminals:
                                if next_symbol not in follow[symbol]:
                                    follow[symbol].add(next_symbol)
                                    changed = True
                            
                            # If next symbol is non-terminal
                            elif next_symbol in self.non_terminals:
                                # Add FIRST of next symbol (except epsilon) to FOLLOW of current symbol
                                first_of_next = self.first_sets[next_symbol] - {''}
                                if not first_of_next.issubset(follow[symbol]):
                                    old_len = len(follow[symbol])
                                    follow[symbol].update(first_of_next)
                                    if len(follow[symbol]) > old_len:
                                        changed = True
                                
                                # If epsilon in FIRST of next, add FOLLOW of LHS to FOLLOW of current
                                if '' in self.first_sets[next_symbol]:
                                    if not follow[non_terminal].issubset(follow[symbol]):
                                        old_len = len(follow[symbol])
                                        follow[symbol].update(follow[non_terminal])
                                        if len(follow[symbol]) > old_len:
                                            changed = True
                            
                            # Check remaining symbols
                            j = i + 1
                            while j < len(production):
                                curr = production[j]
                                
                                # If terminal, break
                                if curr in self.terminals:
                                    break
                                
                                # If current can derive epsilon, check next symbol
                                if curr in self.non_terminals and '' in self.first_sets[curr]:
                                    j += 1
                                    # If end of production, add FOLLOW of LHS
                                    if j == len(production):
                                        if not follow[non_terminal].issubset(follow[symbol]):
                                            old_len = len(follow[symbol])
                                            follow[symbol].update(follow[non_terminal])
                                            if len(follow[symbol]) > old_len:
                                                changed = True
                                    # If next is terminal, add it
                                    elif production[j] in self.terminals:
                                        if production[j] not in follow[symbol]:
                                            follow[symbol].add(production[j])
                                            changed = True
                                    # If next is non-terminal, add its FIRST (without epsilon)
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
        """
        Compute FIRST set of a sequence of symbols
        """
        if not sequence:
            return {''}
        
        first_set = set()
        i = 0
        epsilon_in_all = True
        
        while i < len(sequence) and epsilon_in_all:
            symbol = sequence[i]
            # If terminal, add to FIRST and break
            if symbol in self.terminals:
                first_set.add(symbol)
                epsilon_in_all = False
            # If non-terminal, add its FIRST set (except epsilon)
            elif symbol in self.non_terminals:
                first_set.update(self.first_sets[symbol] - {''})
                if '' not in self.first_sets[symbol]:
                    epsilon_in_all = False
            i += 1
        
        # If all symbols can derive epsilon, add epsilon to FIRST
        if epsilon_in_all:
            first_set.add('')
        
        return first_set

    def closure(self, items):
        """
        Compute the closure of a set of CLR(1) items
        Each item is of the form (non_terminal, (production with dot), lookahead)
        """
        closure_items = set(items)
        changed = True

        while changed:
            changed = False
            for item in list(closure_items):
                non_terminal, production, lookahead = item
                
                # Find position of dot
                dot_index = production.index('.') if '.' in production else len(production)
                
                # If dot is not at the end
                if dot_index < len(production) - 1:
                    next_symbol = production[dot_index + 1]
                    
                    # If next symbol is a non-terminal
                    if next_symbol in self.non_terminals:
                        # Calculate FIRST of remainder of the production and lookahead
                        beta = production[dot_index + 2:] if dot_index + 2 < len(production) else ()
                        
                        # Create remainder + lookahead sequence
                        remainder = beta + (lookahead,) if lookahead else beta
                        
                        # Compute FIRST of the remainder
                        first_of_remainder = self.first_of_sequence(remainder)
                        if '' in first_of_remainder:
                            first_of_remainder.remove('')
                            first_of_remainder.add(lookahead)
                        
                        # Add new items to closure
                        for production_of_next in self.grammar.get(next_symbol, []):
                            for la in first_of_remainder:
                                new_item = (next_symbol, ('.',) + production_of_next, la)
                                if new_item not in closure_items:
                                    closure_items.add(new_item)
                                    changed = True

        return frozenset(closure_items)

    def goto(self, items, symbol):
        """
        Compute GOTO function for CLR(1) parser
        """
        goto_items = set()

        for item in items:
            non_terminal, production, lookahead = item
            dot_index = production.index('.') if '.' in production else len(production)
            
            # If dot is not at the end and next symbol matches
            if dot_index < len(production) - 1 and production[dot_index + 1] == symbol:
                # Move dot one position to the right
                new_production = production[:dot_index] + (symbol, '.') + production[dot_index + 2:]
                goto_items.add((non_terminal, new_production, lookahead))

        return self.closure(goto_items) if goto_items else frozenset()

    def compute_closure_goto(self):
        """
        Compute all closure and GOTO sets in the CLR(1) item collection
        """
        self.states = []
        self.transitions = {}
        
        # Get all symbols from grammar
        all_symbols = sorted(set(
            [symbol for non_terminal in self.grammar for production in self.grammar[non_terminal] for symbol in production]
        ))
        
        # Initial item with end marker '#' as lookahead
        start_symbol = list(self.grammar.keys())[0]
        initial_item = (start_symbol, ('.',) + self.grammar[start_symbol][0], '#')
        
        # Compute closure of initial item
        initial_state = self.closure({initial_item})
        self.states.append(initial_state)
        
        # Process all states
        queue = [initial_state]
        
        while queue:
            current_state = queue.pop(0)
            
            for symbol in all_symbols:
                goto_state = self.goto(current_state, symbol)
                
                if goto_state:
                    # If goto state is new, add it to states
                    if goto_state not in self.states:
                        self.states.append(goto_state)
                        queue.append(goto_state)
                    
                    # Record transition
                    self.transitions[(self.states.index(current_state), symbol)] = self.states.index(goto_state)

    def build_parsing_table(self):
        """
        Build CLR(1) parsing table
        """
        # Initialize action and goto tables
        self.action = {}
        self.goto_table = {}
        
        # Process each state
        for i, state in enumerate(self.states):
            for item in state:
                non_terminal, production, lookahead = item
                dot_index = production.index('.') if '.' in production else len(production)
                
                # Case 1: [A -> α.aβ, b] - Shift action
                if dot_index < len(production) - 1:
                    next_symbol = production[dot_index + 1]
                    if next_symbol in self.terminals:
                        if (i, next_symbol) in self.transitions:
                            next_state = self.transitions[(i, next_symbol)]
                            self.action[(i, next_symbol)] = f'S{next_state}'
                
                # Case 2: [A -> α., a] - Reduce action
                elif dot_index == len(production) - 1:
                    # Skip the augmented production for the accept action
                    if non_terminal == list(self.grammar.keys())[0] and production == ('.', list(self.grammar.keys())[1]):
                        self.action[(i, '#')] = 'acc'
                    else:
                        # Find production index for reduce action
                        prod_without_dot = production[:dot_index] + production[dot_index+1:]
                        prod_index = self.get_production_index(non_terminal, prod_without_dot)
                        
                        if prod_index is not None:
                            self.action[(i, lookahead)] = f'r{prod_index}'
                
                # Case 3: [S' -> S., #] - Accept action
                elif non_terminal == list(self.grammar.keys())[0] and production == (list(self.grammar.keys())[1], '.') and lookahead == '#':
                    self.action[(i, '#')] = 'acc'
            
            # Build GOTO table
            for non_terminal in self.non_terminals:
                if (i, non_terminal) in self.transitions:
                    self.goto_table[(i, non_terminal)] = self.transitions[(i, non_terminal)]

    def get_production_index(self, non_terminal, production):
        """
        Get the index of a production in the grammar
        """
        index = 0
        for nt in self.grammar:
            for prod in self.grammar[nt]:
                if nt == non_terminal and prod == production:
                    return index
                index += 1
        return None

    def print_states(self):
        """
        Print all CLR(1) parsing states
        """
        print("CLR(1) Parsing States:")
        for i, state in enumerate(self.states):
            print(f"State {i}:")
            for item in state:
                non_terminal, production, lookahead = item
                prod_str = ' '.join(production).replace(' . ', '.') if production else 'ε'
                print(f"  [{non_terminal} -> {prod_str}, {lookahead}]")
            print()

    def print_table(self):
        """
        Print the CLR(1) parsing table
        """
        # Build parsing table if not already built
        if not hasattr(self, 'action'):
            self.build_parsing_table()
        
        # Get all terminals and non-terminals
        terminals = sorted(self.terminals)
        terminals.append('#')  # Add end marker
        non_terminals = sorted(self.non_terminals)
        
        # Print header
        print("\nCLR(1) Parsing Table:")
        header = "State"
        for terminal in terminals:
            header += f" | {terminal:^8}"
        for non_terminal in non_terminals:
            header += f" | {non_terminal:^8}"
        print(header)
        print("-" * len(header))
        
        # Print rows
        for i in range(len(self.states)):
            row = f"{i:^5}"
            
            # Print ACTION part
            for terminal in terminals:
                if (i, terminal) in self.action:
                    row += f" | {self.action[(i, terminal)]:^8}"
                else:
                    row += f" | {' ':^8}"
            
            # Print GOTO part
            for non_terminal in non_terminals:
                if (i, non_terminal) in self.goto_table:
                    row += f" | {self.goto_table[(i, non_terminal)]:^8}"
                else:
                    row += f" | {' ':^8}"
            
            print(row)
        
        print("-" * len(header))

    def parse_string(self, input_string):
        """
        Parse an input string using the CLR(1) parsing table
        """
        # Build parsing table if not already built
        if not hasattr(self, 'action'):
            self.build_parsing_table()
        
        # Add end marker to input
        input_string += '#'
        
        # Initialize stacks
        state_stack = [0]  # Stack of states
        symbol_stack = ['#']  # Stack of symbols
        input_index = 0  # Current position in input
        step = 1  # Step counter
        
        while True:
            # Get current state and input symbol
            current_state = state_stack[-1]
            current_symbol = input_string[input_index]
            
            # Print current configuration
            print(f"Step {step:<4} | State Stack: {str(state_stack):<20} | Symbol Stack: {str(symbol_stack):<30} | "
                  f"Input: {input_string[input_index:]:<15} | ", end="")
            
            # Get action
            if (current_state, current_symbol) not in self.action:
                print(f"ERROR: No action defined for state {current_state} and symbol '{current_symbol}'")
                return False
            
            action = self.action[(current_state, current_symbol)]
            print(f"ACTION: {action:<10} | ", end="")
            
            # Process action
            if action.startswith('S'):  # Shift
                next_state = int(action[1:])
                state_stack.append(next_state)
                symbol_stack.append(current_symbol)
                input_index += 1
                print("SHIFT")
            
            elif action.startswith('r'):  # Reduce
                production_index = int(action[1:])
                non_terminal = self.get_non_terminal_by_index(production_index)
                production = self.get_production_by_index(production_index)
                
                # Pop states and symbols from stack
                for _ in range(len(production)):
                    state_stack.pop()
                    symbol_stack.pop()
                
                # Push the LHS non-terminal
                symbol_stack.append(non_terminal)
                
                # Get next state from GOTO table
                goto_state = self.goto_table.get((state_stack[-1], non_terminal))
                if goto_state is None:
                    print(f"ERROR: No GOTO defined for state {state_stack[-1]} and non-terminal {non_terminal}")
                    return False
                
                state_stack.append(goto_state)
                print(f"REDUCE by {non_terminal} -> {''.join(production)}")
            
            elif action == 'acc':  # Accept
                print("ACCEPT")
                return True
            
            step += 1

    def get_non_terminal_by_index(self, index):
        """
        Get the non-terminal of a production by its index
        """
        current_index = 0
        for non_terminal in self.grammar:
            for production in self.grammar[non_terminal]:
                if current_index == index:
                    return non_terminal
                current_index += 1
        return None

    def get_production_by_index(self, index):
        """
        Get a production by its index
        """
        current_index = 0
        for non_terminal in self.grammar:
            for production in self.grammar[non_terminal]:
                if current_index == index:
                    return production
                current_index += 1
        return None


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

    if grammar_file_path:
        # Read grammar and create parser
        grammar = ReadGrammar(grammar_file_path)
        clr1_parser = CLR1Parser(grammar)

        while True:
            print("\nChoose an option:")
            print("1. View states")
            print("2. View parsing table")
            print("3. Parse string")
            print("4. Exit")

            choice = input("Enter your choice (1-4): ")

            if choice == '1':
                clr1_parser.print_states()
            elif choice == '2':
                print("-------------------------------")
                clr1_parser.print_table()
                print("-------------------------------")
            elif choice == '3':
                input_string = input("Enter the string to parse: ")
                result = clr1_parser.parse_string(input_string)
                if result:
                    print(f'The input string: "{input_string}" belongs to the grammar.')
                else:
                    print(f'The input string: "{input_string}" does NOT belong to the grammar.')
            elif choice == '4':
                print("Exiting successfully.")
                break
            else:
                print("Invalid choice!")