import re

class ReadGrammar(dict):
    def __init__(self, grammar_file_path):
        super().__init__()
        self.file_path = grammar_file_path
        self.translate()
        self.add_augmented_production()

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
                
                productions = right.split('|')
                for prod in productions:
                    prod = prod.strip()
                    if prod == 'ε':
                        self[left].append(())
                        continue
                    if prod:
                        symbols = []
                        prod_chars = prod
                        i = 0
                        while i < len(prod_chars):
                            if prod_chars[i].isspace():
                                i += 1
                                continue
                            non_terminal_match = re.match(r'[A-Z][A-Za-z0-9]*\'?', prod_chars[i:])
                            if non_terminal_match:
                                symbol = non_terminal_match.group(0)
                                symbols.append(symbol)
                                i += len(symbol)
                            else:
                                symbol = prod_chars[i]
                                symbols.append(symbol)
                                i += 1
                        self[left].append(tuple(symbols))

    def add_augmented_production(self):
        original_start_symbol = list(self.keys())[0]
        new_start_symbol = 'S\''
        new_dict = {new_start_symbol: [(original_start_symbol,)]}
        new_dict.update(self)
        self.clear()
        self.update(new_dict)
        return new_start_symbol


if __name__ == '__main__':
    grammar_file_path = 'grammar.txt'
    grammar = ReadGrammar(grammar_file_path)
    print("Grammar after parsing and augmentation:")
    print(grammar)