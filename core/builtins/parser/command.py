"""
命令解析模块 - 解析和处理用户命令。

该模块提供了 CommandParser 类，用于解析用户输入的命令，
匹配命令模板，生成帮助文档等功能。
"""

import re
import shlex
from typing import TYPE_CHECKING

from core.config import Config
from core.constants.exceptions import InvalidCommandFormatError
from core.exports import exports
from core.i18n import Locale
from core.logger import Logger
from core.types import Module
from .args import parse_argv, Template, templates_to_str, templates_to_structs, ArgumentPattern, DescPattern

if TYPE_CHECKING:
    from core.builtins.bot import Bot

# 默认地区设置
default_locale = Config("default_locale", cfg_type=str)

# 预编译正则：匹配中文引号（避免每次 parse 重新编译）
_CN_QUOTE_PATTERN = re.compile(r"[“”]")


def _get_available_commands(
    module: Module,
    msg: "Bot.MessageSession | None",
    is_superuser: bool | None,
) -> list:
    """根据当前会话权限返回可用的命令列表。"""
    if not msg:
        return list(module.command_list.set)

    if is_superuser is None:
        is_superuser = msg.check_super_user()
    is_base_superuser = msg.session_info.sender_id in exports["Bot"].base_superuser_list
    return list(
        module.command_list.get(
            msg.session_info.target_from,
            show_required_superuser=is_superuser,
            show_required_base_superuser=is_base_superuser,
        )
    )


def _build_command_templates(
    available_commands: list,
    command_templates: dict,
    options_desc: dict,
) -> None:
    """根据可用命令构建命令模板字典和选项描述字典。"""
    for command in available_commands:
        if command.command_template:
            for template in command.command_template:
                command_templates[template] = {"priority": command.priority, "meta": command}
                has_required_argument = any(isinstance(arg, ArgumentPattern) for arg in template.args)
                if not has_required_argument and "" not in command_templates:
                    command_templates[""] = {"priority": command.priority, "meta": command}
        else:
            command_templates[""] = {"priority": command.priority, "meta": command}

        if command.options_desc:
            for option, desc in command.options_desc.items():
                options_desc[option] = desc


def _dedup_options_desc(options_desc: dict) -> dict:
    """如果多个选项有相同的描述，只保留一个。"""
    seen_values = set()
    deduped = {}
    for key, value in options_desc.items():
        if value not in seen_values:
            deduped[key] = value
            seen_values.add(value)
    return deduped


def _normalize_and_split(command: str) -> list[str]:
    """规范化命令字符串并分割为单词列表。"""
    command = _CN_QUOTE_PATTERN.sub('"', command)
    try:
        return shlex.split(command)
    except ValueError:
        return command.split(" ")


def _resolve_locale(locale, default_lang) -> Locale:
    """解析地区参数为 Locale 对象。"""
    return Locale(locale) if locale else default_lang


class CommandParser:
    """
    命令解析器 - 用于解析和验证用户输入的命令。

    该类根据模块定义的命令模板，对用户输入进行解析和验证，
    支持多种命令格式和权限检查。

    属性说明:
        command_prefixes: 命令前缀列表
        module_name: 模块名称
        origin_template: 原始命令模板
        msg: 消息会话对象（可选）
        args: 命令模板字典
        options_desc: 选项描述字典
    """

    def __init__(
        self,
        args: Module,
        command_prefixes: list,
        module_name=None,
        msg: "Bot.MessageSession | None" = None,
        is_superuser: bool | None = None,
    ):
        """
        初始化命令解析器。

        :param args: 模块对象，包含命令定义
        :param command_prefixes: 命令前缀列表
        :param module_name: 模块名称
        :param msg: 消息会话对象（用于权限检查）
        :param is_superuser: 是否为超级用户（如为 None 则从会话自动检测）
        """
        self.command_prefixes = command_prefixes
        self.module_name = module_name
        self.origin_template = args
        self.msg: "Bot.MessageSession | None" = msg
        self.options_desc = {}
        self.lang = self.msg.session_info.locale if self.msg else Locale(default_locale)

        available_commands = _get_available_commands(args, msg, is_superuser)
        command_templates: dict[Template | str, dict] = {}
        _build_command_templates(available_commands, command_templates, self.options_desc)

        self.args: dict[Template | str, dict] = command_templates
        self.options_desc = _dedup_options_desc(self.options_desc)
        self._filtered_args = [a for a in self.args if a != ""]

    def return_formatted_help_doc(self, locale=None) -> str:
        """
        生成格式化的帮助文档字符串。
        """
        if not self.args:
            return ""

        locale = _resolve_locale(locale, self.lang)
        format_args = templates_to_str(self._filtered_args, with_desc=True)

        lines = []
        for arg_line in format_args:
            translated = locale.t_str(arg_line, locale_failed_prompt=False)
            lines.append(f"{self.command_prefixes[0]}{self.module_name} {translated}")
        result = "\n".join(lines)

        if self.options_desc:
            options_lines = [
                f"{option} - {locale.t_str(desc, locale_failed_prompt=False)}"
                for option, desc in self.options_desc.items()
            ]
            result += f"\n{locale.t('core.help.options')}\n" + "\n".join(options_lines)

        return result

    def return_json_help_doc(self, locale=None) -> dict:
        """
        生成 JSON 格式的帮助文档。

        该方法将命令模板和选项描述转换为结构化的 JSON 格式，
        便于前端或 API 客户端使用。

        返回格式示例：
        ```json
        {
            "args": [
                {"args": "~aaa <keyword>", "desc": "简介1"},
                {"args": "~aaa bbb <keyword> [mode]", "desc": "简介2"}
            ],
            "options": [
                {"-o": "简介3"}
            ]
        }
        ```

        :param locale: 地区/语言代码。如为 None，使用会话默认地区
        :return: 包含 args 和 options 的字典
        """
        if not self.args:
            return {}

        locale = _resolve_locale(locale, self.lang)
        args_list = []
        prefix_module = f"{self.command_prefixes[0]}{self.module_name}"

        for arg_str, desc in templates_to_structs(self._filtered_args, with_desc=True):
            translated_desc = locale.t_str(desc, locale_failed_prompt=False) if desc else ""
            args_list.append({"args": f"{prefix_module} {arg_str}", "desc": translated_desc})

        options_desc_fmtted = [
            {option: locale.t_str(desc, locale_failed_prompt=False)} for option, desc in self.options_desc.items()
        ]

        return {"args": args_list, "options": options_desc_fmtted}

    def parse(self, command):
        """
        解析用户输入的命令字符串。

        该方法负责格式化、分割、匹配命令字符串并返回匹配的命令元数据和参数。

        :param command: 用户输入的完整命令字符串（不包括前缀）
        :return: (CommandMeta, 参数字典) 元组
        :raises InvalidCommandFormatError: 如果命令格式不正确或无法匹配任何模板
        """
        if not self.args:
            return None

        split_command = _normalize_and_split(command)
        Logger.trace("splited command: " + str(split_command))

        if len(split_command) == 1:
            return self._handle_no_arg_command()

        base_match = parse_argv(split_command[1:], self._filtered_args)
        return self.args[base_match.original_template]["meta"], base_match.args

    def _handle_no_arg_command(self):
        """处理只有命令名、没有参数的情况。"""
        if not self.origin_template.command_list.set:
            return None, None

        if "" in self.args:
            return self.args[""]["meta"], None

        for arg in self.args:
            if len(arg.args) == 1 and isinstance(arg.args[0], DescPattern):
                return self.args[arg]["meta"], None

        raise InvalidCommandFormatError
