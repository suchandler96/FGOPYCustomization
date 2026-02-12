import os.path
import re
from typing import NamedTuple, Iterator, List

FIXED_BASE_INDENT = 8
COMMENT     =   99
FLOAT       =  199
INT         =  299
KEYWORDS    =  399
HINTWORDS   =  499
COMPARE     =  599
OP          =  699
ID          =  799
LPAREN      =  899
RPAREN      =  999
STAR        = 1099
COLON       = 1199
DOT         = 1299
COMMA       = 1399
NEWLINE     = 1499
INDENT      = 1599
DEDENT      = 1699
SKIP        = 1799
MISMATCH    = 1899

TOKNAME2INT = {
    "COMMENT"   : COMMENT,
    "FLOAT"     : FLOAT,
    "INT"       : INT,
    "KEYWORDS"  : KEYWORDS,
    "HINTWORDS" : HINTWORDS,
    "COMPARE"   : COMPARE,
    "OP"        : OP,
    "ID"        : ID,
    "LPAREN"    : LPAREN,
    "RPAREN"    : RPAREN,
    "STAR"      : STAR,
    "COLON"     : COLON,
    "DOT"       : DOT,
    "COMMA"     : COMMA,
    "NEWLINE"   : NEWLINE,
    "INDENT"    : INDENT,
    "DEDENT"    : DEDENT,
    "SKIP"      : SKIP,
    "MISMATCH"  : MISMATCH,
}

class Token(NamedTuple):
    type: int
    value: str
    line: int
    column: int

class SelectCardInfo:
    def __init__(self):
        self.target = -1
        self.hougu_servants = []
        self.pre_toks_st = -1
        self.pre_toks_ed = -1
        self.post_toks_st = -1
        self.post_toks_ed = -1
        self.preprogrammed_selectCard = ""
        self.selectCard_params = []

    def empty(self):
        return self.target < 0 and len(self.hougu_servants) == 0 and self.pre_toks_st == self.pre_toks_ed == -1 and \
            self.post_toks_st == self.post_toks_ed == -1 and self.preprogrammed_selectCard == "" and len(self.selectCard_params) == 0

def tokenize(code: str) -> Iterator[Token]:
    token_specification = [
        ('COMMENT',  r'#[^\n]*'),             # Comments
        # ('FLOAT',    r'\d+\.\d+'),            # Decimal numbers
        ('INT',      r'\d+'),                 # Integer numbers
        ('KEYWORDS', r'\b(if|else|elif|and|or|not|exists|pre|post|hougu|target|m|r|g|b)\b'),  # Keywords
        ('HINTWORDS', r'(?<![A-Za-z_])(x|s|st)(?![A-Za-z_])'),  # Keywords that may be directly adjacent to non-letters
        ('COMPARE',  r'>=|<=|==|!='),         # Multi-char comparison
        ('OP',       r'[<>]'),                # Single-char comparison
        ('ID',       r'[a-zA-Z_][a-zA-Z_]*'), # Identifiers
        ('LPAREN',   r'\('),
        ('RPAREN',   r'\)'),
        ('STAR',     r'\*'),                  # * (e.g., exists(0.*))
        ('COLON',    r':'),                   # Colon for blocks
        ('DOT',      r'\.'),                  # Dot for properties
        ('COMMA',    r','),
        ('NEWLINE',  r'\n'),                  # Capture newlines
        ('SKIP',     r'[ \t]+'),              # Spaces/Tabs (handled manually at start of line)
        ('MISMATCH', r'.'),                   # Error catch
    ]

    # regex compilation
    tok_regex = '|'.join('(?P<%s>%s)' % pair for pair in token_specification)
    get_token = re.compile(tok_regex).match

    line_num = 1
    line_start = 0

    # Indentation stack: starts with 0 (root level)
    indent_stack = [0]

    # This helps us decide if we are at the start of a line
    at_line_start = True

    pos = 0
    last_kind = None
    indent_char = None
    indent_amt = 0
    while pos < len(code):
        mo = get_token(code, pos)
        if mo is None:
            break

        kind = mo.lastgroup
        value = mo.group(kind)
        col = mo.start() - line_start

        if kind == 'NEWLINE':
            at_line_start = True
            line_start = mo.end()
            line_num += 1
            if last_kind != 'NEWLINE':  # Avoid yielding multiple NEWLINE tokens
                yield Token(TOKNAME2INT[kind], '\\n', line_num, col)
            pos = mo.end()
            last_kind = kind
            continue

        elif kind == 'SKIP':
            # If we are not at the start of the line, just ignore whitespace
            if not at_line_start:
                pos = mo.end()
                continue

            # If we ARE at start of line, calculate indentation
            indent_level = len(value) # Assuming spaces (1 char = 1 unit)
            # (In a real production parser, you'd handle tabs vs spaces checks here)
            if not indent_char:
                assert indent_level > 0, f"wierd: it shouldn't emit the SKIP token"
                indent_char = value[0]
                assert indent_char == ' ' or indent_char == '\t'
            else:
                assert all(c == indent_char for c in value), f"Mixed indentation characters at line {line_num}"
            if indent_amt == 0:
                indent_amt = indent_level   # take the first indent as the base indent level
                if indent_char == '\t':
                    assert indent_amt == 1 or indent_amt == 2, f"Unexpected tab indent size: {indent_amt}"
                elif indent_char == ' ':
                    assert indent_amt in [2, 4, 8], f"Unexpected space indent size: {indent_amt}"
            else:
                assert indent_level % indent_amt == 0, \
                    f"Indent level {indent_level} is not a multiple of base indent {indent_amt} at line {line_num}"

            pos = mo.end()

            # Note: We don't yield yet, we wait to see if the line is empty/comment
            # But for simplicity in this snippet, we process indentation logic next loop
            # by keeping `at_line_start` True, but strictly speaking, we need
            # to peek ahead to ensure it's not an empty line.
            # Simplified Logic: We will process indentation when we hit the first
            # non-whitespace token below.
            continue

        elif kind == 'COMMENT':
            pos = mo.end()
            continue

        elif kind == 'ID' and not re.search(r"^selectCard", value):
            # Apart from selectCardxxx, only accepts the following as IDs
            if value not in {"np"}:
                raise RuntimeError(f'Unexpected token {value!r} at line {line_num}')

        # --- INDENTATION LOGIC ---
        if at_line_start:
            # We hit a real token (not newline/skip/comment)
            # Calculate column based on where this token actually starts
            if indent_amt == 0:
                assert col == 0, f"indent_amt should've been set before getting col == 0"
                current_indent = 0
            else:
                current_indent = col // indent_amt

            if current_indent > indent_stack[-1]:
                assert current_indent == indent_stack[-1] + 1, f"Unexpected indent increase at line {line_num}"
                indent_stack.append(current_indent)
                yield Token(INDENT, '', line_num, 0)
            elif current_indent < indent_stack[-1]:
                while current_indent < indent_stack[-1]:
                    indent_stack.pop()
                    yield Token(DEDENT, '', line_num, 0)
                if current_indent != indent_stack[-1]:
                    raise IndentationError(f"Unindent does not match any outer indentation level at line {line_num}")

            at_line_start = False

        if kind == 'MISMATCH':
            raise RuntimeError(f'Unexpected char {value!r} at line {line_num}')

        last_kind = kind
        yield Token(TOKNAME2INT[kind], value, line_num, col)
        pos = mo.end()
    if last_kind != 'NEWLINE':
        yield Token(NEWLINE, '\\n', line_num, 0)

    # End of file: Deduce remaining indents
    while len(indent_stack) > 1:
        indent_stack.pop()
        yield Token(DEDENT, '', line_num, 0)


