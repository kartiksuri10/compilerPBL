import tkinter as tk
from tkinter import filedialog, messagebox
from read_grammar_lalr_temp import ReadGrammar


class LALR1Parser:
    def __init__(self, grammar):
        # Initialize LALR(1) parser with the given grammar
        self.grammar = grammar
        self.terminals = set()
        self.non_terminals = set(self.grammar.keys())
        
        # Identify all terminals in the grammar
        for lhs, productions in self.grammar.items():
            for production in productions:
                for symbol in production:
                    if symbol not in self.non_terminals:
                        self.terminals.add(symbol)
        
        # Add end marker
        self.terminals.add('#')
        
        # Compute first and follow sets
        self.compute_first_sets()
        self.compute_follow_sets()
        
        # Compute LR(1) items
        self.compute_lr1_items()
        
        # Merge states to form LALR(1) states
        self.merge_lr1_states()

    def compute_first_sets(self):
        """Compute FIRST set for all symbols in the grammar"""
        self.first = {terminal: {terminal} for terminal in self.terminals}
        self.first.update({non_terminal: set() for non_terminal in self.non_terminals})
        
        changed = True
        while changed:
            changed = False
            for lhs, productions in self.grammar.items():
                for production in productions:
                    # Handle empty production (epsilon)
                    if not production:
                        if '' not in self.first[lhs]:
                            self.first[lhs].add('')
                            changed = True
                        continue
                    
                    # Add first symbol if it's a terminal
                    first_symbol = production[0]
                    if first_symbol in self.terminals:
                        if first_symbol not in self.first[lhs]:
                            self.first[lhs].add(first_symbol)
                            changed = True
                    else:  # first_symbol is a non-terminal
                        # Add all non-epsilon elements from first(first_symbol) to first(lhs)
                        for symbol in self.first[first_symbol] - {''}:
                            if symbol not in self.first[lhs]:
                                self.first[lhs].add(symbol)
                                changed = True
                        
                        # If epsilon is in first of current symbol, check the next symbol
                        if '' in self.first[first_symbol]:
                            i = 1
                            while i < len(production) and '' in self.first[production[i-1]]:
                                if production[i] in self.terminals:
                                    if production[i] not in self.first[lhs]:
                                        self.first[lhs].add(production[i])
                                        changed = True
                                    break
                                else:  # production[i] is a non-terminal
                                    for symbol in self.first[production[i]] - {''}:
                                        if symbol not in self.first[lhs]:
                                            self.first[lhs].add(symbol)
                                            changed = True
                                i += 1
                            
                            # If all symbols can derive epsilon, add epsilon to first(lhs)
                            if i == len(production) and all('' in self.first.get(symbol, set()) for symbol in production):
                                if '' not in self.first[lhs]:
                                    self.first[lhs].add('')
                                    changed = True

    def first_of_sequence(self, sequence):
        """Compute FIRST set for a sequence of symbols"""
        if not sequence:
            return {''}
        
        result = set()
        empty_in_all = True
        
        for symbol in sequence:
            if symbol in self.terminals:
                if empty_in_all:
                    result.add(symbol)
                    empty_in_all = False
                break
            else:  # symbol is a non-terminal
                symbol_first = self.first[symbol]
                result.update(symbol_first - {''})
                if '' not in symbol_first:
                    empty_in_all = False
                    break
        
        if empty_in_all:
            result.add('')
        
        return result

    def compute_follow_sets(self):
        """Compute FOLLOW set for all non-terminals in the grammar"""
        self.follow = {non_terminal: set() for non_terminal in self.non_terminals}
        
        # Add end marker to follow of start symbol
        start_symbol = next(iter(self.grammar))
        self.follow[start_symbol].add('#')
        
        changed = True
        while changed:
            changed = False
            for lhs, productions in self.grammar.items():
                for production in productions:
                    for i, symbol in enumerate(production):
                        if symbol in self.non_terminals:
                            # Get first of what follows this non-terminal
                            if i < len(production) - 1:
                                beta_first = self.first_of_sequence(production[i+1:])
                                
                                # Add all non-epsilon symbols from first(beta) to follow(symbol)
                                for terminal in beta_first - {''}:
                                    if terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True
                                
                                # If epsilon is in first(beta), add follow(lhs) to follow(symbol)
                                if '' in beta_first:
                                    for terminal in self.follow[lhs]:
                                        if terminal not in self.follow[symbol]:
                                            self.follow[symbol].add(terminal)
                                            changed = True
                            else:
                                # If symbol is at the end, add follow(lhs) to follow(symbol)
                                for terminal in self.follow[lhs]:
                                    if terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True

    def closure_lr1(self, items):
        """
        Compute closure of a set of LR(1) items
        Each item is in the form (lhs, production, dot_position, lookahead)
        """
        closure_set = set(items)
        changed = True
        
        while changed:
            changed = False
            for item in list(closure_set):
                lhs, prod, dot_pos, lookahead = item
                
                # If dot is not at the end
                if dot_pos < len(prod):
                    symbol_after_dot = prod[dot_pos]
                    
                    # If symbol after dot is a non-terminal
                    if symbol_after_dot in self.non_terminals:
                        # Compute first set of what follows the non-terminal plus lookahead
                        beta = prod[dot_pos+1:] if dot_pos+1 < len(prod) else tuple()
                        first_beta_lookahead = self.first_of_sequence(beta + (lookahead,))
                        
                        # Add new items to closure
                        for p_rhs in self.grammar[symbol_after_dot]:
                            for la in first_beta_lookahead:
                                new_item = (symbol_after_dot, p_rhs, 0, la)
                                if new_item not in closure_set:
                                    closure_set.add(new_item)
                                    changed = True
        
        return frozenset(closure_set)

    def goto_lr1(self, items, symbol):
        """
        Compute GOTO function for LR(1) items
        """
        goto_items = set()
        
        for item in items:
            lhs, prod, dot_pos, lookahead = item
            
            if dot_pos < len(prod) and prod[dot_pos] == symbol:
                new_item = (lhs, prod, dot_pos + 1, lookahead)
                goto_items.add(new_item)
        
        return self.closure_lr1(goto_items) if goto_items else frozenset()

    def compute_lr1_items(self):
        """Compute all LR(1) items"""
        self.lr1_states = []
        self.lr1_transitions = {}
        
        # Initial item with start symbol and end marker lookahead
        start_symbol = next(iter(self.grammar))
        initial_item = (start_symbol, self.grammar[start_symbol][0], 0, '#')
        
        initial_state = self.closure_lr1({initial_item})
        self.lr1_states.append(initial_state)
        
        queue = [initial_state]
        
        while queue:
            current_state = queue.pop(0)
            
            # All symbols in grammar
            all_symbols = self.terminals.union(self.non_terminals) - {''}
            
            for symbol in all_symbols:
                goto_state = self.goto_lr1(current_state, symbol)
                
                if goto_state and goto_state not in self.lr1_states:
                    self.lr1_states.append(goto_state)
                    queue.append(goto_state)
                
                if goto_state:
                    self.lr1_transitions[(self.lr1_states.index(current_state), symbol)] = self.lr1_states.index(goto_state)

    def merge_lr1_states(self):
        """Merge LR(1) states with same core to form LALR(1) states"""
        # Group states by their cores
        cores = {}
        for state_idx, state in enumerate(self.lr1_states):
            core_state = frozenset((lhs, prod, dot_pos) for lhs, prod, dot_pos, _ in state)
            if core_state not in cores:
                cores[core_state] = []
            cores[core_state].append(state_idx)
        
        # Create LALR(1) states by merging states with same core
        self.lalr_states = []
        self.lr1_to_lalr_map = {}
        
        for core, state_indices in cores.items():
            # Merge all states with this core
            merged_state = set()
            for state_idx in state_indices:
                for item in self.lr1_states[state_idx]:
                    lhs, prod, dot_pos, lookahead = item
                    merged_state.add((lhs, prod, dot_pos, lookahead))
            
            self.lalr_states.append(frozenset(merged_state))
            
            # Map all LR(1) states with this core to the merged LALR(1) state
            for state_idx in state_indices:
                self.lr1_to_lalr_map[state_idx] = len(self.lalr_states) - 1
        
        # Update transitions for LALR(1) states
        self.lalr_transitions = {}
        for (from_state, symbol), to_state in self.lr1_transitions.items():
            lalr_from = self.lr1_to_lalr_map[from_state]
            lalr_to = self.lr1_to_lalr_map[to_state]
            self.lalr_transitions[(lalr_from, symbol)] = lalr_to

    def print_states(self):
        """Print all LALR(1) states"""
        print("LALR(1) Parsing States:")
        for i, state in enumerate(self.lalr_states):
            print(f"State {i}:")
            for item in state:
                lhs, prod, dot_pos, lookahead = item
                # Format the production with the dot position
                prod_str = ' '.join(prod[:dot_pos]) + ' · ' + ' '.join(prod[dot_pos:])
                print(f"  {lhs} -> {prod_str}, {lookahead}")

    def print_table(self):
        """Print the LALR(1) parsing table"""
        # Sort terminals and non-terminals for better readability
        terminals = sorted(self.terminals)
        non_terminals = sorted(self.non_terminals)
        all_symbols = terminals + non_terminals
        
        # Initialize table
        self.states_table = [['' for _ in range(len(all_symbols) + 1)] for _ in range(len(self.lalr_states) + 1)]
        self.states_table[0][0] = 'states'
        
        # Fill header row
        for col, symbol in enumerate(all_symbols, start=1):
            self.states_table[0][col] = symbol
        
        # Fill state numbers
        for row in range(1, len(self.lalr_states) + 1):
            self.states_table[row][0] = row - 1
        
        # Fill table cells
        for state_idx, state in enumerate(self.lalr_states):
            # Check for reduce actions
            for item in state:
                lhs, prod, dot_pos, lookahead = item
                
                # If dot is at the end, it's a reduce action
                if dot_pos == len(prod):
                    # Find production index
                    prod_idx = -1
                    for head, productions in self.grammar.items():
                        for i, p in enumerate(productions):
                            if head == lhs and p == prod:
                                prod_idx = sum(len(self.grammar[h]) for h in list(self.grammar.keys())[:list(self.grammar.keys()).index(head)]) + i
                                break
                        if prod_idx != -1:
                            break
                    
                    # Accept if it's the augmented production
                    if lhs == next(iter(self.grammar)) and prod == self.grammar[lhs][0] and lookahead == '#':
                        col = all_symbols.index('#') + 1
                        self.states_table[state_idx + 1][col] = 'acc'
                    else:
                        # Reduce action
                        col = all_symbols.index(lookahead) + 1
                        # Only add reduce action if cell is empty or also a reduce action with higher index
                        if not self.states_table[state_idx + 1][col] or (self.states_table[state_idx + 1][col].startswith('r') and int(self.states_table[state_idx + 1][col][1:]) > prod_idx):
                            self.states_table[state_idx + 1][col] = f'r{prod_idx}'
            
            # Check for shift actions
            for symbol in terminals:
                if (state_idx, symbol) in self.lalr_transitions:
                    col = all_symbols.index(symbol) + 1
                    next_state = self.lalr_transitions[(state_idx, symbol)]
                    # Don't overwrite accept
                    if not self.states_table[state_idx + 1][col] or self.states_table[state_idx + 1][col] == 'acc':
                        self.states_table[state_idx + 1][col] = f'S{next_state}'
            
            # GOTO actions for non-terminals
            for symbol in non_terminals:
                if (state_idx, symbol) in self.lalr_transitions:
                    col = all_symbols.index(symbol) + 1
                    next_state = self.lalr_transitions[(state_idx, symbol)]
                    self.states_table[state_idx + 1][col] = f'{next_state}'
        
        # Print the table
        for row in range(len(self.states_table)):
            for col in range(len(self.states_table[row])):
                print(f"{self.states_table[row][col]:<10}", end='|')
            print()

    def get_action(self, state, symbol):
        """Get ACTION based on state and symbol"""
        try:
            symbol_index = self.states_table[0].index(symbol)
            state_index = state + 1
            return self.states_table[state_index][symbol_index]
        except ValueError:
            return None

    def get_production_by_index(self, production_index):
        """Get production by index"""
        index = 0
        for lhs, productions in self.grammar.items():
            for production in productions:
                if index == production_index:
                    return lhs, production
                index += 1
        return None

    def parse_string(self, input_string):
        """Parse a string using LALR(1) parsing table"""
        input_string += '#'
        states_stack = [0]
        symbol_stack = ['#']
        input_index = 0
        step = 1

        while True:
            current_state = states_stack[-1]
            current_symbol = input_string[input_index]

            print(f"Step {step:<4} | State Stack: {str(states_stack):<20} | Symbol Stack: {str(symbol_stack):<30} | "
                  f"Input: {input_string[input_index:]:<15} | ", end="")

            try:
                action = self.get_action(current_state, current_symbol)
            except ValueError:
                print(f"Error: Symbol '{current_symbol}' not in grammar")
                return False

            print(f"ACTION: {action:<10} | ", end="")

            if not action:
                print("No action defined for this state/symbol combination")
                return False

            if action.startswith('S'):
                next_state = int(action[1:])
                states_stack.append(next_state)
                symbol_stack.append(current_symbol)
                input_index += 1
                print("SHIFT")

            elif action.startswith('r'):
                production_index = int(action[1:])
                production = self.get_production_by_index(production_index)
                lhs = production[0]
                rhs_length = len(production[1])
                
                # Pop states and symbols
                for _ in range(rhs_length):
                    states_stack.pop()
                    symbol_stack.pop()
                
                # Get new state from GOTO table
                goto_state = self.get_action(states_stack[-1], lhs)
                if not goto_state:
                    print(f"No GOTO for state {states_stack[-1]} and symbol {lhs}")
                    return False
                
                states_stack.append(int(goto_state))
                symbol_stack.append(lhs)
                print(f"REDUCE by {production[0]}->{''.join(production[1])}")

            elif action == 'acc':
                print("ACCEPT")
                return True

            step += 1


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
        title="Select File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if grammar_file_path:
        grammar = ReadGrammar(grammar_file_path)
        lalr_parser = LALR1Parser(grammar)

    while True:
        print("\nChoose an option:")
        print("1. View states")
        print("2. View parsing table")
        print("3. Parse string")
        print("4. Exit")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            lalr_parser.print_states()
        elif choice == '2':
            print("-------------------------------")
            lalr_parser.print_table()
            print("-------------------------------")
        elif choice == '3':
            input_string = input("Enter the string to parse: ")
            result = lalr_parser.parse_string(input_string)
            if result:
                print(f'The input string: "{input_string}" belongs to the grammar.')
            else:
                print(f'The input string: "{input_string}" does NOT belong to the grammar.')
        elif choice == '4':
            print("Exiting successfully.")
            break
        else:
            print("Invalid choice!")