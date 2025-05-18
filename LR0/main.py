import tkinter as tk
from tkinter import filedialog, messagebox
from LR0.read_grammar import ReadGrammar
import csv

class LR0Parser:
    def __init__(self, grammar):
        # Initialize LR(0) parser with the given grammar
        self.grammar = grammar
        # Compute closures and transitions
        self.compute_closure_goto()

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
        Compute all closure and GOTO sets in the LR(0) item collection
        :return:
        '''

        self.states = []
        self.transitions = {}

        all_symbols = sorted(set(
            symbol for production_list in self.grammar.values() for production in production_list for symbol in production))

        # initial_item = ('S', ('.', 'E'))
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

    def is_reduce_state(self, state):
        '''
        Check if the state is a reduce state
        '''
        for item in state:
            dot_index = item[1].index('.') if '.' in item[1] else len(item[1])
            if dot_index < len(item[1]) - 1:
                return False
        return True


    def get_reduce_production_index(self, state):
        '''
        Get the (index, production) of the reduction
        '''
        index = 0
        for item in state:
            dot_index = item[1].index('.') if '.' in item[1] else len(item[1])
            if dot_index == len(item[1]) - 1:
                lhs = item[0]
                rhs = item[1][:dot_index]
                for head, productions in self.grammar.items():
                    for prod in productions:
                        if head == lhs and prod == rhs:
                            return index, (lhs, rhs)
                        index += 1

    def print_states(self):
        '''
        Print all state sets
        '''
        print("LR(0) Parsing States:")
        for i, state in enumerate(self.states):
            print(f"State {i}: {state}")

    # def print_table(self):
        '''
        Print the LR(0) parsing table
        '''
        all_symbols = sorted(set(
            symbol for production_list in self.grammar.values() for production in production_list for symbol in production))

        uppercase_symbols = sorted(set(symbol for symbol in all_symbols if symbol.isupper()))
        lowercase_symbols = sorted(set(symbol for symbol in all_symbols if symbol.islower()))
        lowercase_symbols.append('#')

        all_sorted_symbols = lowercase_symbols + uppercase_symbols
        self.states_table = [[''] * (len(self.states) + 10) for _ in range(len(all_symbols) + 10)]

        self.states_table[0][0] = 'states'

        for row in range(len(self.states)):
            self.states_table[row + 1][0] = row

        for col, symbol in enumerate(all_sorted_symbols, start=1):
            self.states_table[0][col] = symbol

        for row in range(1, len(self.states) + 1):
            for col in range(1, len(all_sorted_symbols) + 1):
                current_states = self.states_table[row][0]
                current_symbol = self.states_table[0][col]

                if self.is_reduce_state(self.states[current_states]):
                    production_index = self.get_reduce_production_index(self.states[current_states])
                    if production_index == 0:
                        cell_value = 'acc' if current_symbol == '#' else ''
                    else:
                        cell_value = 'r' + str(production_index) if current_symbol in lowercase_symbols else ''
                else:
                    goto_state = self.goto(self.states[current_states], current_symbol)
                    if goto_state:
                        goto_index = self.states.index(goto_state)
                        cell_value = 'S' + str(goto_index) if current_symbol.islower() else str(goto_index)
                    else:
                        cell_value = ''
                self.states_table[row][col] = cell_value

        for row in range(len(self.states) + 1):
            for col in range(len(all_sorted_symbols) + 1):
                print(f"{self.states_table[row][col]:<10}", end='|')
            print()
    def print_table(self):
        '''
        Print the LR(0) parsing table
        '''
        # Get all symbols from grammar
        all_symbols = set()
        for production_list in self.grammar.values():
            for production in production_list:
                for symbol in production:
                    all_symbols.add(symbol)
        
        # Separate terminals and non-terminals
        non_terminals = set(self.grammar.keys())
        all_symbols = set()
        for prods in self.grammar.values():
            for prod in prods:
                for sym in prod:
                    all_symbols.add(sym)

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
            for symbol in all_sorted_symbols:
                col = all_sorted_symbols.index(symbol) + 1
                row = state_index + 1
                
                if self.is_reduce_state(self.states[state_index]):
                    # production_index = self.get_reduce_production_index(self.states[state_index])
                    production_index, _ = self.get_reduce_production_index(self.states[state_index])

                    if production_index == 0:
                        cell_value = 'acc' if symbol == '#' else ''
                    else:
                        cell_value = 'r' + str(production_index) if symbol in terminals else ''
                else:
                    goto_state = self.goto(self.states[state_index], symbol)
                    if goto_state:
                        goto_index = self.states.index(goto_state)
                        cell_value = 'S' + str(goto_index) if symbol in terminals else str(goto_index)
                    else:
                        cell_value = ''
                
                self.states_table[row][col] = cell_value
        
        # Print the table
        for row in range(len(self.states_table)):
            for col in range(len(self.states_table[row])):
                print(f"{self.states_table[row][col]:<10}", end='|')
            print()
    # def parse_string(self, input_string):
        # '''
        # Use LR(0) parsing table to parse a string
        # '''
        # input_string += '#'
        # states_stack = [0]
        # symbol_stack = ['#']
        # input_index = 0
        # step = 1
        # goto_state = ''

        # while True:
        #     current_state = states_stack[-1]
        #     current_symbol = input_string[input_index]

        #     action = self.get_action(current_state, current_symbol)

        #     print(f"Step {step:<4} | State Stack: {str(states_stack):<20} | Symbol Stack: {str(symbol_stack):<30} | "
        #           f"Input: {input_string[input_index:]:<15} | "
        #           f"ACTION: {action:<10} | ", end="")

        #     if not action:
        #         return False

        #     if action.startswith('S'):
        #         next_state = int(action[1:])
        #         states_stack.append(next_state)
        #         symbol_stack += input_string[input_index]
        #         input_index += 1
        #         print("GOTO: ")

        #     elif action.startswith('r'):
        #         production_index = int(action[1:])
        #         production = self.get_production_by_index(production_index)

        #         for _ in range(len(production[1])):
        #             states_stack.pop()
        #             symbol_stack.pop()

        #         goto_state = self.get_action(states_stack[-1], production[0])
        #         states_stack.append(goto_state)
        #         symbol_stack.append(production[0])
        #         print(f"GOTO: {goto_state}")

        #     elif action == 'acc':
        #         print("GOTO: ")
        #         return True

        #     step += 1
    
    def parse_string(self, input_string):
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
    
    # def get_action(self, state, symbol):
    #     '''
    #     Get ACTION based on state and symbol
    #     '''
    #     symbol_index = self.states_table[0].index(symbol)
    #     state_index = int(state) + 1
    #     return self.states_table[state_index][symbol_index]

    def get_action(self, state, symbol):
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
        for left_symbol, productions in self.grammar.items():
            for index, production in enumerate(productions):
                if production_index == 0:
                    return left_symbol, production
                production_index -= 1
    def export_table_to_csv(self, filename="parsing_table.csv"):
        '''
        Export the parsing table to a CSV file
        '''
        if not hasattr(self, 'states_table'):
            print("Parsing table not generated yet. Please view it first using option 2.")
            return
        try:
            with open(filename, 'w', newline='') as csvfile:
                writer = csv.writer(csvfile)
                for row in self.states_table:
                    writer.writerow(row)
            print(f"Parsing table successfully exported to '{filename}'")
        except Exception as e:
            print(f"Failed to write to file: {e}")


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

    if(grammar_file_path):
        grammar = ReadGrammar(grammar_file_path)
        lr0_parser = LR0Parser(grammar)

    while True:
        print("\nChoose an option:")
        print("1. View states")
        print("2. View parsing table")
        print("3. Parse string")
        print("4. Exit")
        print("5. Export parsing table to CSV")

        choice = input("Enter your choice (1-4): ")

        if choice == '1':
            lr0_parser.print_states()
        elif choice == '2':
            print("-------------------------------")
            lr0_parser.print_table()
            print("-------------------------------")
        elif choice == '3':
            input_string = input("Enter the string to parse: ")
            result = lr0_parser.parse_string(input_string)
            if result:
                print(f'The input string: "{input_string}" belongs to the grammar.')
            else:
                print(f'The input string: "{input_string}" does NOT belong to the grammar.')
        elif choice == '4':
            print("Exiting successfully.")
            break
            elif choice == '5':
                filename = input("Enterfilename to save (e.g., parsing_table.csv): ").strip()
                if not filename: filename ="parsing_table.csv"lalr_parser.export_table_to_csv(filename)
        else:
            print("Invalid choice!")