class ActionTokWalker:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0

    def curTok(self) -> Token:
        return self.tokens[self.pos] if self.pos < len(self.tokens) else self.tokens[-1]

    def advance(self):
        self.pos += 1

    def get_pos(self) -> int:
        return self.pos

    def set_pos(self, pos: int):
        self.pos = pos

    def peek(self, offset=1) -> Token:
        idx = self.pos + offset
        if idx >= len(self.tokens):
            return self.tokens[-1]
        elif idx < 0:
            return self.tokens[0]
        return self.tokens[idx]

    def peek_until(self, start_pos, tok_vals):
        offset = 1
        while start_pos + offset < len(self.tokens):
            tok = self.tokens[start_pos + offset]
            if tok.value in tok_vals:
                return start_pos + offset# , toks
            offset += 1
        assert False, f"Expected token of value {tok_vals} not found after position {start_pos}"


class SyntaxValidator(ActionTokWalker):
    def __init__(self, tokens: List[Token]):
        super(SyntaxValidator, self).__init__(tokens)
        # Tracks if an 'if' was seen at a specific indentation level
        # Key: Indent Level, Value: Boolean (True if an IF is active/pending)
        self.scope_has_if = {}
        self.current_indent_level = 0

    def validate(self):
        paren_depth = 0
        while self.get_pos() < len(self.tokens):
            token = self.curTok()

            if token.type == INDENT:
                self.current_indent_level += 1
            elif token.type == DEDENT:
                # When leaving a block, reset the "if" memory for the inner level
                if self.current_indent_level in self.scope_has_if:
                    del self.scope_has_if[self.current_indent_level]
                self.current_indent_level -= 1
            elif token.type == LPAREN:
                paren_depth += 1
            elif token.type == RPAREN:
                paren_depth -= 1
                if paren_depth < 0:
                    raise SyntaxError(f"Line {token.line}: Mismatched parentheses.")
            elif token.type == COLON:
                if paren_depth != 0:
                    raise SyntaxError(f"Line {token.line}: Colon found inside parentheses. Possibly missing closing parenthesis.")
                cur_pos = self.pos
                self.advance()
                content_found = False
                while self.get_pos() < len(self.tokens):
                    tok = self.curTok()
                    if tok.type not in {DEDENT, INDENT, NEWLINE, SKIP, COMMENT}:
                        content_found = True
                        break
                    self.advance()
                if not content_found:
                    raise SyntaxError(f"Line {token.line}: Expected content after colon, but found end of file.")
                self.set_pos(cur_pos)  # Reset position to after the colon for normal processing
            elif token.type == NEWLINE:
                if paren_depth != 0:
                    raise SyntaxError(f"Line {token.line}: Newline found inside parentheses. Possibly missing closing parenthesis.")
            elif token.value in {"s", "st"}:
                if self.peek().type != INT:
                    raise SyntaxError(f"Line {token.line}: Expected integer after '{token.value}' for stage/stageTurn.")
                if self.peek_until(self.pos, [':']) not in [self.pos + 2, self.pos + 4]:
                    raise SyntaxError(f"Line {token.line}: Expected 'sX:' or 'sXstY:' format.")
            elif token.value in {"target"}:
                if not (self.tokens[self.pos + 1].type == COLON and self.tokens[self.pos + 2].type == INT and self.tokens[self.pos + 3].type == NEWLINE):
                    raise SyntaxError(f"Line {token.line}: Expected 'target: <int>', got 'target {self.peek().value} {self.peek(2).value} {self.peek(3).value}'")
            elif token.value in {"hougu"}:
                if not self.tokens[self.pos + 1].type == COLON:
                    raise SyntaxError(f"Line {token.line}: Expected colon following hougu, got 'hougu {self.peek().value} '")
                pos = self.pos + 2
                int_found = False
                while self.tokens[pos].type != NEWLINE:
                    if self.tokens[pos].type == INT:
                        int_found = True
                        if not 0 <= int(self.tokens[pos].value) <= 2:
                            raise SyntaxError(f"Line {token.line}: Expected servant index 0, 1, or 2 in hougu declaration, got {self.tokens[pos].value}")
                    elif self.tokens[pos].type in [COMMA, LPAREN, RPAREN]:
                        pass
                    else:
                        raise SyntaxError(f"Line {token.line}: Unexpected token in hougu declaration: {self.tokens[pos].value}")
                    pos += 1
                if not int_found:
                    raise SyntaxError(f"Line {token.line}: Expected at least one servant index in hougu declaration.")
            elif token.value in {"pre", "post"}:
                if self.peek().type != COLON:
                    raise SyntaxError(f"Line {token.line}: Expected colon following '{token.value}', got '{token.value} {self.peek().value}'")
            elif token.value == "exists":
                if not ((self.peek().type == LPAREN and self.peek(2).value in ['0', '1', '2', '*'] and
                         self.peek(3).type == DOT and self.peek(4).value in ['r', 'g', 'b', '*'] and self.peek(5).type == RPAREN) or
                        (self.peek().type == LPAREN and self.peek(2).value in ['0', '1', '2', '*'] and
                         self.peek(3).type == DOT and self.peek(4).value in ['r', 'g', 'b', '*'] and self.peek(5).value == 'x' and
                         self.peek(6).type == INT and self.peek(7).type == RPAREN) or
                        (self.peek().type == LPAREN and self.peek(2).type == INT and self.peek(3).value == 'x' and
                         self.peek(4).value in ['0', '1', '2', '*'] and self.peek(5).type == DOT and self.peek(6).value in ['r', 'g', 'b', '*'] and
                         self.peek(7).type == RPAREN)):
                    raise SyntaxError(f"Line {token.line}: Syntax of 'exists' is exists(_count_ x _servant_._color_) or exists(_servant_._color_ x _count_) "
                                      "or exists(_servant_._color_)")
            elif token.type == KEYWORDS and token.value == 'if':
                self.handle_if()
            elif token.type == KEYWORDS and token.value == 'else':
                self.handle_else()
            elif token.type == KEYWORDS and token.value == 'elif':
                self.handle_elif()
            elif token.type == HINTWORDS and token.value == 'x':
                self.handle_x()
            else:
                pass
            self.advance()

    def handle_x(self):
        line = self.curTok().line
        if not ((self.peek(-3).value == 'exists' and self.peek(-2).type == LPAREN and self.peek(-1).type == INT and
                 self.peek(1).type in {STAR, INT} and self.peek(2).type == DOT and self.peek(3).type in {STAR, INT} and self.peek(4).type == RPAREN) or
                (self.peek(-5).value == 'exists' and self.peek(-4).type == LPAREN and self.peek(-3).type in {INT, STAR} and
                 self.peek(-2).type == DOT and self.peek(-1).type in {STAR, INT} and self.peek(1).type == INT and self.peek(2).type == RPAREN)):
            raise SyntaxError(f"Line {line}: Syntax of 'x': exists(_count_ x _servant_._color_) or exists(_servant_._color_ x _count_)")

    def handle_if(self):
        """
        Rule: Check for colon, then check for newline vs inline expression.
        Also marks this indentation level as having an active 'if'.
        """
        line = self.curTok().line
        cur_pos = self.get_pos()
        self.scope_has_if[self.current_indent_level] = True

        # Scan forward to find the colon
        while self.get_pos() < len(self.tokens) and self.curTok().type != COLON:
            if self.curTok().type == NEWLINE:
                raise SyntaxError(f"Line {line}: 'if' statement missing colon before newline.")
            self.advance()
        if self.get_pos() >= len(self.tokens) or self.curTok().type != COLON:
            raise SyntaxError(f"Line {line}: 'if' statement missing colon.")

        self.advance() # consume COLON

        # RULE: "either there should be some expressions in this line or an indent"
        next_tok = self.curTok()

        if next_tok.type == NEWLINE:
            # If newline immediately follows colon, next token MUST be INDENT
            if self.peek().type != INDENT:
                raise SyntaxError(f"Line {line}: Expected 4-space indent after 'if' statement on new line.")
        else:
            # Inline expression (e.g., "if x: y = 1")
            pass
        self.set_pos(cur_pos)   # recover to the original state

    def handle_else(self):
        """
        Rule: Must be an 'if' at the same indent level immediately before.
        """
        line = self.curTok().line

        # Check if we have a matching IF at this level
        if not self.scope_has_if.get(self.current_indent_level, False):
            raise SyntaxError(f"Line {line}: 'else' without matching 'if' at this indentation level.")

        # Reset because the if-else block is essentially consumed/linked now
        # (Allows 'if... else... if...' chains if needed, though simple else usually ends it)
        self.scope_has_if[self.current_indent_level] = False

    def handle_elif(self):
        """
        Rule: Must be an 'if' or 'elif' at the same indent level immediately before.
              Check for colon, then check for newline vs inline expression.
        """
        line = self.curTok().line
        cur_pos = self.get_pos()
        # Check if we have a matching IF or ELIF at this level
        if not self.scope_has_if.get(self.current_indent_level, False):
            raise SyntaxError(f"Line {line}: 'elif' without matching 'if' at this indentation level.")

        # Keep the 'if' active for further 'elif' or 'else'
        self.advance()

        # Scan forward to find the colon
        while self.get_pos() < len(self.tokens) and self.curTok().type != COLON:
            if self.curTok().type == NEWLINE:
                raise SyntaxError(f"Line {line}: 'if' statement missing colon before newline.")
            self.advance()
        if self.get_pos() >= len(self.tokens) or self.curTok().type != COLON:
            raise SyntaxError(f"Line {line}: 'if' statement missing colon.")

        self.advance() # consume COLON

        # RULE: "either there should be some expressions in this line or an indent"
        next_tok = self.curTok()

        if next_tok.type == NEWLINE:
            # If newline immediately follows colon, next token MUST be INDENT
            if self.peek().type != INDENT:
                raise SyntaxError(f"Line {line}: Expected 4-space indent after 'if' statement on new line.")
        else:
            # Inline expression
            pass
        self.set_pos(cur_pos)   # recover the original state

    # rules:
    # 1. (do it in postprocessing) the last token should be a single NEWLINE
    # 2. the next token of a colon should not be the last token
    # 3. s and st must be at start of line (only applies to the first if adjacent),
    #    the next token of s and st should be INT, followed by a COLON and NEWLINE,
    #    and next line should be indented (if not, postprocessing should've inserted)


