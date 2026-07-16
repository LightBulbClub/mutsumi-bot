"""
参数解析模块 - 定义命令参数的模式和匹配结果。

该模块提供了用于定义和解析命令参数模式的各种类，包括
参数模式、可选模式、模板等，是命令解析系统的基础。
"""

import itertools
import re
from dataclasses import dataclass, field

from core.constants.exceptions import InvalidTemplatePattern, InvalidCommandFormatError

# 最大嵌套深度限制 - 防止无限递归
MAX_NEST_DEPTH = 10

# 模板字符串的分隔正则：分离可选参数块、参数块、描述块和空格
# 捕获组：(\[.*?]) 可选参数 [...]
#        (<.*?>)  必需参数 <...>
#        (\{.*})  描述信息 {...}
#        空格     普通分隔符
_TEMPLATE_TOKEN_RE = re.compile(r"(\[.*?])|(<.*?>)|(\{.*})| ")

# 非法的括号混嵌组合
_ILLEGAL_BRACKET_NESTINGS = ("<[", ">{", "{<", "[{", "{[")


class ArgumentPattern:
    """
    参数模式类 - 表示命令中的一个参数占位符。

    用于在命令模板中定义一个需要解析的参数位置。

    :param name: 参数的名称，用于标识和匹配结果中引用
    """

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return f'ArgumentPattern("{self.name}")'

    def __repr__(self):
        return self.__str__()


class DescPattern:
    """
    描述模式类 - 用于在命令模板中添加文本描述。

    不进行参数匹配，仅用于帮助文档和提示。

    :param text: 描述文本
    """

    def __init__(self, text: str):
        self.text = text

    def __str__(self):
        return f'DescPattern("{self.text}")'

    def __repr__(self):
        return self.__str__()


class Template:
    """
    命令模板类 - 定义一个命令的完整参数结构。

    模板由一系列参数模式组成，用于匹配和解析用户输入。

    :param args: 参数模式列表，可包含 ArgumentPattern、OptionalPattern、DescPattern
    :param priority: 优先级（用于多个模板匹配时的选择，数值越大优先级越高）
    """

    def __init__(
        self,
        args: "list[ArgumentPattern | OptionalPattern | DescPattern]",
        priority: int = 1,
    ):
        # 参数列表
        self.args_ = args
        # 模板优先级
        self.priority = priority

    @property
    def args(self):
        """获取参数列表"""
        return self.args_

    def __str__(self):
        return f"Template({self.args})"

    def __repr__(self):
        return self.__str__()


class OptionalPattern:
    """
    可选模式类 - 表示可选的命令参数或选项。

    :param flag: 可选标志，如 "option" 或 "o"
    :param args: 该选项下的模板列表（支持多个可选变体）
    """

    def __init__(self, flag: str, args: list[Template]):
        # 选项标志
        self.flag = flag
        # 该选项的模板列表
        self.args = args

    def __str__(self):
        return f'OptionalPattern("{self.flag}", {self.args})'

    def __repr__(self):
        return self.__str__()


class Argument:
    """
    参数类 - 表示解析后的单个参数值。

    :param value: 参数值
    """

    def __init__(self, value: str):
        self.value = value


class Optional:
    """
    可选项类 - 表示解析后的可选参数。

    :param args: 可选项的参数字典
    :param flagged: 是否已被设置（有值）
    """

    def __init__(self, args: dict[str, dict], flagged=False):
        # 标志此选项是否被使用
        self.flagged = flagged
        # 选项的参数
        self.args = args


class MatchedResult:
    """
    匹配结果类 - 表示命令匹配后的结果。

    包含解析出的所有参数和匹配的原始模板信息。

    :param args: 解析出的参数字典
    :param original_template: 匹配的原始模板对象
    :param priority: 匹配的优先级
    """

    def __init__(self, args: dict, original_template, priority: int = 1):
        # 解析出的参数字典
        self.args = args
        # 原始模板引用
        self.original_template = original_template
        # 优先级（用于多模板匹配时排序）
        self.priority = priority

    def __str__(self):
        return f"MatchedResult({self.args}, {self.priority})"

    def __repr__(self):
        return self.__str__()


