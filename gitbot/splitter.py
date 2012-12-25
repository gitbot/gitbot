import json
from itertools import chain
from pyparsing import (
                        Combine, Forward, Group, LineEnd, Literal, OneOrMore,
                        Optional, SkipTo, Suppress, White, Word, ZeroOrMore,
                        alphanums, dblQuotedString, delimitedList,
                        originalTextFor)


def _translate_token(t):

    if not hasattr(t, 'getName'):
        return t

    name = t.getName()

    res = t

    combined = ''.join(chain.from_iterable(t))

    if name == 'ScriptEnd':
        combined += '\n'

    if name == 'Script' or name == 'ScriptEnd':
        res = json.dumps(combined)
        res += ', '

        if name == 'ScriptEnd':
            res = res.rstrip(' ')

    elif name == 'AWS':
        res = json.dumps(json.loads(combined))
        res += ', '
    elif name == 'AWSEnd':
        res = combined + json.dumps('\n') + ','
    return res

def translate(s, l, t):
    return _translate_token(t)

def process_line(s, l, t):
    return ''.join(chain.from_iterable(t)) + '\n'

def grammar():
    REF = Combine(Literal('"Ref"'))
    FN = Combine(Literal('"Fn::') + Word(alphanums) + Literal('"'))

    json_val = Forward()
    json_string = dblQuotedString
    json_list_items = delimitedList(json_val)
    json_list = Literal('[') + Optional(json_list_items) + Literal(']')
    json_dict_member = json_string + Literal(':') + json_val
    json_dict_members = delimitedList(json_dict_member)
    json_dict = Literal('{') + Optional(json_dict_members) + Literal('}')

    json_val << (json_string | json_list | json_dict)

    aws_member = (REF | FN) + Literal(':') + originalTextFor(json_val)
    aws = Group(Literal('{') +
                    aws_member +
                    Literal('}')).setParseAction(translate)
    aws_start = Literal('{').leaveWhitespace() + (REF | FN)
    term = aws_start | LineEnd()

    script_stuff = Group(
                            ZeroOrMore(White()) +
                            SkipTo(term)
                        ).setParseAction(translate)
    script_line = script_stuff('ScriptEnd') + ~aws_start + Suppress(LineEnd())
    script_line_ending_with_aws = (
                                    Optional(script_stuff('Script')) +
                                    aws('AWS') +
                                    Suppress(LineEnd())
                                ).setParseAction(translate)
    script_line_containing_aws = (
                                    Optional(script_stuff('Script')) +
                                    aws('AWS') +
                                    script_line)
    line = Group(
                    script_line_ending_with_aws('AWSEnd') |
                    script_line_containing_aws |
                    script_line
                ).setParseAction(process_line)

    return OneOrMore(line('Line'))


def split(txt):
    script = grammar()
    toks = script.parseString(txt)
    result = '{"Fn::Join": ["", [\n'
    content = ''.join(toks)
    content = ''.join(['    ' + line for line in content.splitlines(True)])
    content = content.rstrip(', \n')
    result += content
    result += '\n]]}\n'
    return result


__all__ = ['split']