class CustomizedTurnGenerator(ActionTokWalker):
    def __init__(self, tokens: List[Token], turn_name: str):
        super(CustomizedTurnGenerator, self).__init__(tokens)
        self.cur_indent = 2
        self.class_str = \
f'''class {turn_name}(CustomTurn):
    def __init__(self):
        super({turn_name}, self).__init__()''' \
r'''
    def __call__(self,turn):
        self.stage,self.stageTurn=[t:=Detect(.2).getStage(),1+self.stageTurn*(self.stage==t)]
        if turn==1:
            Detect.cache.setupServantDead()
            self.stageTotal=Detect.cache.getStageTotal()
            self.servant=[(lambda x:(x,)+servantData.get(x,(0,0,0,0,(0,0),((0,0),(0,0),(0,0)))))(Detect.cache.getFieldServant(i))for i in range(3)]
        else:
            for i in(i for i in range(3)if Detect.cache.isServantDead(i)):
                self.servant[i]=(lambda x:(x,)+servantData.get(x,(0,0,0,0,(0,0),((0,0),(0,0),(0,0)))))(Detect.cache.getFieldServant(i))
                self.countDown[0][i]=[0,0,0]
        logger.info(f'Turn {turn} Stage {self.stage} StageTurn {self.stageTurn} {[i[0]for i in self.servant]}')
        if self.stageTurn==1:Detect.cache.setupEnemyGird()
        self.enemy=[Detect.cache.getEnemyHp(i)for i in range(6)]
'''

    def parseActionString(self, action_tok_st, action_tok_ed) -> str:
        ret_str = ""
        tok_id = action_tok_st
        while tok_id < action_tok_ed:
            if self.tokens[tok_id].type == INT:             # servant_id
                assert self.tokens[tok_id + 1].type == DOT and self.tokens[tok_id + 2].type == INT, \
                    "Expected format: servant_id.skill_id>target ('>target' is optional), got " \
                    f"{self.tokens[tok_id].value} {self.tokens[tok_id + 1].value} {self.tokens[tok_id + 2].value} at line {self.tokens[tok_id].line}"
                servant_id = int(self.tokens[tok_id].value)
                skill_id = int(self.tokens[tok_id + 2].value)
                if tok_id + 4 < action_tok_ed and self.tokens[tok_id + 3].value == ">":
                    assert self.tokens[tok_id + 4].type == INT  # target
                    target = int(self.tokens[tok_id + 4].value)
                    tok_id += 5
                else:
                    target = -1
                    tok_id += 3
                ret_str += "    " * self.cur_indent + f"self.castSingleOrNoTargetServantSkill({servant_id}, {skill_id}, {target})\n"
            elif self.tokens[tok_id].value == "m" or self.tokens[tok_id].value == "M":  # master skill
                assert self.tokens[tok_id + 1].type == DOT and self.tokens[tok_id + 2].type == INT, \
                    "Expected format: m.skill_id>target ('>target' is optional), got " \
                    f"{self.tokens[tok_id].value} {self.tokens[tok_id + 1].value} {self.tokens[tok_id + 2].value} at line {self.tokens[tok_id].line}"
                skill_id = int(self.tokens[tok_id + 2].value)
                targets = []
                if tok_id + 3 < action_tok_ed and self.tokens[tok_id + 3].value == ">":
                    if self.tokens[tok_id + 4].type == INT:
                        targets.append(int(self.tokens[tok_id + 4].value))
                        tok_id += 5
                    else:   # multiple targets
                        assert self.tokens[tok_id + 4].value == "("
                        j = tok_id + 5
                        while j < action_tok_ed:
                            if self.tokens[j].type == INT:
                                targets.append(int(self.tokens[j].value))
                            elif self.tokens[j].value == ")":
                                break
                            j += 1
                        tok_id = j + 1
                else:
                    tok_id += 3
                ret_str += "    " * self.cur_indent + f"self.castMasterSkill({skill_id}, " + (f"{targets}" if len(targets) > 0 else "[]") + ")\n"
            elif "selectCard" in self.tokens[tok_id].value:
                ret_str += "    " * self.cur_indent + "fgoDevice.device.perform(' ',(2100,))\n" + \
                           "    " * self.cur_indent + "fgoDevice.device.perform(self." + self.tokens[tok_id].value + "("
                tok_id += 1
                while tok_id < action_tok_ed:
                    ret_str += self.tokens[tok_id].value + ","
                    tok_id += 1
                ret_str += "),(300,300,2300,1300,6000))\n" + \
                           "    " * self.cur_indent + "return\n"
            elif self.tokens[tok_id].type == COMMA:
                tok_id += 1
            else:
                raise RuntimeError(f"Unexpected token {self.tokens[tok_id].value} in action block at line {self.tokens[tok_id].line}")
        return ret_str

    def generateCustiomizedSelectCard(self, s_st_str: str, info: SelectCardInfo) -> str:
        def _generateColorCombs(toks_st, toks_ed):  # num_cards, [[(servant, color){1,2}], ...(different priorities)]
            cards = 0
            color_combs = []
            if toks_st < toks_ed:
                seps = [toks_st,]
                depth = 0
                for i in range(toks_st, toks_ed):
                    if self.tokens[i].type == COMMA and depth == 0:
                        seps.append(i + 1)
                    elif self.tokens[i].type == LPAREN:
                        depth += 1
                    elif self.tokens[i].type == RPAREN:
                        depth -= 1
                seps.append(toks_ed)
                for i, start in enumerate(seps[:-1]):
                    this_priority_servant_color_combs = []  # length = 1 or 2 or 3
                    for j in range(start, seps[i + 1]):
                        servant, color = -1, '*'
                        if self.tokens[j].type == DOT:
                            if self.tokens[j - 1].type == INT and int(self.tokens[j - 1].value) in [0, 1, 2]:
                                servant = int(self.tokens[j - 1].value)
                            else:
                                assert self.tokens[j - 1].type == STAR, \
                                    f"Expected 0, 1, 2 or *, got {self.tokens[j - 1].value} at line {self.tokens[j - 1].line}."
                            if self.tokens[j + 1].type == KEYWORDS and self.tokens[j + 1].value in ['r', 'g', 'b']:
                                color = self.tokens[j + 1].value.lower()
                            else:
                                assert self.tokens[j + 1].type == STAR, \
                                    f"Expected r, g, b or *, got {self.tokens[j + 1].value} at line {self.tokens[j + 1].line}."
                        elif self.tokens[j].type == STAR and (j == 0 or self.tokens[j-1].value != '.') and \
                                (j == len(self.tokens) - 1 or self.tokens[j+1].value != '.'):
                            pass
                        else:
                            continue
                        this_priority_servant_color_combs.append((servant, color))
                    if cards <= 0:
                        cards = len(this_priority_servant_color_combs)
                    color_combs.append(this_priority_servant_color_combs)
            return cards, color_combs
        def _appendSelectCardFunc(pre_or_post : str, pre_or_post_servant_color_combs):
            ret_str = f"        def {pre_or_post}_evaluate(card):\n" + \
                      ' ' * 12 + "mark = -10000\n"
            for priority, servant_color_combs in enumerate(pre_or_post_servant_color_combs):
                cond_str = ""
                for i, (servant, color) in enumerate(servant_color_combs):
                    if i > 0:
                        cond_str += " and "
                    if servant != -1:
                        cond_str += f"group[card[{i}]] == {servant}"
                    else:
                        cond_str += "True"
                    cond_str += " and "
                    if color != '*':
                        if color == "b":
                            cond_str += f"color[card[{i}]] == 0"
                        elif color == "g":
                            cond_str += f"color[card[{i}]] == 1"
                        elif color == "r":
                            cond_str += f"color[card[{i}]] == 2"
                        else:
                            raise RuntimeError(f"Unknown card color: {color}")
                    else:
                        cond_str += "True"
                cond_str += f": mark={-priority}\n"
                ret_str += ' ' * 12 + ("el" if priority != 0 else "") + "if " + cond_str
            ret_str += ' ' * 12 + "return mark\n"
            return ret_str

        if info.preprogrammed_selectCard != "":
            return ""
            # currently have to ignore target since target selection code can't be inserted into a pre-written selectCard function
        post_cards, post_servant_color_combs = _generateColorCombs(info.post_toks_st, info.post_toks_ed)
        pre_cards, pre_servant_color_combs = _generateColorCombs(info.pre_toks_st, info.pre_toks_ed)
        assert pre_cards + post_cards + len(info.hougu_servants) == 3 or (pre_cards == 0 and post_cards == 0), \
            "Total selected cards (pre + hougu + post) must be 3. If only hougu is specified while pre and post are not, " \
            "random cards after casting hougu will be selected. It's illegal if non of these two circumstances are met.\n\n" \
            f"Detected: pre={' '.join([self.tokens[i].value for i in range(info.pre_toks_st, info.pre_toks_ed)])}, post=" \
            f"{' '.join([self.tokens[i].value for i in range(info.post_toks_st, info.post_toks_ed)])}, hougu_servants={info.hougu_servants}"
        ret_str = \