def split_multi_arguments(lst: list[str]) -> list[str]:
    """
    分割包含多个选项的参数字符串。

    该函数处理形如 "hello(world|everyone)" 的字符串，将其展开为多个变体：
    ["hello world", "hello everyone"]

    支持嵌套的括号和多个选择组。

    示例:
    ```
        >>> split_multi_arguments(["hello(world|earth)"])
        ["hello world", "hello earth"]
        >>> split_multi_arguments(["a(b|c)d(e|f)"])
        ["abde", "abdf", "acde", "acdf"]
    ```

    :param lst: 包含参数字符串的列表，字符串中可能包含 (option1|option2) 形式的选择组
    :return: 展开后的参数列表，每个变体为一个独立的字符串
    """
    patn = re.compile(r"\((.*?)\)")
    new_lst = []

    for item in lst:
        # 将 "hello(world|earth)foo(a|b)" 拆分为文本块和选项列表
        # 例如: ["hello", "world|earth", "foo", "a|b", ""]
        parts = patn.split(item)

        # 将选项块按 "|" 分割转换为列表，纯文本直接作为单元素列表
        choices = []
        for i, part in enumerate(parts):
            if i % 2 != 0:
                choices.append(part.split("|"))
            else:
                choices.append([part])

        # 使用笛卡尔积生成所有组合
        for combination in itertools.product(*choices):
            new_lst.append("".join(combination))

    return list(set(new_lst))


def _normalize_template_input(argv: list[str]) -> list[str]:
    """预处理模板输入：去重空字符串并展开多选项参数。"""
    normalized = []
    for raw in argv:
        if not isinstance(raw, str):
            continue
        stripped = raw.strip()
        if not stripped:
            continue
        for expanded in split_multi_arguments([stripped]):
            normalized.append(expanded)
    return normalized


def _check_mixed_bracket_nesting(template_str: str) -> None:
    """检查模板字符串中是否存在非法的括号混嵌。"""
    if any(nesting in template_str for nesting in _ILLEGAL_BRACKET_NESTINGS):
        raise InvalidTemplatePattern(f"Illegal mixed bracket nesting: {template_str}")


def _split_template_tokens(template_str: str) -> list[str]:
    """将模板字符串拆分为参数块、可选参数块、描述块等 token。"""
    return [token for token in _TEMPLATE_TOKEN_RE.split(template_str) if token]


class _TemplateBuildState:
    """parse_template 内部使用的构建状态。"""

    def __init__(self):
        self.arg_names: set[str] = set()
        self.last_type: str | None = None
        self.seen_desc = False
        self.seen_variadic = False


def _ensure_argument_block_valid(token: str, raw_token: str) -> None:
    """校验 <...> 参数块的完整性。"""
    if not token.endswith(">"):
        raise InvalidTemplatePattern(f"Broken argument block: {raw_token}")
    if not token[1:-1].strip():
        raise InvalidTemplatePattern("Empty argument block <> not allowed")


def _build_optional_pattern(inner: str, depth: int) -> OptionalPattern:
    """根据可选参数块内部内容构建 OptionalPattern。"""
    parts = inner.split(" ")
    flag = None
    args = []

    if parts[0].startswith("<"):
        _ensure_argument_block_valid(parts[0], inner)
        args = parts
    else:
        flag = parts[0]
        args = parts[1:]

    if flag and flag.startswith("{"):
        raise InvalidTemplatePattern(f"Optional flag cannot be description: {flag}")

    # 检查可选参数块内部是否重复
    seen = set()
    for arg in args:
        if arg in seen:
            raise InvalidTemplatePattern(f'Duplicate argument in optional flag "{flag}": {arg}')
        seen.add(arg)

    parsed_args = parse_template([" ".join(args)], depth + 1) if args else []
    return OptionalPattern(flag=flag, args=parsed_args)


