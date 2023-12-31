from collections import OrderedDict
import sys
import re

class BaseChecker:
    def __init__(self, checkers):
        self.checkers = checkers

    def check_styles(self, user_fd, output, error_count):
        line_count = 0
        for line in user_fd:
            line_count += 1
            stripped_line = line.strip()
            for checker in self.checkers:
                checker.check_styles(line, stripped_line, line_count, output)
        for checker in self.checkers:
            checker.count_errors(error_count)

class NameCommentChecker:
    def __init__(self):
        self.error_count = 0
        self.author_found = False
        self.comment_found = False
        self.email_found = False
        self.comment_added = False

    def check_styles(self, line, stripped_line, line_count, output):
        # Skip if past the first 10 lines  
        if line_count > 10 or self.comment_added:
            return

        if "/*" in line or "//" in line:
            self.comment_found = True
            
        if self.comment_found:
            if "author" in line.lower():
                self.author_found = True
            if "@" in line:
                self.email_found = True

        # Check for different cases
        if self.author_found and self.email_found and self.comment_found:
            output["NameCommentChecker"].append("Line "+ str(line_count) + ": Name comment found")
            self.comment_added = True
            return True
        if self.author_found and self.comment_found:
            output["NameCommentChecker"].append("Line "+ str(line_count) + ": Name comment found, but email is missing")
            self.comment_added = True
            return True
        if self.email_found and self.comment_found:
            output["NameCommentChecker"].append("Line "+ str(line_count) + ": Name comment found, but did not include 'Author'")
            self.comment_added = True
            return True
        if line_count == 10 and self.author_found == False and self.email_found == False and self.comment_found == False:
            output["NameCommentChecker"].append("In Lines 1 - 10: No name comment found")
        return False
    
    def count_errors(self, error_count):
        if self.comment_added:
            error_count["NameCommentChecker"].append("Name Comment Errors: " + str(self.error_count))
        else:
            error_count["NameCommentChecker"].append("Name Comment Error: 1 Error - No Name Comment Found")

class NamingChecker:
    def __init__(self):
        self.error_count = 0

    def check_styles(self, line, stripped_line, line_count, output):
        struct_union_match = re.match(r'\b(struct|union)\s+(\w+)', stripped_line)
        if struct_union_match:
            struct_union_name = struct_union_match.group(2)
            if not struct_union_name[0].isupper() or "_" in struct_union_name:
                output["NamingChecker"].append("Line " + str(line_count) + ": Struct/Union name " + struct_union_name + " should be in CamelCase \n" + stripped_line)
                self.error_count += 1
        
        func_match = re.match(r'\w+\s+([a-zA-Z_]+)\(', stripped_line)
        if func_match:
            func_name = func_match.group(1)
            if not func_name.islower():
                output["NamingChecker"].append("Line " + str(line_count) + ": Uppercase character found. Function name '" + func_name + "' should be in snake_case. \n" + stripped_line)
                self.error_count += 1

            if len(func_name) > 7:
                if not "_" in func_name:
                    output["NamingChecker"].append("Line" + str(line_count) + ": Long function name '" + func_name + "' with no underscore\nCheck if function name is really a single word that follows snake_case")

            # Check for single letter variables
            if len(func_name) == 1 and func_name not in ['i', 'j', 'k', 'n', 'm']:
                    output["NamingChecker"].append("Line " + line_count + ": Single-letter variable '" + func_name + "' should not be used.")
                    self.error_count += 1


    def count_errors(self, error_count):   
        error_count["NamingChecker"].append("Total Naming Errors: " + str(self.error_count))
   
class LineLengthChecker:
    def __init__(self):
        self.error_count = 0

    def check_styles(self, line, stripped_line, line_count, output):
        if len(line) > 120:
            output["LineLengthChecker"].append("Line " + str(line_count) + ": A single line should never exceed 120 characters in a line including indentation\n" + line.rstrip('\n'))
            self.error_count += 1
        elif len(line) > 80:
            output["LineLengthChecker"].append("Line " + str(line_count) + ": Not an error, but try to avoid overlong lines.\nKeep it less than 80 characters including indentation. " + str(len(line)) + " characters have been found in this line \n" + line.rstrip('\n'))

    def count_errors(self, error_count):
        error_count["LineLengthChecker"].append("Total Line Length Errors: " + str(self.error_count))
        