f'''
    @logit(logger,logging.INFO)
    def selectCard_{s_st_str}(self):
''' \
r'''        color,sealed,hougu,np,resist,critical,group=Detect().getCardColor()+[i[5][1]for i in self.servant],Detect.cache.isCardSealed(),Detect.cache.isHouguReady(),[Detect.cache.getFieldServantNp(i)<100 for i in range(3)],[[1,1.7,.6][i]for i in Detect.cache.getCardResist()],[i/10 for i in Detect.cache.getCardCriticalRate()],[next(j for j,k in enumerate(self.servant)if k[0]==i)for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]
        houguTargeted,houguArea,houguSupport=[[j for j in range(3)if hougu[j]and self.servant[j][0]and self.servant[j][5][0]==i]for i in range(3)]
        houguArea=houguArea if self.stage==self.stageTotal or sum(i>0 for i in self.enemy)>1 and sum(self.enemy)>12000 else[]
        houguTargeted=houguTargeted if self.stage==self.stageTotal or max(self.enemy)>23000+8000*len(houguArea)else[]
        hougu=[i+5 for i in houguSupport+houguArea+houguTargeted]
        if self.stageTurn==1 or houguTargeted or self.enemy[self.target]==0:
            self.target=numpy.argmax(self.enemy)
            fgoDevice.device.perform('\x67\x68\x69\x64\x65\x66'[self.target],(500,))
        self.enemy=[max(0,i-18000*len(houguArea))for i in self.enemy]
        if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
        for _ in houguTargeted:
            self.enemy[self.target]=max(0,self.enemy[self.target]-48000)
            if any(self.enemy)and self.enemy[self.target]==0:self.target=next(i for i in range(5,-1,-1)if self.enemy[i])
''' + \
(r"""
        fgoDevice.device.perform('\x67\x68\x69\x64\x65\x66'""" f"[{info.target}],(500,))\n" if info.target >= 0 else "")
        ret_str += _appendSelectCardFunc("pre", pre_servant_color_combs)
        ret_str += _appendSelectCardFunc("post", post_servant_color_combs)
        ret_str += (' ' * 8 + "pre_card=" + (f"list(max(permutations(range(5),{pre_cards}),key=lambda x:pre_evaluate(list(x))))\n" if pre_cards > 0 else "[]\n")) + \
                   (' ' * 8 + "post_card=" + (r"list(max(permutations({0,1,2,3,4}-set(pre_card)," f"{post_cards}),key=lambda x:post_evaluate(list(x))))\n" if post_cards > 0 else "[]\n")) + \
                   ' '* 8 + "return''.join(['12345678'[i]for i in pre_card+" f"{[5+hougu_servant for hougu_servant in info.hougu_servants]}" r"+post_card+list({0,1,2,3,4}-set(post_card)-set(pre_card))])"
        return ret_str

    def generateCustomizedTurn(self):
        self.pos = 0
        first_s_st = True
        this_s_st_str = ""
        select_card_id_for_this_s_st = 0
        to_replace_toks = {}
        this_info = SelectCardInfo()
        select_card_info_map = {}

        while self.pos < len(self.tokens):
            cur_tok = self.tokens[self.pos]
            if cur_tok.type == INDENT:
                self.cur_indent += 1
                self.pos += 1
            elif cur_tok.type == DEDENT:
                self.cur_indent -= 1
                self.pos += 1
            elif cur_tok.type == HINTWORDS and cur_tok.value in {"s", "st"}:
                # reset some info when seeing a new stage/stageTurn
                if not this_info.empty():
                    select_card_info_map[this_s_st_str + "_" + str(select_card_id_for_this_s_st)] = this_info
                    this_info = SelectCardInfo()
                    select_card_id_for_this_s_st = 0
                pos_of_colon = self.peek_until(self.pos,[':'])

                # info about stage/stageTurn
                stage, stageTurn = -1, -1
                while self.pos < pos_of_colon:
                    cur_tok = self.tokens[self.pos]
                    if cur_tok.value == "s":
                        stage = int(self.tokens[self.pos + 1].value)
                        self.pos += 2
                    elif cur_tok.value == "st":
                        stageTurn = int(self.tokens[self.pos + 1].value)
                        self.pos += 2
                    else:
                        assert False, f"Unexpected keyword {cur_tok.value} when expecting s/st (stage/stageTurn)"
                # consume COLON and NEWLINE
                self.pos += 2
                self.class_str += '    ' * self.cur_indent + ("elif" if not first_s_st else "if") + \
                                  (f" self.stage == {stage}" if stage >= 1 else "") + \
                                  (f" and" if stage >= 1 and stageTurn >= 1 else "") + \
                                  (f" self.stageTurn == {stageTurn}" if stageTurn >= 1 else "") + ":\n"
                first_s_st = False
                this_s_st_str = (f"s{stage}" if stage >= 1 else "") + (f"st{stageTurn}" if stageTurn >= 1 else "")
                get_card_info_inserted_for_this_s_st = False
                exists_flag_num = 0
                to_replace_toks = {}    # key: start_token_id, value: (end_token_id, replaced_str); to replace tokens[key, end)
                                        # replaced_expr can be a flag or a subexpression like 0.np (np[0])
                try_tok_id = self.pos
                while try_tok_id < len(self.tokens):
                    if self.tokens[try_tok_id].value in ["s", "st"]:
                        break
                    elif self.tokens[try_tok_id].value in ["if", "elif", "else"]:
                        while self.tokens[try_tok_id].type != COLON:
                            if self.tokens[try_tok_id].value == "exists":
                                exist_tokid = try_tok_id
                                servant, card = -1, "*"
                                count = 1
                                while self.tokens[try_tok_id].type != COLON:
                                    if self.tokens[try_tok_id].value == "x":
                                        # find out whether COUNT is on the left or right of 'x'
                                        if self.tokens[try_tok_id - 1].value in {"r", "g", "b", "*"}:
                                            count = int(self.tokens[try_tok_id + 1].value)
                                        else:
                                            count = int(self.tokens[try_tok_id - 1].value)
                                    elif self.tokens[try_tok_id].type == DOT:
                                        servant = int(self.tokens[try_tok_id - 1].value) if self.tokens[try_tok_id - 1].type == INT else -1
                                        card = self.tokens[try_tok_id + 1].value

                                    elif self.tokens[try_tok_id].type == RPAREN:
                                        to_replace_toks[exist_tokid] = (try_tok_id + 1, f"flag_{exists_flag_num}")
                                        break
                                    try_tok_id += 1
                                if servant != -1 or card in ["r", "g", "b"]:
                                    if not get_card_info_inserted_for_this_s_st:
                                        get_card_info_inserted_for_this_s_st = True
                                        self.class_str += "    " * (self.cur_indent + 1) + "fgoDevice.device.perform(' ',(2100,))\n" + \
                                                          "    " * (self.cur_indent + 1) + \
                                                          "color,sealed,hougu,np,resist,critical,group=" \
                                                          "Detect().getCardColor()+[i[5][1]for i in self.servant],Detect.cache.isCardSealed()," \
                                                          "Detect.cache.isHouguReady(),[Detect.cache.getFieldServantNp(i)<100 for i in range(3)]," \
                                                          "[[1,1.7,.6][i]for i in Detect.cache.getCardResist()]," \
                                                          "[i/10 for i in Detect.cache.getCardCriticalRate()]," \
                                                          "[next(j for j,k in enumerate(self.servant)if k[0]==i)" \
                                                          "for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]\n" + \
                                                          "    " * (self.cur_indent + 1) + "fgoDevice.device.perform(' ',(2100,))\n"

                                    servant_str = f"group[i]=={servant}" if servant != -1 else ""
                                    color_str = f"color[i]=={0 if card == 'b' else (1 if card == 'g' else 2)}" if card in {"r", "g", "b"} else "True"
                                    cond_str = servant_str + (" and " + color_str if servant_str and color_str else color_str)
                                    self.class_str += "    " * (self.cur_indent + 1) + f"count_{exists_flag_num} = 0\n" + \
                                                      "    " * (self.cur_indent + 1) + "for i in range(5):\n" + \
                                                      "    " * (self.cur_indent + 2) + "if " + cond_str + ":\n" + \
                                                      "    " * (self.cur_indent + 3) + f"count_{exists_flag_num} += 1\n" + \
                                                      "    " * (self.cur_indent + 1) + f"flag_{exists_flag_num} = count_{exists_flag_num} >= {count}\n"
                                else:   # invalid condition, let it always be true
                                    self.class_str += "    " * (self.cur_indent + 1) + f"flag_{exists_flag_num} = True\n"
                                exists_flag_num += 1
                                continue
                            elif self.tokens[try_tok_id].type == DOT:
                                attribute = self.tokens[try_tok_id + 1].value
                                assert attribute in {"np"}  # todo: should check this in Validator
                                to_replace_toks[try_tok_id - 1] = (try_tok_id + 2, f"{attribute}[{self.tokens[try_tok_id - 1].value}]")
                                try_tok_id += 2
                                continue

                            try_tok_id += 1
                    else:
                        try_tok_id += 1
            elif cur_tok.value in {"if", "elif", "else"}:
                if (cur_tok.value == "else" or cur_tok.value == "elif") and not this_info.empty():
                    # If this_info is non-empty when encountering "else" or "elif",
                    # we assume the user has finished specifying the previous selectCard info.
                    # the calling of selectCard_xxx() has been inserted when parsing "hougu"
                    select_card_info_map[this_s_st_str + "_" + str(select_card_id_for_this_s_st)] = this_info
                    this_info = SelectCardInfo()
                    select_card_id_for_this_s_st += 1

                self.class_str += "    " * self.cur_indent + cur_tok.value + " "
                tok_id = self.pos + 1
                while self.tokens[tok_id].type != NEWLINE:
                    if tok_id in to_replace_toks:
                        end, replaced_str = to_replace_toks[tok_id]
                        self.class_str += " " + replaced_str
                        tok_id = end
                    else:
                        self.class_str += " " + self.tokens[tok_id].value
                        tok_id += 1
                self.class_str += "\n"
                self.pos = tok_id + 1   # consume NEWLINE
            elif cur_tok.value == "hougu":
                tok_id = self.pos + 1
                hougu_servants = []
                while self.tokens[tok_id].type != NEWLINE:
                    if self.tokens[tok_id].type == INT:
                        hougu_servants.append(int(self.tokens[tok_id].value))
                    tok_id += 1
                this_info.hougu_servants = hougu_servants
                self.class_str += "    " * self.cur_indent + "fgoDevice.device.perform(' ',(2100,))\n" + \
                                  "    " * self.cur_indent + "fgoDevice.device.perform(self.selectCard" + "_" + \
                                  this_s_st_str + "_" + str(select_card_id_for_this_s_st) + "(),(300,300,2300,1300,6000))\n"
                self.pos = tok_id + 1   # consume NEWLINE
            elif cur_tok.value == "pre":
                this_info.pre_toks_st = self.pos + 2
                this_info.pre_toks_ed = self.peek_until(self.pos + 2, ["\\n"])
                self.pos = this_info.pre_toks_ed + 1    # consume NEWLINE
            elif cur_tok.value == "post":
                this_info.post_toks_st = self.pos + 2
                this_info.post_toks_ed = self.peek_until(self.pos + 2, ["\\n"])
                self.pos = this_info.post_toks_ed + 1   # consume NEWLINE
            elif cur_tok.value == "target":
                this_info.target = int(self.tokens[self.pos + 2].value)
                self.pos += 4
            elif cur_tok.type == NEWLINE:
                assert False, f"standalone NEWLINE should've been eliminated in the tokenizing process @line {cur_tok.line}"
            else:
                eol = self.peek_until(self.pos, ["\\n"])
                if re.search("^selectCard", cur_tok.value):
                    # we may need this info to guide selectCard generation apart from selectCard calling
                    this_info.preprogrammed_selectCard = cur_tok.value
                    this_info.selectCard_params = self.tokens[self.pos + 1 : eol]
                self.class_str += self.parseActionString(self.pos, eol)
                self.pos = eol + 1

        if not this_info.empty():
            # when the input ends, save the previous stage/turn
            select_card_info_map[this_s_st_str + "_" + str(select_card_id_for_this_s_st)] = this_info
        self.class_str += '        else:\n' \
                          '            self.dispatchSkill()\n' \
                          '            fgoDevice.device.perform(" ",(2100,))\n' \
                          '            fgoDevice.device.perform(self.selectCard(),(300,300,2300,1300,6000))\n'

        # generate selectCard_*() methods
        for s_st_str, this_info in select_card_info_map.items():
            self.class_str += self.generateCustiomizedSelectCard(s_st_str, this_info)