def _parse_optional_block(token: str, state: _TemplateBuildState, depth: int) -> OptionalPattern:
    """解析 [...] 可选参数块。"""
    if not token.endswith("]"):
        raise InvalidTemplatePattern(f"Broken optional block: {token}")

    inner = token[1:-1].strip()
    if not inner:
        raise InvalidTemplatePattern("Empty optional block [] not allowed")

    if state.last_type == "desc":
        raise InvalidTemplatePattern(f"Optional argument cannot follow description: {token}")

    optional = _build_optional_pattern(inner, depth)
    if not optional.flag and state.last_type == "optional_no_flag":
        raise InvalidTemplatePattern(f"Two no-flag optional arguments not allowed: {token}")

    # 无标志可选参数需要与已有必需参数去重
    if not optional.flag:
        for inner_template in optional.args:
            for inner_arg in inner_template.args:
                if isinstance(inner_arg, ArgumentPattern):
                    if inner_arg.name in state.arg_names:
                        raise InvalidTemplatePattern(f"Duplicate required argument: {inner_arg.name}")
                    state.arg_names.add(inner_arg.name)

    state.last_type = "optional" if optional.flag else "optional_no_flag"
    return optional


def _parse_desc_block(token: str, state: _TemplateBuildState) -> DescPattern:
    """解析 {...} 描述块。"""
    if not token.endswith("}"):
        raise InvalidTemplatePattern(f"Broken description block: {token}")
    if state.seen_desc:
        raise InvalidTemplatePattern(f"Multiple descriptions not allowed: {token}")

    state.seen_desc = True
    desc = token[1:-1].strip()
    if not desc:
        raise InvalidTemplatePattern("Empty description block {} not allowed")

    state.last_type = "desc"
    return DescPattern(desc)


def _parse_argument_or_flag(token: str, state: _TemplateBuildState) -> ArgumentPattern:
    """解析 <...> 值参数、... 可变长参数或布尔标志。"""
    if token.startswith("<"):
        _ensure_argument_block_valid(token, token)

    if state.last_type in ("optional", "optional_no_flag"):
        raise InvalidTemplatePattern(f"Argument cannot follow optional block: {token}")
    if state.last_type == "desc":
        raise InvalidTemplatePattern(f"Argument cannot follow description: {token}")
    if token in state.arg_names:
        raise InvalidTemplatePattern(f'Duplicate argument: "{token}"')

    if token == "...":
        if state.seen_variadic:
            raise InvalidTemplatePattern('Duplicate "..." not allowed')
        state.seen_variadic = True
        state.last_type = "variadic"
        return ArgumentPattern("...")

    state.arg_names.add(token)
    state.last_type = "argument"
    return ArgumentPattern(token)


def parse_template(argv: list[str], depth: int = 0) -> list[Template]:
    """
    解析命令模板字符串为 Template 对象列表。

    该函数是命令解析系统的核心，将用户定义的模板字符串转换为可用于匹配的
    Template 对象。支持递归处理嵌套的可选参数。

    模板语法:
        - <arg>: 必需参数，用 < > 包括
        - [option]: 可选参数，用 [ ] 包括
        - [flag <arg>]: 带标志的可选参数
        - {description}: 描述信息，用于生成帮助文本

    示例:
    ```
        > parse_template(["<source> [-o <destination>] {Copy a file}"])
        [Template([ArgumentPattern('source'),
        OptionalPattern('-o', [Template([ArgumentPattern('destination')])]),
         DescPattern('Copy a file')])]
    ```

    :param argv: 包含模板字符串的列表
    :param depth: 递归深度，用于防止无限递归（最大深度由 MAX_NEST_DEPTH 定义）
    :return: 解析后的 Template 对象列表
    :raises InvalidTemplatePattern: 如果模板格式不合法
    """
    if depth > MAX_NEST_DEPTH:
        raise InvalidTemplatePattern("Template nesting too deep")

    templates = []
    for template_str in _normalize_template_input(argv):
        _check_mixed_bracket_nesting(template_str)

        template = Template([])
        state = _TemplateBuildState()

        for token in _split_template_tokens(template_str):
            token = token.strip()
            if not token:
                continue

            if token.startswith("["):
                template.args.append(_parse_optional_block(token, state, depth))
            elif token.startswith("{"):
                template.args.append(_parse_desc_block(token, state))
            else:
                template.args.append(_parse_argument_or_flag(token, state))

        templates.append(template)

    return templates