class IncludeDirectiveChecker:
    def __init__(self):
        self.error_count = 0
        self.std_headers = []
        self.custom_headers = []
        self.state = "standard"

    def check_styles(self, line, stripped_line, line_count, output):
        if stripped_line == "" or line_count > 100:
            return
        if line_count == 100:
            self.validate_order(output)
            return
        
        if stripped_line.startswith("#include <") and self.state == "custom":
            output["IncludeDirectiveChecker"].append("Line " + str(line_count) + ": Custom project headers should be after standard library headers")
            self.std_headers.append(stripped_line)
            self.state = "standard"
            self.error_count += 1
        elif stripped_line.startswith("#include <"):
            self.std_headers.append(stripped_line)
            self.state = "standard"
        elif stripped_line.startswith("#include \""):
            self.custom_headers.append(stripped_line)
            self.state = "custom"
        
    def validate_order(self, output):
        if self.std_headers != sorted(self.std_headers):
            output["IncludeDirectiveChecker"].append("Standard library headers are not in alphabetical order")
            self.error_count += 1

        if self.custom_headers != sorted(self.custom_headers):
            output["IncludeDirectiveChecker"].append("Custom headers not in alphabetical order.")
            self.error_count += 1

    def count_errors(self, error_count):
        error_count["IncludeDirectiveChecker"].append("Total Include Directive Errors: " + str(self.error_count))

class IndentationChecker:
    def __init__(self):
        self.error_count = 0
        self.indentation_level = 0
        self.in_multiline_comment = False
        self.switch_found = False
        self.case_found = False

    def check_styles(self, line, stripped_line, line_count, output):
        if stripped_line == "":
            return
        if stripped_line.startswith("/*"):
            self.in_multiline_comment = True
        if stripped_line.endswith("*/"):
            self.in_multiline_comment = False
            return
        # Ignore lines within a comment block
        if self.in_multiline_comment or stripped_line.startswith("//"):
            return
        
        # Do not change indent count inside a switch statement
        if "switch" in stripped_line:
            self.switch_found = True
        elif self.switch_found and "case" in stripped_line:
            self.case_found = True
        elif self.switch_found and "}" in stripped_line:
            self.switch_found = False
            self.case_found = False

        cur_indentation = line[:len(line) - len(line.lstrip())]
        if "}" in line:
            expected_indentation = "    " * (self.indentation_level - 1)
        else:
            expected_indentation = "    " * self.indentation_level

        if "{" in line:
            self.indentation_level +=1
        if "}" in line:
            self.indentation_level -=1

        if "\t" in line:
            self.error_count += 1
            output["IndentationChecker"].append("Line " + str(line_count) + ": Tab found\n" + line.rstrip('\n'))
            return
        
        if cur_indentation != expected_indentation:
            self.error_count += 1
            output["IndentationChecker"].append("Line " + str(line_count) + ": Not 4 spaces or wrong indentation level.\n" + line.rstrip('\n'))

    def count_errors(self, error_count):
        error_count["IndentationChecker"].append("Total Indentation Errors: " + str(self.error_count))

