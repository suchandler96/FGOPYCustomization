import re
from typing import NamedTuple, Iterator, List

FIXED_BASE_INDENT = 8

class Token(NamedTuple):
    type: str
    value: str
    line: int
    column: int

class SelectCardInfo(NamedTuple):
    target: int
    hougu_servants: list
    pre_eval_str: str
    post_eval_str: str
    preprogrammed_selectCard: str = ""

    def empty(self):
        return self.target < 0 and len(self.hougu_servants) == 0 and self.pre_eval_str == "" and \
            self.post_eval_str == "" and self.preprogrammed_selectCard == ""

def tokenize(code: str) -> Iterator[Token]:
    token_specification = [
        ('COMMENT',  r'#[^\n]*'),             # Comments
        # ('FLOAT',    r'\d+\.\d+'),            # Decimal numbers
        ('INT',      r'\d+'),                 # Integer numbers
        ('KEYWORDS', r'\b(if|else|elif|and|or|not|exists|x)\b'), # Keywords
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
            yield Token(kind, '\\n', line_num, col)
            pos = mo.end()
            continue

        elif kind == 'SKIP':
            # If we are not at the start of the line, just ignore whitespace
            if not at_line_start:
                pos = mo.end()
                continue

            # If we ARE at start of line, calculate indentation
            indent_level = len(value) # Assuming spaces (1 char = 1 unit)
            # (In a real production parser, you'd handle tabs vs spaces checks here)
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

        # --- INDENTATION LOGIC ---
        if at_line_start:
            # We hit a real token (not newline/skip/comment)
            # Calculate column based on where this token actually starts
            current_indent = col

            if current_indent > indent_stack[-1]:
                indent_stack.append(current_indent)
                yield Token('INDENT', '', line_num, 0)
            elif current_indent < indent_stack[-1]:
                while current_indent < indent_stack[-1]:
                    indent_stack.pop()
                    yield Token('DEDENT', '', line_num, 0)
                if current_indent != indent_stack[-1]:
                    raise IndentationError(f"Unindent does not match any outer indentation level at line {line_num}")

            at_line_start = False

        if kind == 'MISMATCH':
            raise RuntimeError(f'Unexpected char {value!r} at line {line_num}')

        yield Token(kind, value, line_num, col)
        pos = mo.end()

    # End of file: Deduce remaining indents
    while len(indent_stack) > 1:
        indent_stack.pop()
        yield Token('DEDENT', '', line_num, 0)


class SyntaxValidator:
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.pos = 0
        # Tracks if an 'if' was seen at a specific indentation level
        # Key: Indent Level, Value: Boolean (True if an IF is active/pending)
        self.scope_has_if = {}
        self.current_indent_level = 0

    def current(self) -> Token:
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

    def validate(self):
        while self.get_pos() < len(self.tokens):
            token = self.current()

            if token.type == 'INDENT':
                self.current_indent_level += 1
                self.advance()

            elif token.type == 'DEDENT':
                # When leaving a block, reset the "if" memory for the inner level
                if self.current_indent_level in self.scope_has_if:
                    del self.scope_has_if[self.current_indent_level]
                self.current_indent_level -= 1
                self.advance()

            elif token.type == 'KEYWORDS' and token.value == 'if':
                self.handle_if()
            elif token.type == 'KEYWORDS' and token.value == 'else':
                self.handle_else()
            elif token.type == 'KEYWORDS' and token.value == 'elif':
                self.handle_elif()
            elif token.type == 'KEYWORDS' and token.value == 'x':
                self.handle_x()
            else:
                # Skip other tokens (expressions, assignments, etc.)
                self.advance()

    def handle_x(self):
        """
        Rule: 'x' must be preceded by 'exists' keyword.
        """
        line = self.current().line
        if not (self.peek(-3).value == 'exists' and self.peek(-2).value == '(' and self.peek(-1).type == 'INT' and
                self.peek(1).type in {"STAR", "INT"} and self.peek(2).type == "DOT" and self.peek(3).type in {"STAR", "INT"}):
            raise SyntaxError(f"Line {line}: Syntax of 'x': exists(_count_ x _servant_._color_)")

        self.advance()

    def handle_if(self):
        """
        Rule: Check for colon, then check for newline vs inline expression.
        Also marks this indentation level as having an active 'if'.
        """
        line = self.current().line
        cur_pos = self.get_pos()
        self.scope_has_if[self.current_indent_level] = True

        # Scan forward to find the colon
        while self.get_pos() < len(self.tokens) and self.current().type != 'COLON':
            if self.current().type == 'NEWLINE':
                raise SyntaxError(f"Line {line}: 'if' statement missing colon before newline.")
            self.advance()
        if self.get_pos() >= len(self.tokens) or self.current().type != 'COLON':
            raise SyntaxError(f"Line {line}: 'if' statement missing colon.")

        self.advance() # consume COLON

        # RULE: "either there should be some expressions in this line or an indent"
        next_tok = self.current()

        if next_tok.type == 'NEWLINE':
            # If newline immediately follows colon, next token MUST be INDENT
            if self.peek().type != 'INDENT':
                raise SyntaxError(f"Line {line}: Expected 4-space indent after 'if' statement on new line.")
        else:
            # Inline expression (e.g., "if x: y = 1")
            pass
        self.set_pos(cur_pos + 1)

    def handle_else(self):
        """
        Rule: Must be an 'if' at the same indent level immediately before.
        """
        line = self.current().line

        # Check if we have a matching IF at this level
        if not self.scope_has_if.get(self.current_indent_level, False):
            raise SyntaxError(f"Line {line}: 'else' without matching 'if' at this indentation level.")

        # Reset because the if-else block is essentially consumed/linked now
        # (Allows 'if... else... if...' chains if needed, though simple else usually ends it)
        self.scope_has_if[self.current_indent_level] = False
        self.advance()

    def handle_elif(self):
        """
        Rule: Must be an 'if' or 'elif' at the same indent level immediately before.
              Check for colon, then check for newline vs inline expression.
        """
        line = self.current().line
        cur_pos = self.get_pos()
        # Check if we have a matching IF or ELIF at this level
        if not self.scope_has_if.get(self.current_indent_level, False):
            raise SyntaxError(f"Line {line}: 'elif' without matching 'if' at this indentation level.")

        # Keep the 'if' active for further 'elif' or 'else'
        self.advance()

        # Scan forward to find the colon
        while self.get_pos() < len(self.tokens) and self.current().type != 'COLON':
            if self.current().type == 'NEWLINE':
                raise SyntaxError(f"Line {line}: 'if' statement missing colon before newline.")
            self.advance()
        if self.get_pos() >= len(self.tokens) or self.current().type != 'COLON':
            raise SyntaxError(f"Line {line}: 'if' statement missing colon.")

        self.advance() # consume COLON

        # RULE: "either there should be some expressions in this line or an indent"
        next_tok = self.current()

        if next_tok.type == 'NEWLINE':
            # If newline immediately follows colon, next token MUST be INDENT
            if self.peek().type != 'INDENT':
                raise SyntaxError(f"Line {line}: Expected 4-space indent after 'if' statement on new line.")
        else:
            # Inline expression
            pass
        self.set_pos(cur_pos + 1)


def parseActionString(indent: int, action_str: str, class_str: str):
    action_tokens = list(tokenize(action_str))
    tok_id = 0
    while tok_id < len(action_tokens):
        if action_tokens[tok_id].type == "INT":             # servant_id
            assert action_tokens[tok_id + 1].type == "DOT"
            assert action_tokens[tok_id + 2].type == "INT"  # skill_id
            servant_id = int(action_tokens[tok_id].value)
            skill_id = int(action_tokens[tok_id + 2].value)
            if tok_id + 4 < len(action_tokens) and action_tokens[tok_id + 3].value == ">":
                assert action_tokens[tok_id + 4].type == "INT"  # target
                target = int(action_tokens[tok_id + 4].value)
                tok_id += 5
            else:
                target = -1
                tok_id += 3
            class_str += ' ' * indent + f"self.castSingleOrNoTargetServantSkill({servant_id}, {skill_id}, {target})\n"
        elif action_tokens[tok_id].value == "m" or action_tokens[tok_id].value == "M":  # master skill
            assert action_tokens[tok_id + 1].type == "DOT"
            assert action_tokens[tok_id + 2].type == "INT"  # skill_id
            skill_id = int(action_tokens[tok_id + 2].value)
            targets = []
            if action_tokens[tok_id + 3].value == ">":
                if action_tokens[tok_id + 4].type == "INT":
                    targets.append(int(action_tokens[tok_id + 4].value))
                    tok_id += 5
                else:   # multiple targets
                    assert action_tokens[tok_id + 4].value == "("
                    j = tok_id + 5
                    while j < len(action_tokens):
                        if action_tokens[j].type == "INT":
                            targets.append(int(action_tokens[j].value))
                        elif action_tokens[j].value == ")":
                            break
                        j += 1
                    tok_id = j + 1
            class_str += ' ' * indent + f"self.castMasterSkill({skill_id}, " + (f"{targets}" if len(targets) > 0 else "") + ")\n"
        elif "selectCard" in action_tokens[tok_id].value:
            class_str += ' ' * indent + "fgoDevice.device.perform(' ',(2100,))\n" + \
                         ' ' * indent + "fgoDevice.device.perform(self." + action_tokens[tok_id].value + "("
            tok_id += 1
            while tok_id < len(action_tokens):
                class_str += action_tokens[tok_id].value + ","
                tok_id += 1
            class_str += "),(300,300,2300,1300,6000))\n" + \
                         ' ' * indent + "return\n"
        else:
            tok_id += 1
    return indent, class_str


def generateCustiomizedSelectCard(s_st_str: str, info: SelectCardInfo, class_str: str) -> str:
    def _generateColorCombs(eval_str: str):     # num_cards, [[(servant, color){1,2}], ...(different priorities)]
        cards = 0
        color_combs = []
        if eval_str != "":
            eval_tokens = list(tokenize(eval_str))
            seps = [0,]
            depth = 0
            for i, tok in enumerate(eval_tokens):
                if tok.value == ',' and depth == 0:
                    seps.append(i + 1)
                elif tok.value == '(':
                    depth += 1
                elif tok.value == ')':
                    depth -= 1
            seps.append(len(eval_tokens))
            for i, start in enumerate(seps[:-1]):
                this_priority_servant_color_combs = []  # length = 1 or 2 or 3
                for j in range(start, seps[i + 1]):
                    servant, color = -1, '*'
                    if eval_tokens[j].value == '.':
                        if eval_tokens[j - 1].type == "INT":
                            servant = int(eval_tokens[j - 1].value)
                        else:
                            assert eval_tokens[j - 1].value == '*'
                        if eval_tokens[j + 1].type == "ID":
                            color = eval_tokens[j + 1].value.lower()
                        else:
                            assert eval_tokens[j + 1].value == '*'
                    elif eval_tokens[j].value == '*' and (j == 0 or eval_tokens[j-1].value != '.') and \
                            (j == len(eval_tokens) - 1 or eval_tokens[j+1].value != '.'):
                        pass
                    else:
                        continue
                    this_priority_servant_color_combs.append((servant, color))
                if cards <= 0:
                    cards = len(this_priority_servant_color_combs)
                color_combs.append(this_priority_servant_color_combs)
        return cards, color_combs
    def _appendSelectCardFunc(class_str : str, pre_or_post : str, pre_or_post_servant_color_combs):
        class_str += f"        def {pre_or_post}_evaluate(card):\n"
        class_str += ' ' * 12 + "mark = -10000\n"
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
            class_str += ' ' * 12 + ("el" if priority != 0 else "") + "if " + cond_str
        class_str += ' ' * 12 + "return mark\n"
        return class_str

    if info.preprogrammed_selectCard != "":
        return class_str
        # currently have to ignore target since target selection code can't be inserted into a pre-written selectCard function
    post_cards, post_servant_color_combs = _generateColorCombs(info.post_eval_str)
    pre_cards, pre_servant_color_combs = _generateColorCombs(info.pre_eval_str)
    assert pre_cards + post_cards + len(info.hougu_servants) == 3 or (pre_cards == 0 and post_cards == 0)
    class_str += \
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
    class_str = _appendSelectCardFunc(class_str, "pre", pre_servant_color_combs)
    class_str = _appendSelectCardFunc(class_str, "post", post_servant_color_combs)
    class_str += (' ' * 8 + "pre_card=" + (f"list(max(permutations(range(5),{pre_cards}),key=lambda x:pre_evaluate(list(x))))\n" if pre_cards > 0 else "[]\n")) + \
                 (' ' * 8 + "post_card=" + (r"list(max(permutations({0,1,2,3,4}-set(pre_card)," f"{post_cards}),key=lambda x:post_evaluate(list(x))))\n" if post_cards > 0 else "[]\n")) + \
                 ' '* 8 + "return''.join(['12345678'[i]for i in pre_card+" f"{[5+hougu_servant for hougu_servant in info.hougu_servants]}" r"+post_card+list({0,1,2,3,4}-set(post_card)-set(pre_card))])"
    return class_str

def generateCustomizedTurn(file):
    class_str = \
r'''class GeneratedCustomTurn(CustomTurn):
    def __init__(self):
        super(GeneratedCustomTurn, self).__init__()
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
    indent = 8
    inTurnBranch = False
    this_s_st_str = ""
    this_info = SelectCardInfo(target=-1, hougu_servants=[], pre_eval_str="", post_eval_str="")
    select_card_info_map = {}
    last_cmd_line_indent, this_cmd_line_indent = 0, 0

    cmd_lines = []
    with open(file) as fp:
        raw_cmd_lines = fp.readlines()
        raw_str = ''.join(raw_cmd_lines)

    try:
        tokens = list(tokenize(raw_str))
        validator = SyntaxValidator(tokens)
        validator.validate()

    except (SyntaxError, IndentationError) as e:
        print(f"Error: {e}")

    for i in range(len(raw_cmd_lines)):
        cmd_line = raw_cmd_lines[i].split('#')[0]
        if len(cmd_line.strip()) > 0:
            cmd_lines.append(cmd_line)

    for line_id, cmd_line in enumerate(cmd_lines):
        this_cmd_line_indent = len(re.search(r"^(\s*)", cmd_line).group(1))
        indent += (this_cmd_line_indent - last_cmd_line_indent)

        if turn_start_match := re.search(r"^\s*([sStT])+(\d+)([STst]{0,2})(\d*):\s*$", cmd_line):
            indent = FIXED_BASE_INDENT
            assert turn_start_match.group(1).lower() == 's', \
                f"At line {line_id + 1}, detected " \
                f"{turn_start_match.group(1) + turn_start_match.group(2) + turn_start_match.group(3) + turn_start_match.group(4)}, " \
                "but s*(st*) is expected: (stage * stageTurn *).\n"
            assert turn_start_match.group(3).lower() in {'', 'st'}, "st is expected to indicate stageTurn.\n"
            class_str += ' ' * indent + ("el" if inTurnBranch else "") + "if self.stage==" + turn_start_match.group(2) + \
                         (" and self.stageTurn==" + turn_start_match.group(4) if turn_start_match.group(4) else "") + ":\n"
            inTurnBranch = True
            if not this_info.empty():   # when starting a new turn/stage, save the previous one
                select_card_info_map[this_s_st_str] = this_info
                this_info = SelectCardInfo(target=-1, hougu_servants=[], pre_eval_str="", post_eval_str="")
            this_s_st_str = cmd_line.strip().replace(":", "")
            get_card_info_str_inserted = False
            exists_flag_num = 0
            to_replace_toks = {}    # key = (line_id, start_token_id), value = (end, replaced_expr); to replace tokens[key, end)
            # replaced_expr can be a flag or a subexpression like 0.np (np[0])

            # Check whether we need to peek the cards for this turn/stage.
            # If yes, insert the code to peek cards and get flag values.
            for line_j in range(line_id + 1, len(cmd_lines)):
                if re.search(r"^\s*[sS](\d+)([STst]{0,2})(\d*):\s*$", cmd_lines[line_j]):
                    break   # stop when next turn/stage starts
                elif cond_match := re.search(r"^(\s*)([elifs]{2,4})\s*(.*):\s*(.*)$", cmd_lines[line_j]):
                    # insert get_card_info string
                    assert cond_match.group(2) in {"if", "else", "elif"}
                    condition_tokens = list(tokenize(cond_match.group(3)))
                    tok_id = 0
                    while tok_id < len(condition_tokens):
                        if condition_tokens[tok_id].value == "exists":
                            j = tok_id + 1
                            exist_tokid = tok_id
                            servant, card = -1, ""
                            count = 1
                            while j < len(condition_tokens):
                                if condition_tokens[j].value == 'x':
                                    assert condition_tokens[j-1].type == "INT", "Invalid exists() condition"
                                    count = int(condition_tokens[j-1].value)
                                elif condition_tokens[j].value == '.':
                                    servant = int(condition_tokens[j-1].value if condition_tokens[j-1].type == "INT" else -1)
                                    card = condition_tokens[j+1].value.lower() if j+1 < len(condition_tokens) else ""
                                    if servant != -1 or card in {"r", "g", "b"}:
                                        if not get_card_info_str_inserted:
                                            get_card_info_str_inserted = True
                                            class_str += ' ' * (indent + 4) + "fgoDevice.device.perform(' ',(2100,))\n" + \
                                                         ' ' * (indent + 4) + \
                                                         "color,sealed,hougu,np,resist,critical,group=" \
                                                         "Detect().getCardColor()+[i[5][1]for i in self.servant],Detect.cache.isCardSealed()," \
                                                         "Detect.cache.isHouguReady(),[Detect.cache.getFieldServantNp(i)<100 for i in range(3)]," \
                                                         "[[1,1.7,.6][i]for i in Detect.cache.getCardResist()]," \
                                                         "[i/10 for i in Detect.cache.getCardCriticalRate()]," \
                                                         "[next(j for j,k in enumerate(self.servant)if k[0]==i)" \
                                                         "for i in Detect.cache.getCardServant([i[0] for i in self.servant if i[0]])]+[0,1,2]\n" + \
                                                         ' ' * (indent + 4) + "fgoDevice.device.perform(' ',(2100,))\n"

                                        servant_str = f"group[i]=={servant}" if servant != -1 else ""
                                        color_str = f"color[i]=={0 if card == 'b' else (1 if card == 'g' else 2)}" if card in {"r", "g", "b"} else "True"
                                        cond_str = servant_str + (" and " + color_str if servant_str and color_str else color_str)
                                        class_str += " " * (indent + 4) + f"count_{exists_flag_num} = 0\n" + \
                                                     " " * (indent + 4) + "for i in range(5):\n" + \
                                                     " " * (indent + 8) + "if " + cond_str + ":\n" + \
                                                     " " * (indent + 12) + f"count_{exists_flag_num} += 1\n" + \
                                                     " " * (indent + 4) + f"flag_{exists_flag_num} = count_{exists_flag_num} >= {count}\n"
                                    else:   # invalid condition, let it always be true
                                        class_str += " " * (indent + 4) + f"flag_{exists_flag_num} = True\n"
                                elif condition_tokens[j].value == ')':
                                    to_replace_toks[(line_j, exist_tokid)] = (j + 1, f"flag_{exists_flag_num}")
                                    exists_flag_num += 1
                                    break
                                j += 1
                            tok_id = j + 1
                            continue
                        elif condition_tokens[tok_id].value == ".":
                            attribute = condition_tokens[tok_id + 1].value
                            assert attribute in {"np"}
                            to_replace_toks[(line_j, tok_id - 1)] = (tok_id + 2, attribute + "["+condition_tokens[tok_id - 1].value+"]")
                            tok_id += 2
                            continue

                        tok_id += 1
            next_line_ind_match = re.search(r"^(\s*).+$", cmd_lines[line_id + 1])
            if (next_line_ind := len(next_line_ind_match.group(1))) == this_cmd_line_indent:
                indent = FIXED_BASE_INDENT + 4  # entering the domain of this stage / stageTurn
            elif next_line_ind < this_cmd_line_indent:
                raise RuntimeError(f'After "{cmd_line.strip()}", expected the same or more indent in the next line, but found less.\n')

        elif cond_match := re.search(r"^(\s*)([elifs]{2,4})\s*(.*):\s*(.*)$", cmd_line):
            condition_tokens = list(tokenize(cond_match.group(3)))
            # print the conditional expression
            class_str += ' ' * indent + cond_match.group(2)
            tok_id = 0
            while tok_id < len(condition_tokens):
                if (line_id, tok_id) in to_replace_toks:
                    end, replaced_expr = to_replace_toks[(line_id, tok_id)]
                    class_str += " " + replaced_expr
                    tok_id = end
                else:
                    class_str += " " + condition_tokens[tok_id].value
                    tok_id += 1
            class_str += ":\n"

            # parse action_str
            if len(cond_match.group(4)) > 0:
                indent += 4
                indent, class_str = parseActionString(indent, cond_match.group(4), class_str)
                indent -= 4

        elif hougu_match := re.search(r"^(\s*)hougu:(.+)$", cmd_line):
            hougu_servants = []
            hougu_tokens = list(tokenize(hougu_match.group(2)))
            for token in hougu_tokens:
                if token.type == "INT":
                    hougu_servants.append(int(token.value))
            this_info = this_info._replace(hougu_servants=hougu_servants)
            class_str += ' ' * indent + "fgoDevice.device.perform(' ',(2100,))\n" + \
                         ' ' * indent + "fgoDevice.device.perform(self.selectCard"+"_"+this_s_st_str+"(),(300,300,2300,1300,6000))\n"
        elif pre_eval_match := re.search(r"^\s*pre:(.+)$", cmd_line):
            this_info = this_info._replace(pre_eval_str=pre_eval_match.group(1).strip())
        elif post_eval_match := re.search(r"^\s*post:(.+)$", cmd_line):
            this_info = this_info._replace(post_eval_str=post_eval_match.group(1).strip())
        elif target_match := re.search(r"^\s*target:(\d+)$", cmd_line):
            this_info = this_info._replace(target=int(target_match.group(1)))
        else:
            if "selectCard" in cmd_line:    # we may need this info to guide selectCard generation apart from selectCard calling
                this_info = this_info._replace(preprogrammed_selectCard=cmd_line.strip())
            indent, class_str = parseActionString(indent, cmd_line.strip(), class_str)
        last_cmd_line_indent = this_cmd_line_indent

    select_card_info_map[this_s_st_str] = this_info     # when the input ends, save the previous stage/turn
    class_str += '        else:\n' \
                 '            self.dispatchSkill()\n' \
                 '            fgoDevice.device.perform(" ",(2100,))\n' \
                 '            fgoDevice.device.perform(self.selectCard(),(300,300,2300,1300,6000))\n'

    # generate selectCard_*() methods
    for s_st_str, this_info in select_card_info_map.items():
        class_str = generateCustiomizedSelectCard(s_st_str, this_info, class_str)
    return class_str


if __name__ == '__main__':
    out_str = generateCustomizedTurn("SampleTurnSeq.txt")
    with open("SampleOutput.py", "w", encoding="utf-8") as f:
        f.write(out_str)