def _collect_template_parts(template: Template) -> tuple[list[str], str | None]:
    """收集单个模板的参数文本片段和描述文本。"""
    arg_parts = []
    desc = None
    for arg in template.args:
        if isinstance(arg, DescPattern):
            desc = arg.text
        elif isinstance(arg, OptionalPattern):
            arg_parts.append(_format_optional_pattern(arg))
        elif isinstance(arg, ArgumentPattern):
            arg_parts.append(arg.name)
    return arg_parts, desc


def _iter_simplified_templates(templates: list[Template], simplify: bool):
    """迭代模板，应用重复描述简化规则，产出 (参数片段列表, 描述) 元组。

    简化模式下，描述与上一个模板相同的整个模板会被跳过。
    """
    last_desc = None
    for template in templates:
        arg_parts, desc = _collect_template_parts(template)
        # 简化模式下，重复描述的整个模板被跳过
        if desc is not None and simplify and desc == last_desc:
            continue
        if desc is not None:
            last_desc = desc
        yield arg_parts, desc


def templates_to_str(templates: list[Template], with_desc=False, simplify=True) -> list[str]:
    """
    将 Template 对象列表转换回字符串表示。

    该函数用于生成帮助文本，将解析后的 Template 对象转换为人类可读的字符串格式。

    示例:
    ```
        > template = Template([ArgumentPattern('<source>'), OptionalPattern('-o', [Template([ArgumentPattern('<destination>')])]), DescPattern('Copy a file')])
        > templates_to_str([template])
        ['<source> [-o <destination>] - Copy a file']
    ```

    :param templates: Template 对象列表
    :param with_desc: 是否包含描述信息（用于生成详细帮助）
    :param simplify: 是否简化输出（去除重复的描述）
    :return: 字符串列表，每个字符串代表一个模板的可读形式
    """
    text = []

    for arg_parts, desc in _iter_simplified_templates(templates, simplify):
        if arg_parts:
            arg_str = " ".join(arg_parts)
            if with_desc and desc:
                text.append(f"{arg_str} - {desc}")
            else:
                text.append(arg_str)
        elif with_desc and desc:
            text.append(f"- {desc}")

    return text


def templates_to_structs(templates: list[Template], with_desc=False, simplify=True) -> list[tuple[str, str | None]]:
    """
    将 Template 对象列表转换为结构化的 (参数字符串, 描述) 元组列表。

    :param templates: Template 对象列表
    :param with_desc: 是否包含描述信息
    :param simplify: 是否简化输出（去除重复的描述）
    :return: (参数字符串, 描述) 元组列表，描述可能为 None
    """
    result = []

    for arg_parts, desc in _iter_simplified_templates(templates, simplify):
        arg_str = " ".join(arg_parts)
        if with_desc:
            result.append((arg_str, desc))
        else:
            result.append((arg_str, None))

    return result


def _format_optional_pattern(arg: OptionalPattern) -> str:
    """将 OptionalPattern 格式化为 [flag args] 字符串。"""
    parts = ["["]
    if arg.flag:
        parts.append(arg.flag)
    if arg.args:
        if arg.flag:
            parts.append(" ")
        parts.append(" ".join(templates_to_str(arg.args, simplify=False)))
    parts.append("]")
    return "".join(parts)


@dataclass
class _MatchState:
    """parse_argv 单次模板匹配过程中的可变状态。"""

    argv_copy: list[str]
    parsed_argv: dict = field(default_factory=dict)
    deferred_processors: list[Template] = field(default_factory=list)