class BlocksChecker:
    def __init__(self):
        self.error_count = 0
        self.std_headers = []
        self.custom_headers = []
        self.block_starters = [
            r'\b(if|else|for|while|do|switch)\b',
            r'\b(int|float|char|void|double|bool|long|short)\s+\w+\s*\(.*\)\s*{',
            r'\b(const\s+)?\b(int|float|char|void|double|bool|long|short)(\s+\*|\s*)\s+\w+(\s*\[\])?',
            r'\b(enum|struct)\s+\w+\s*{'
        ]

    def check_styles(self, line, stripped_line, line_count, output):
        if "typedef" in stripped_line:
            match = re.search(r'\btypedef\b\s+\w+\s+(\w+)', stripped_line)
            if match:
                custom_type = match.group(1)
                custom_type_pattern = r'\b(' + custom_type + r')\s+\w+\s*\(.*\)\s*{'
                self.block_starters.append(custom_type_pattern)

        elif "{" in stripped_line:
            if stripped_line == "{":
                output["BlocksChecker"].append("Line " + str(line_count) + ": Opening curly brace should not be on a separate line \n" + stripped_line)
                self.error_count += 1
            elif not any(re.search(pattern, line) for pattern in self.block_starters):
                output["BlocksChecker"].append("Line " + str(line_count) + ": Suspicious block start: \n" + stripped_line)
                self.error_count += 1
                
            spacing_check = re.search(r'(\w|\))\s\{', stripped_line)

            if not spacing_check:
                output["BlocksChecker"].append("Line " + str(line_count) + ": Opening curly brace should be preceded by one space \n" + stripped_line)
                self.error_count += 1

        if "}" in stripped_line:
            if not stripped_line.startswith("}") and not any(re.search(pattern, line) for pattern in self.block_starters):
                output["BlocksChecker"].append("Line " + str(line_count) + ": Closing curly brace should be on a separate line \n" + stripped_line)
                self.error_count += 1

    def count_errors(self, error_count):   
        error_count["BlocksChecker"].append("Total Block Errors: " + str(self.error_count))
   
