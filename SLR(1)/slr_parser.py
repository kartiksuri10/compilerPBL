import tkinter as tk
from tkinter import filedialog, messagebox
from read_grammar_slr_temp import ReadGrammar

class SLR1Parser:
    def __init__(self, grammar):
        # Initialize SLR(1) parser with the given grammar
        self.grammar = grammar
        # Compute first and follow sets
        self.compute_first_follow_sets()
        # Compute closures and transitions
        self.compute_closure_goto()
        # Generate the parsing table during initialization
        self.print_table()  # Ensures self.states_table is always created

    def compute_first_sets(self):
        '''
        Compute FIRST sets for all symbols in the grammar 
        '''
        self.first = {}
        
        # Initialize FIRST sets
        for non_terminal in self.grammar.keys():
            self.first[non_terminal] = set()
        
        # Iterate until no more changes
        changed = True
        while changed:
            changed = False
            
            for non_terminal, productions in self.grammar.items():
                for production in productions:
                    # If empty production, add epsilon to FIRST set
                    if len(production) == 0 or production[0] == 'ε':
                        if 'ε' not in self.first[non_terminal]:
                            self.first[non_terminal].add('ε')
                            changed = True
                    else:
                        # Get first symbol of the production
                        first_symbol = production[0]
                        
                        # If terminal, add to FIRST set
                        if first_symbol not in self.grammar:
                            if first_symbol not in self.first[non_terminal]:
                                self.first[non_terminal].add(first_symbol)
                                changed = True
                        else:
                            # If non-terminal, add its FIRST set (except epsilon)
                            for symbol in self.first.get(first_symbol, set()):
                                if symbol != 'ε' and symbol not in self.first[non_terminal]:
                                    self.first[non_terminal].add(symbol)
                                    changed = True
                            
                            # If epsilon in FIRST of first_symbol, check next symbol
                            if 'ε' in self.first.get(first_symbol, set()):
                                i = 1
                                all_derive_epsilon = True
                                
                                while i < len(production) and all_derive_epsilon:
                                    current_symbol = production[i]
                                    
                                    if current_symbol not in self.grammar:  # Terminal
                                        self.first[non_terminal].add(current_symbol)
                                        all_derive_epsilon = False
                                    else:  # Non-terminal
                                        for symbol in self.first.get(current_symbol, set()):
                                            if symbol != 'ε':
                                                self.first[non_terminal].add(symbol)
                                        
                                        if 'ε' not in self.first.get(current_symbol, set()):
                                            all_derive_epsilon = False
                                    
                                    i += 1
                                
                                # If all symbols can derive epsilon, add epsilon to FIRST
                                if all_derive_epsilon and 'ε' not in self.first[non_terminal]:
                                    self.first[non_terminal].add('ε')
                                    changed = True

    def compute_follow_sets(self):
        '''
        Compute FOLLOW sets for all non-terminals in the grammar
        '''
        self.follow = {}
        
        # Initialize FOLLOW sets
        for non_terminal in self.grammar.keys():
            self.follow[non_terminal] = set()
        
        # Add end marker to FOLLOW of start symbol
        start_symbol = list(self.grammar.keys())[0]
        self.follow[start_symbol].add('#')
        
        # Iterate until no more changes
        changed = True
        while changed:
            changed = False
            
            for non_terminal, productions in self.grammar.items():
                for production in productions:
                    for i, symbol in enumerate(production):
                        if symbol in self.grammar:  # If symbol is a non-terminal
                            # Case 1: A -> αBβ, add FIRST(β) - {ε} to FOLLOW(B)
                            if i < len(production) - 1:
                                beta = production[i+1:]
                                beta_first = self.compute_first_of_string(beta)
                                
                                for terminal in beta_first:
                                    if terminal != 'ε' and terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True
                            
                            # Case 2: A -> αB or A -> αBβ where β can derive ε
                            # Add FOLLOW(A) to FOLLOW(B)
                            if i == len(production) - 1 or 'ε' in self.compute_first_of_string(production[i+1:]):
                                for terminal in self.follow[non_terminal]:
                                    if terminal not in self.follow[symbol]:
                                        self.follow[symbol].add(terminal)
                                        changed = True

    def compute_first_of_string(self, symbols):
        '''
        Compute FIRST set for a string of symbols
        '''
        if not symbols:
            return {'ε'}
        
        first_set = set()
        all_derive_epsilon = True
        
        for symbol in symbols:
            if symbol not in self.grammar:  # Terminal
                first_set.add(symbol)
                all_derive_epsilon = False
                break
            else:  # Non-terminal
                for terminal in self.first.get(symbol, set()):
                    if terminal != 'ε':
                        first_set.add(terminal)
                
                if 'ε' not in self.first.get(symbol, set()):
                    all_derive_epsilon = False
                    break
        
        if all_derive_epsilon:
            first_set.add('ε')
        
        return first_set

    def compute_first_follow_sets(self):
        '''
        Compute both FIRST and FOLLOW sets
        '''
        self.compute_first_sets()
        self.compute_follow_sets()

    def closure(self, items):
        '''
        Compute the closure of a set of items
        :param items: current set of items
        :return:
        '''
        closure_items = set(items)
        changed = True

        while changed:
            changed = False
            for item in closure_items.copy():
                dot_index = item[1].index('.') if '.' in item[1] else len(item[1])

                if dot_index < len(item[1]) - 1:
                    next_symbol = item[1][dot_index + 1]

                    if next_symbol in self.grammar:
                        for production in self.grammar[next_symbol]:
                            new_item = (next_symbol, ('.',) + production)
                            if new_item not in closure_items:
                                closure_items.add(new_item)
                                changed = True

            for item in closure_items.copy():
                dot_index = item[1].index('.') if '.' in item[1] else len(item[1])
                if dot_index == len(item[1]) - 1:
                    if item not in closure_items:
                        closure_items.add(item)
                        changed = True

        return frozenset(sorted(closure_items))

    def goto(self, items, symbol):
        '''
        Compute GOTO function
        :param items: current set of items
        :param symbol: input symbol
        :return:
        '''
        goto_items = set()

        for item in items:
            dot_index = item[1].index('.') if '.' in item[1] else len(item[1])

            if dot_index < len(item[1]) - 1 and item[1][dot_index + 1] == symbol:
                new_item = (item[0], item[1][:dot_index] + (symbol, '.') + item[1][dot_index + 2:])
                goto_items.add(new_item)

        return self.closure(goto_items)

    def compute_closure_goto(self):
        '''
        Compute all closure and GOTO sets in the SLR(1) item collection
        :return:
        '''
        self.states = []
        self.transitions = {}

        all_symbols = sorted(set(
            symbol for production_list in self.grammar.values() for production in production_list for symbol in production))

        start_symbol = list(self.grammar.keys())[0]
        initial_item = (start_symbol, ('.',) + self.grammar[start_symbol][0])

        initial_state = self.closure({initial_item})
        self.states.append(initial_state)

        queue = [initial_state]

        while queue:
            current_state = queue.pop(0)

            for symbol in all_symbols:
                goto_items = self.goto(current_state, symbol)

                if goto_items:
                    closure_goto_items = self.closure(goto_items)

                    if closure_goto_items and closure_goto_items not in self.states:
                        self.states.append(closure_goto_items)
                        queue.append(closure_goto_items)

                    self.transitions[(current_state, symbol)] = closure_goto_items

    def is_reduce_state(self, state, symbol=None):
        '''
        Check if the state has a reduce action for the given symbol.
        For SLR(1), we need to check the FOLLOW set.
        '''
        for item in state:
            dot_index = item[1].index('.') if '.' in item[1] else len(item[1])
            
            # If dot is at the end, this could be a reduce state
            if dot_index == len(item[1]) - 1:
                # For SLR(1), we check if the input symbol is in FOLLOW(A) for item A -> α.
                if symbol is None or symbol in self.follow.get(item[0], set()):
                    return True
        return False

    def get_reduce_production_index(self, state, symbol):
        '''
        Get the (index, production) of the reduction
        For SLR(1), we only reduce if the symbol is in FOLLOW(A)
        '''
        index = 0
        for item in state:
            dot_index = item[1].index('.') if '.' in item[1] else len(item[1])
            if dot_index == len(item[1]) - 1:
                lhs = item[0]
                rhs = item[1][:dot_index]
                
                # For SLR(1), check if symbol is in FOLLOW(lhs)
                if symbol in self.follow.get(lhs, set()):
                    for head, productions in self.grammar.items():
                        for prod in productions:
                            if head == lhs and prod == rhs:
                                return index, (lhs, rhs)
                            index += 1
        
        return None, None

    def print_states(self):
        '''
        Print all state sets
        '''
        print("SLR(1) Parsing States:")
        for i, state in enumerate(self.states):
            print(f"State {i}: {state}")

    def print_table(self):
        '''
        Print the SLR(1) parsing table
        '''
        # Get all symbols from grammar
        all_symbols = set()
        for production_list in self.grammar.values():
            for production in production_list:
                for symbol in production:
                    all_symbols.add(symbol)
        
        # Separate terminals and non-terminals
        non_terminals = set(self.grammar.keys())
        terminals = all_symbols - non_terminals

        # Add end marker
        terminals.add('#')
        
        # Sort them
        terminals = sorted(terminals)
        non_terminals = sorted(non_terminals)
        
        # Combine them with terminals first
        all_sorted_symbols = terminals + non_terminals
        
        # Initialize table
        self.states_table = [[''] * (len(all_sorted_symbols) + 1) for _ in range(len(self.states) + 1)]
        self.states_table[0][0] = 'states'
        
        # Fill header row
        for col, symbol in enumerate(all_sorted_symbols, start=1):
            self.states_table[0][col] = symbol
        
        # Fill state numbers
        for row in range(1, len(self.states) + 1):
            self.states_table[row][0] = row - 1
        
        # Fill table cells
        for state_index in range(len(self.states)):
            for symbol_index, symbol in enumerate(all_sorted_symbols):
                col = symbol_index + 1
                row = state_index + 1
                
                # Handle terminals (ACTION table)
                if symbol in terminals:
                    # Check for shift action
                    if (self.states[state_index], symbol) in self.transitions:
                        next_state = self.states.index(self.transitions[(self.states[state_index], symbol)])
                        cell_value = f'S{next_state}'
                    
                    # Check for reduce action (SLR(1) checks FOLLOW sets)
                    elif self.is_reduce_state(self.states[state_index], symbol):
                        prod_index, prod = self.get_reduce_production_index(self.states[state_index], symbol)
                        if prod_index is not None:
                            if prod_index == 0 and symbol == '#':
                                cell_value = 'acc'
                            else:
                                cell_value = f'r{prod_index}'
                        else:
                            cell_value = ''
                    else:
                        cell_value = ''
                
                # Handle non-terminals (GOTO table)
                else:
                    if (self.states[state_index], symbol) in self.transitions:
                        next_state = self.states.index(self.transitions[(self.states[state_index], symbol)])
                        cell_value = str(next_state)
                    else:
                        cell_value = ''
                
                self.states_table[row][col] = cell_value
        
        # Print the table
        print("SLR(1) Parsing Table:")
        for row in range(len(self.states_table)):
            for col in range(len(self.states_table[row])):
                print(f"{self.states_table[row][col]:<10}", end='|')
            print()

    def get_action(self, state, symbol):
        '''
        Get ACTION based on state and symbol
        '''
        try:
            symbol_index = self.states_table[0].index(symbol)
            state_index = state + 1
            return self.states_table[state_index][symbol_index]
        except ValueError:
            return None

    def get_production_by_index(self, production_index):
        '''
        Get production by index
        '''
        index = 0
        for left_symbol, productions in self.grammar.items():
            for production in productions:
                if index == production_index:
                    return left_symbol, production
                index += 1
        return None, None

    def parse_string(self, input_string):
        '''
        Use SLR(1) parsing table to parse a string
        '''
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
                if production[0] is None:  # Check if production exists
                    print(f"Error: Invalid production index {production_index}")
                    return False
                lhs = production[0]
                rhs_length = len(production[1])
                
                # Pop states and symbols
                for _ in range(rhs_length):
                    states_stack.pop()
                    symbol_stack.pop()
                
                # Get new state from GOTO table
                goto_state = self.get_action(states_stack[-1], lhs)
                if not goto_state:
                    print(f"No GOTO for state {states_stack[-1]} and symbol wywo{lhs}")
                    return False
                
                states_stack.append(int(goto_state))
                symbol_stack.append(lhs)
                print(f"REDUCE by {production[0]}->{''.join(production[1])}")

            elif action == 'acc':
                print("ACCEPT")
                return True

            step += 1


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
        title="Select File",
        filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
    )

    if not grammar_file_path:
        print("No file selected. Exiting.")
        exit()

    try:
        grammar = ReadGrammar(grammar_file_path)
        parser = SLR1Parser(grammar)
    except Exception as e:
        print(f"Error loading grammar: {e}")
        exit()

    while True:
        print("\nChoose an option:")
        print("1. View states")
        print("2. View parsing table")
        print("3. Parse string")
        print("4. Exit")
        print("5. Generate DFA diagram")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            slr1_parser.print_states()
        elif choice == '2':
            print("-------------------------------")
            slr1_parser.print_table()
            print("-------------------------------")
        elif choice == '3':
            input_string = input("Enter the string to parse: ")
            result = slr1_parser.parse_string(input_string)
            if result:
                print(f'The input string: "{input_string}" belongs to the grammar.')
            else:
                print(f'The input string: "{input_string}" does NOT belong to the grammar.')
        elif choice == '5':
            parser.draw_dfa()
        elif choice == '4':
            print("Exiting successfully.")
            break
        else:
            print("Invalid choice!")