def _match_optional_patterns(args: list, state: _MatchState, depth: int) -> None:
    """处理带标志和无标志的可选参数。"""
    for arg in args:
        if not isinstance(arg, OptionalPattern):
            continue

        if not arg.flag:
            # 无标志可选参数（如 [<file>]）延后到必需参数之后处理
            state.deferred_processors.append(arg.args[0])
            continue

        state.parsed_argv[arg.flag] = Optional({}, flagged=False)
        if arg.flag not in state.argv_copy:
            continue

        if not arg.args:
            state.parsed_argv[arg.flag] = Optional({}, flagged=True)
            state.argv_copy.remove(arg.flag)
            continue

        flag_index = state.argv_copy.index(arg.flag)
        required_sub_args = len(arg.args[0].args)
        if len(state.argv_copy[flag_index:]) < required_sub_args:
            continue

        sub_argv = state.argv_copy[flag_index + 1 : flag_index + required_sub_args + 1]
        state.parsed_argv[arg.flag] = Optional(parse_argv(sub_argv, arg.args).args, flagged=True)
        del state.argv_copy[flag_index : flag_index + required_sub_args + 1]


def _match_required_arguments(args: list, state: _MatchState) -> None:
    """处理必需参数、布尔标志和可变长参数标记。"""
    for arg in args:
        if not isinstance(arg, ArgumentPattern):
            continue

        if arg.name.startswith("<"):
            if state.argv_copy:
                state.parsed_argv[arg.name] = Argument(state.argv_copy[0])
                del state.argv_copy[0]
            else:
                state.parsed_argv[arg.name] = False
        elif arg.name == "...":
            state.deferred_processors.append(Template([arg]))
        else:
            state.parsed_argv[arg.name] = arg.name in state.argv_copy
            if state.parsed_argv[arg.name]:
                state.argv_copy.remove(arg.name)


def _match_deferred_processors(state: _MatchState) -> None:
    """处理无标志可选参数和可变长参数等延后处理器。"""
    if not state.argv_copy or not state.deferred_processors:
        return

    for processor_index, processor in enumerate(state.deferred_processors, start=1):
        for arg_index, sub_arg in enumerate(processor.args, start=1):
            if not isinstance(sub_arg, ArgumentPattern):
                continue

            if sub_arg.name.startswith("<"):
                if not state.argv_copy:
                    state.parsed_argv[sub_arg.name] = False
                    continue

                is_last = processor_index == len(state.deferred_processors) and arg_index == len(processor.args)
                if is_last:
                    state.parsed_argv[sub_arg.name] = Argument(" ".join(state.argv_copy))
                    state.argv_copy.clear()
                else:
                    state.parsed_argv[sub_arg.name] = Argument(state.argv_copy[0])
                    del state.argv_copy[0]

            elif sub_arg.name == "...":
                state.parsed_argv[sub_arg.name] = [Argument(x) for x in state.argv_copy]
                del state.argv_copy[:]

            else:
                state.parsed_argv[sub_arg.name] = sub_arg.name in state.argv_copy
                if state.parsed_argv[sub_arg.name]:
                    state.argv_copy.remove(sub_arg.name)


def _append_remaining_to_last_value_arg(args: list, state: _MatchState) -> None:
    """将剩余参数追加到最后一个值参数（兼容旧行为）。"""
    if not state.argv_copy:
        return

    template_arguments = [arg for arg in args if isinstance(arg, ArgumentPattern)]
    if not template_arguments:
        return

    last_argument = template_arguments[-1]
    if last_argument.name.startswith("<"):
        argv_keys = list(state.parsed_argv.keys())
        state.parsed_argv[argv_keys[argv_keys.index(last_argument.name)]].value += " " + " ".join(state.argv_copy)
        del state.argv_copy[0]


def _try_match_template(argv: list[str], template: Template, depth: int = 0) -> MatchedResult | None:
    """使用单个模板尝试匹配参数列表。"""
    args = [arg for arg in template.args if not isinstance(arg, DescPattern)]
    if not args:
        return None

    state = _MatchState(argv.copy())

    _match_optional_patterns(args, state, depth)
    _match_required_arguments(args, state)
    _match_deferred_processors(state)
    _append_remaining_to_last_value_arg(args, state)

    return MatchedResult(state.parsed_argv, template, template.priority)