class HorizontalSpaceChecker:
    def __init__(self):
        self.error_count = 0
        self.word_or_num =   r'[\w\d]'
        self.relational_op = r'((?<!<)<=|==|!=|(?<!>)>=|((?<!<)<(?!<)(?!=))|((?<!>)>(?!>)(?!=)))'
        self.assignment_op = r'(\+=|-=|\*=|/=|%=|&=|\|=|\^=|~=|<<=|>>=|((?<!\+)(?<!-)(?<!\*)(?<!/)(?<!%)(?<!&)(?<!\|)(?<!\^)(?<!~)(?<!<)(?<!>)(?<!<)(?<!>)(?<!!)(?<!=)=(?!=)))'
        self.arithmetic_op = r'(((?<!\+)\+(?!=)(?!\+))|((?<!\-)-(?!=)(?!-))|((?<!/)/(?!/)(?!=)))'
        self.logical_op =   r'((\&\&)|(\|\|))'
        self.bitwise_op =   r'((?<!\|)\|(?!\|)|\^(?!=)|<<(?!=)|>>(?!=))'
        self.address_op =   r'(?<!&)&(?!&)'
        self.start_exceptions = [
            r'/\*', r'\*', r'#define', r'#include'
        ]
        self.other_exceptions = [
            r'print\s*\(\s*["\'](.*)["\']\s*\)',  # Ignore all text in a print statement
            r'printf\s*\(\s*["\'](.*)["\']\s*\)', # Ignore all text in a printf statement
            r'scanf\s*\(\s*["\'](.*)["\']\s*\)'   # Ignore all text in a scan statement
        ]
        self.lr_spacing = {
            # Check:            No space on either side | No space on left | No space of right
            "relational":       r'(?<!\s)' + self.relational_op + r'(?!\s)|(?<!\s)' + self.relational_op + r'\s+|\s+' + self.relational_op + r'(?!\s)',
            "assignment":       r'(?<!\s)' + self.assignment_op + r'(?!\s)|(?<!\s)' + self.assignment_op + r'\s+|\s+' + self.assignment_op + r'(?!\s)',
            "arithmetic":       r'(?<!\s)' + self.arithmetic_op + r'(?!\s)|(?<!\s)' + self.arithmetic_op + r'\s+|\s+' + self.arithmetic_op + r'(?!\s)',
            "logical":          r'(?<!\s)' + self.logical_op + r'(?!\s)|(?<!\s)' + self.logical_op + r'\s+|\s+' + self.logical_op + r'(?!\s)',
            "bitwise":          r'(?<!\s)' + self.bitwise_op + r'(?!\s)|(?<!\s)' + self.bitwise_op + r'\s+|\s+' + self.bitwise_op + r'(?!\s)',
            "address_bit":      r'(?<!\s)' + self.address_op + r'(?!\s)|(?<!\s)' + self.address_op + r'\s+',
            "pointer":          r'(?<!\s)\*+(?!\s)|(?<!\s)\*+\s+|\s+\*+(?!\s)(?!=)',
        }
        self.over_spacing = {
            # Check:            Two or more space on the right | Two or more space on the left
            "relational":       r'[\w\d]\s{2,}' + re.escape(self.relational_op) + r'\s{2,}[\w\d]',
            "assignment":       r'[\w\d]\s{2,}' + re.escape(self.assignment_op) + r'\s{2,}[\w\d]',
            "arithmetic":       r'[\w\d]\s{2,}' + re.escape(self.arithmetic_op) + r'\s{2,}[\w\d]',
            "logical":          r'[\w\d]\s{2,}(\&\&|\|\|)\s{2,}[\w\d]',
            "bitwise":          r'[\w\d]\s{2,}' + re.escape(self.bitwise_op) + r'\s{2,}[\w\d]',
            "conds_loops":      r'(if|else if|for|while|do)\s{2,}(\(|\{)',
            "pointer":          r'(\s{2,}\*+\s*|\s*\*+\s{2,})'

        }
        self.other_rules = {
            "logical_not":  r'!\s+\w',
            "conds_loops":  r'(if|else if|for|while|do)(\(|\{)',
            "unary_ops":    r'(?<![\w\d])(\~|\+\+|--)\s+[\w\d]', 
            "inside_paren": r'[(\[]\s+|\s+[)\]]'
        }
        self.other_comment = {
            "logical_not": "Too many spaces between unary operator ! (logical not) and its operand",
            "conds_loops": "There should be a space between ",
            "unary_ops":   "Never insert a space between a unary operator and its operand", 
            "inside_paren": "Never insert a space immediately inside a parenthesis or square bracket"
        }
        self.spacing_rules = [self.lr_spacing, self.over_spacing, self.other_rules]

    def check_styles(self, line, stripped_line, line_count, output):
        for exception in self.start_exceptions:
            if re.match(exception, stripped_line):
                return
        for exception in self.other_exceptions:
            if re.search(exception, stripped_line):
                return

        for i in range(len(self.spacing_rules)):
            for pattern_name, pattern in self.spacing_rules[i].items():
                match = re.search(pattern, line)
                if match:
                    error_msg = "Line " + str(line_count) + ": "
                    notify_fp = ""

                    current_error = match.group(0).strip()
                    stripped_error = current_error.strip()
                    if stripped_error == "-":
                        notify_fp += "\nCheck if error is a negative number. Could be a false positive."
                    elif stripped_error == ">" or stripped_error == "<":
                        notify_fp += "\nCheck if current error is a usage string. Could be a false positive."
                    elif stripped_error == "*" or stripped_error == "/":
                        notify_fp += "\nCheck if current error is an inline comment or type-cast. Could be a false positive."

                    
                    if i == 0: # self.spacing_rules[0] = self.lr_spacing
                        error_msg += ("No space on one or both sides of " + current_error + notify_fp)
                    elif i == 1: # self.spacing_rules[1] = self.over_spacing
                        error_msg += ("Too many spaces before and after" + current_error + notify_fp)
                    else: # self.spacing_rules[2] = self.other_rules
                        error_msg += (self.other_comment[pattern_name] + current_error)
                    output["HorizontalSpaceChecker"].append(error_msg + "\n" + stripped_line)
                    self.error_count += 1
                
    def count_errors(self, error_count):  
        error_count["HorizontalSpaceChecker"].append("Total Horizontal Spacing Errors: " + str(self.error_count))

