import re

class ReadGrammar(dict):
    def __init__(self, grammar_file_path):
        super().__init__()
        self.file_path = grammar_file_path
        self.translate()
        self.add_augmented_production()
    
    def translate(self):
        """
        Read grammar rules from file and convert them to dictionary format
        """
        with open(self.file_path, 'r', encoding='utf-8') as file:
            rules = file.readlines()
        
        for rule in rules:
            # Use regex to match the left-hand side and right-hand side
            match = re.match(r'\s*(\w+)\s*->\s*(.+)\s*', rule)
            if match:
                left = match.group(1)
                right = match.group(2).strip()
                
                if left not in self:
                    self[left] = []
                
                # Split right-hand side properly, handling multiple productions with '|'
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
                        
                        # Add the production to our dictionary
                        if tuple(symbols) not in self[left]:
                            self[left].append(tuple(symbols))
    
    def add_augmented_production(self):
        """
        Add an augmented production S' -> S to the grammar
        """
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
    
    def get_terminals(self):
        """
        Get all terminal symbols in the grammar
        """
        non_terminals = set(self.keys())
        all_symbols = set()
        
        for productions in self.values():
            for production in productions:
                for symbol in production:
                    all_symbols.add(symbol)
        
        terminals = all_symbols - non_terminals
        return terminals
    
    def get_non_terminals(self):
        """
        Get all non-terminal symbols in the grammar
        """
        return set(self.keys())

if __name__ == '__main__':
    # Path to the grammar file
    grammar_file_path = 'grammar.txt'
    
    # Convert to dictionary format usable by the parser
    grammar_reader = ReadGrammar(grammar_file_path)
    print("Grammar after augmentation:")
    print(grammar_reader)