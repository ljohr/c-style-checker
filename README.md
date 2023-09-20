# C Style Checker
This is a python script which checks whether a C program conforms to the style guideline based on the Google C++ Style Guide, compiled by Professor Amittai Aviram at Boston College.

## Usage
`python style_checker.py file_name.c`

## Code Structure
The code is organized eight styling checker classes, one main checker class (coordinates how styling checker classes are run), and a main section at the end (runs the script). 
Basic descriptions are provided by class, but please see All Rules section for a complete list of what is checked by this script.

### `BaseChecker` Class
- `check_styles`: This method breaks down user input line by line, strips unnecessary whitespace, and sends each line to each style checker for analysis. This method also handles error counting.

### Style Checker Classes Common Methods
- All style checker classes have at least two methods called `check_styles` and `count_errors`
- `check_styles`: Method that handles main style checking
- `count_errors`: Method that counts all errors generated in the class

### `NameCommentChecker` Class
- Checks if author, email, and the keyword "Author" is found
- Operates on the basis that the "Author" comment will be within the first 10 lines of the file
- Searches for a opening comment (either `/*` or `//`)
  - When comment_found == True searches for the keyword "Author" and "@" ("Author" can be lowercase or uppercase)

### `NamingChecker` Class
- Makes sure variables and functions are in snake_case
- Reports an error if variable and function names are too long (over 7 characters)
- Reports an error if variable and function names are single letters (exceptions: i, j, k, n, m)
  
### `LineLengthChecker` Class
- Reports an error if a line exceeds 120 characters
- Adds a warning to the output file if a line exceeds 80 characters

### `IncludeDirectiveChecker` Class
- Checks the first 100 lines to check header #include directives
- Checks if custom project headers are after standard library headers
- Checks if standard library headers are in alphabetical order
- Checks if custom library headers are in alphabetical order

### `IndentationChecker` Class
- Checks if all indentations are multiples of 4 spaces at the correct indentation level
- Checks for tabs
- Checks for lines that are comments and skips
- Note: indentation is NOT counted inside a switch statement to prevent errors (Manual check necessary)

### `BlocksChecker` Class
- Checks if a given code block always begins with an open curly brace and ends with a close curly brace

### `HorizontalSpaceChecker` Class
- Checks that one space character is inserted in the right positions
- Checks that no space character is inserted in the right positions
- Each condition is checked for using regular expressions organized by type

### `VerticalSpaceChecker` Class
- Checks that vertical spaces are provided in the right places

### `file_checker()` Function
- Checks that file specified by the user is a C file and then checks if the file exists.

## `main()` Section
- Runs the program
- Organizes the output and error count into ordered dictionaries to preserve the specified order (Necessary as this program is made compatible with Python 2.7)
- Style checkers are organized into an array
- The base_checker is called on the array of style checkers
- The error messages (output dictionary) and error count are written to the output text file line by line
- The output file take the format `user_file_style_info.txt`

For a comprehensive list of all rules, please check the all_rules.txt file

## Demo
https://github.com/ljohr/c-style-checker/assets/46297075/0f08dfbd-8292-49e4-baba-bffec11bac42