class VerticalSpaceChecker:
    def __init__(self):
        self.error_count = 0
        self.last_line_type = None
        self.newline_count = 0
        self.last_line = None

    def check_styles(self, line, stripped_line, line_count, output):
        if stripped_line == "":
            self.newline_count += 1
            self.last_line_type = None
        else:
            if re.match(r'^#include', stripped_line):
                if self.last_line_type == "#include" and self.newline_count > 0:
                    output["VerticalSpaceChecker"].append("Line " + str(line_count-1) + ": Possible error. Check if directives are split by group.\nIncludes directive of the same group should not be separated with a new line. \n" + self.last_line)
                self.last_line_type = "#include"

            elif re.match(r'^#define', stripped_line):
                if self.last_line_type == "#include" and self.newline_count != 1:
                    output["VerticalSpaceChecker"].append("Line" + str(line_count) + ": There should be one vertical space (newline) between the last #include and first #define \n" + self.last_line)
                self.last_line_type = "#define"
            elif self.last_line_type == "#define" and not re.match(r'(^#define|\n|"")', stripped_line):
                output["VerticalSpaceChecker"].append("Line" + str(line_count) + ": There should be one vertical space (newline) after the last #define \n" + self.last_line)
                self.last_line_type = None
            self.newline_count = 0

        self.last_line = stripped_line
            
    def count_errors(self, error_count):  
        error_count["VerticalSpaceChecker"].append("Total Vertical Spacing Errors: " + str(self.error_count))

def file_checker(file_name):
    # Check file type
    if file_name[-2:] != ".c":
        raise ValueError("Please enter a .c file!")

    # Check if file exists
    try:
      with open(file_name, "r") as user_fd:
          pass
    except Exception as e:
        raise ValueError("File not found")
    
def main():
    if len(sys.argv) != 2:
        print("Usage: python style_checker.py <file_name.c>")
        return
    
    file_name = sys.argv[1].strip()

    try:
        file_checker(file_name)
        out_file_name = file_name[:-2] + "_style_info.txt"

        # clear contents of out_file before appending info
        open(out_file_name, 'w').close()
        out_fd = open(out_file_name, "a")
        output = OrderedDict([("NameCommentChecker", []), 
                              ("IncludeDirectiveChecker", []), 
                              ("NamingChecker", []), 
                              ("BlocksChecker", []), 
                              ("LineLengthChecker", ["Ignore if 80+ char error is caused by a necessary function declaration etc.",]), 
                              ("HorizontalSpaceChecker", []), 
                              ("VerticalSpaceChecker", []), 
                              ("IndentationChecker", [])])
        
        error_count = OrderedDict([("NameCommentChecker", []),
                                   ("IncludeDirectiveChecker", []), 
                                   ("NamingChecker", []),
                                   ("BlocksChecker", []), 
                                   ("LineLengthChecker", []), 
                                   ("HorizontalSpaceChecker", []), 
                                   ("VerticalSpaceChecker", []), 
                                   ("IndentationChecker", [])])

        name_comment_checker = NameCommentChecker()
        include_directive_checker = IncludeDirectiveChecker()
        naming_checker = NamingChecker()
        blocks_checker = BlocksChecker()
        line_length_checker = LineLengthChecker()
        horizontal_space_checker = HorizontalSpaceChecker()
        vertical_space_checker = VerticalSpaceChecker()
        indentation_checker = IndentationChecker()
        
        checkers = [name_comment_checker, include_directive_checker, naming_checker, blocks_checker, line_length_checker, horizontal_space_checker, vertical_space_checker, indentation_checker]

        with open(file_name, "r") as user_fd:
            base_checker = BaseChecker(checkers)
            base_checker.check_styles(user_fd, output, error_count)

            for key, value_list in error_count.items():
                for item in value_list:
                    out_fd.write(item + "\n")
            
            out_fd.write("\nErrors found:\n")
            for key, value_list in output.items():
                out_fd.write(key + ": \n")
                if not value_list:
                    out_fd.write("No errors found\n\n");
                    continue
                for item in value_list:
                    out_fd.write(item + "\n\n")
                    
        print("Check complete! See the errors in ./" + out_file_name)

    except ValueError as e:
        print(e)
    
if __name__ == "__main__":
    main()