def _convert_and_filter_match(result: MatchedResult) -> bool:
    """转换匹配结果并返回是否有效（所有必需参数都被满足）。"""
    for key, value in result.args.items():
        # 注意：使用 if/elif 链，确保 Optional 被转换为 False 后不会在同一次迭代中被过滤。
        if isinstance(value, Optional):
            if not value.flagged:
                result.args[key] = False
            else:
                result.args[key] = True if not value.args else value.args
        elif isinstance(value, Argument):
            result.args[key] = value.value
        elif isinstance(value, list):
            result.args[key] = [v.value for v in value if isinstance(v, Argument)]
        elif isinstance(value, bool) and not value:
            return False
    return True


def _primary_match_score(result: MatchedResult) -> int:
    """第一轮优先级：基础优先级 + 值为 True 的参数个数。"""
    return result.priority + sum(1 for value in result.args.values() if value is True)


def _secondary_match_score(result: MatchedResult) -> int:
    """第二轮优先级：基础优先级 + 非空/真值参数个数。"""
    return result.priority + sum(1 for value in result.args.values() if value)


def _select_best_match(results: list[MatchedResult]) -> MatchedResult:
    """根据两轮优先级计算选择最佳匹配。"""
    results = sorted(results, key=_primary_match_score, reverse=True)
    top_score = _primary_match_score(results[0])
    top_results = [r for r in results if _primary_match_score(r) == top_score]

    if len(top_results) == 1:
        return top_results[0]

    top_results = sorted(top_results, key=_secondary_match_score, reverse=True)
    return top_results[0]


def parse_argv(argv: list[str], templates: list["Template"]) -> MatchedResult:
    """
    根据给定的模板列表解析命令行参数。

    该函数是参数解析的核心逻辑，尝试用各个模板匹配输入的参数列表。
    采用贪心匹配算法，逐个尝试每个模板直到找到匹配，然后根据优先级选择最佳结果。

    匹配流程：
    1. 逐个尝试所有模板
    2. 对每个模板，按顺序处理可选参数、必需参数和可变长参数
    3. 构建解析结果字典，存储解析后的参数值
    4. 过滤出有效的匹配结果（所有必需参数都被满足）
    5. 对多个有效匹配按优先级进行排序
    6. 返回优先级最高的匹配结果或抛出异常

    优先级计算规则：
    - 基础优先级：来自 Template 的 priority 值
    - 额外优先级：每个被成功匹配的参数加 1 分
    - 多个相同优先级时：再次按有值参数的个数排序

    参数类型说明：
    - `<param>`: 值参数，必须消耗一个参数值，如 <file>、<name>
    - flag: 标志参数，是否存在于参数列表中（True/False），如 -v
    - ...: 可变长参数，可消耗 0 个或多个参数
    - `[flag <param>]`: 可选参数，可能带有标志和子参数

    示例：
    - 模板: Template([ArgumentPattern('<lang>'), OptionalPattern('-v', [...])])
    - 输入: argv = ["python", "-v"]
    - 输出: MatchedResult({"<lang>": "python", "-v": True}, template, priority)

    :param argv: 命令行参数列表（不包括命令名本身）
    :param templates: 可用的模板列表，会逐个尝试匹配
    :return: MatchedResult 对象，包含：
             - args: 解析后的参数字典
             - original_template: 匹配的原始模板对象
             - priority: 最终优先级分数
    :raises InvalidCommandFormatError: 如果无法用任何模板匹配参数
    """
    matched_results = []

    for template in templates:
        try:
            result = _try_match_template(argv, template)
            if result is not None:
                matched_results.append(result)
        except TypeError:
            # 类型错误说明该模板不适用，继续尝试下一个
            continue

    valid_results = [r for r in matched_results if _convert_and_filter_match(r)]

    if not valid_results:
        raise InvalidCommandFormatError

    if len(valid_results) == 1:
        return valid_results[0]

    return _select_best_match(valid_results)
