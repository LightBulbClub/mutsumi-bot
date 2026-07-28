from core.component import module
from core.config import Config

zzz = module(
    "zzz",
    alias="zenless",
    developers=["SoftGreyMon", "haoye_qwq"],
    support_languages=["zh_cn", "en_us"],
    desc="{I18N:zzzerouid.help.desc}",
    doc=True,
)


@zzz.config()
class ZzzConfig:
    sched_energy_push: bool = True
    widget_resin: bool = True
    crazy_notice: bool = False
    refresh_bg: str = "bg2"
    zzz_guide_provide: str = "猫冬"
    refresh_card_use_pic: bool = True
    enable_custom_char_bg: bool = False
    refresh_data_list: list[str] = ["ENKA", "MINIGG", "MYS"]


DEFAULT_CDN = "https://file.minigg.cn/sayu-bot/ZZZeroUID"
RESOURCE_CDN = Config("resource_cdn", DEFAULT_CDN, table_name="module_zzzerouid")