def generateCustomizedTurn(file):
    turn_name = os.path.basename(file)[:file.rfind('.')] + "Turn"

    cmd_lines = []
    with open(file) as fp:
        raw_cmd_lines = fp.readlines()

    # preprocessing
    for i in range(len(raw_cmd_lines)):
        # use regex to add spaces to separate letters and numbers
        cmd_lines.append(raw_cmd_lines[i].split('#')[0].rstrip() + '\n')

    tokens = list(tokenize(''.join(cmd_lines)))

    # postprocessing
    postproc_tokens = []
    branch_line_not_ended = False
    for tok_id, tok in enumerate(tokens):
        postproc_tokens.append(tok)
        if tok.type == KEYWORDS and tok.value in {"if", "else", "elif"}:
            branch_line_not_ended = True
        elif tok.type == COLON and branch_line_not_ended:
            if tokens[tok_id + 1].type == NEWLINE:
                branch_line_not_ended = False
            else:
                # if there is an expression after the colon in the same line, we insert a NEWLINE and an INDENT to make it a block
                postproc_tokens.append(Token(type=NEWLINE, value="\\n", line=tok.line, column=tok.column))
                postproc_tokens.append(Token(type=INDENT, value="", line=tok.line, column=tok.column))
        elif tok.type == NEWLINE and branch_line_not_ended:
            postproc_tokens.append(Token(type=DEDENT, value="", line=tok.line, column=tok.column))
            branch_line_not_ended = False

    tokens, postproc_tokens = postproc_tokens, []
    this_cmd_line_is_s_st = False
    inserted_indent_after_s_st_line = False
    for tok_id, tok in enumerate(tokens[:-1]):
        if tok.type == HINTWORDS and tok.value in {"s", "st"}:
            if inserted_indent_after_s_st_line:
                postproc_tokens.append(Token(type=DEDENT, value="", line=tok.line, column=tok.column))
                inserted_indent_after_s_st_line = False
            postproc_tokens.append(tok)
            this_cmd_line_is_s_st = True
        elif tok.type == NEWLINE:
            if this_cmd_line_is_s_st and tokens[tok_id + 1].type != INDENT:
                postproc_tokens.append(tok)
                postproc_tokens.append(Token(type=INDENT, value="", line=tok.line, column=tok.column))
                inserted_indent_after_s_st_line = True
            else:
                postproc_tokens.append(tok)
            this_cmd_line_is_s_st = False
        else:
            postproc_tokens.append(tok)
    postproc_tokens.append(tokens[-1])
    if inserted_indent_after_s_st_line:
        postproc_tokens.append(Token(type=DEDENT, value="", line=tokens[-1].line, column=tokens[-1].column))

    try:
        validator = SyntaxValidator(postproc_tokens)
        validator.validate()
    except SyntaxError as e:
        print(f"Error: {e}")
        exit()

    generator = CustomizedTurnGenerator(postproc_tokens, turn_name)
    generator.generateCustomizedTurn()
    return generator.class_str


if __name__ == '__main__':
    out_str = generateCustomizedTurn("WhitePaper90SS.txt")
    with open("WhitePaper90SS.py", "w", encoding="utf-8") as f:
        f.write(out_str)
