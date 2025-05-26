import re

class ReadGrammar(dict):
    def __init__(self, grammar_file_path):
        super().__init__()
        self.file_path = grammar_file_path
        self.translate()
        self.add_augmented_production()

    # def translate(self):
        # Read grammar rules from the file
        with open(self.file_path, 'r', encoding='utf-8') as file:
            rules = file.readlines()

        # Process each rule
        for rule in rules:
            # Use regex to match the left-hand side and right-hand side
            match = re.match(r'\s*(\w+)\s*->\s*(.+)\s*', rule)
            if match:
                left = match.group(1)
                right = match.group(2)

                # Add new non-terminal to the dictionary if not present
                if left not in self:
                    self[left] = []

                # Split the right-hand side into individual symbols and add as a tuple
                productions = [symbol for symbol in right]
                self[left].append(tuple(productions))
        print("\nprinting self\n")
        print(self)

    def translate(self):
        with open(self.file_path, 'r', encoding='utf-8') as file:
            rules = file.readlines()

        for rule in rules:
            match = re.match(r'\s*(\w+)\s*->\s*(.+)\s*', rule)
            if match:
                left = match.group(1)
                right = match.group(2).strip()
                
                if left not in self:
                    self[left] = []
                
                # Split right-hand side properly, handling spaces
                productions = right.split('|')
                for prod in productions:
                    prod = prod.strip()
                    if prod:
                        # Split into symbols, handling multi-character tokens
                        symbols = []
                        current = ''
                        for char in prod:
                            if char == ' ':
                                if current:
                                    symbols.append(current)
                                    current = ''
                            else:
                                current += char
                        if current:
                            symbols.append(current)
                        self[left].append(tuple(symbols))

    def add_augmented_production(self):
        # Get the original start symbol of the grammar
        original_start_symbol = list(self.keys())[0]

        # Create a new augmented start symbol
        new_start_symbol = 'S'

        # Create a new dictionary and add the augmented production
        new_dict = {new_start_symbol: [(original_start_symbol,)]}

        # Merge the original grammar into the new dictionary
        new_dict.update(self)

        # Replace the current dictionary with the new one
        self.clear()
        self.update(new_dict)

        # Return the new start symbol
        return new_start_symbol

if __name__ == '__main__':
    # Path to the grammar file
    grammar_file_path = 'src/grammar_2.txt'  # Unaugmented grammar file

    # Convert to dictionary format usable by the parser
    grammar_reader = ReadGrammar(grammar_file_path)

    print("Original Grammar:")
    print(grammar_reader)
